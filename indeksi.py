"""Pravljenje FAISS indeksa i pretraga (vektorska pretraga, reranking i prepravka upita)."""
import json
import time

import faiss
import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

from config import FOLDER_INDEKSI, FOLDER_PODACI, PRISTUPI, TOP_K
from fragmentacija import napravi_fragmente, ucitaj_dokumente
from llm import prepravi_upit

# modeli su veliki, pa se svaki učitava samo jednom i deli između pristupa
_ucitani_modeli = {}


def embeding_model(naziv):
    if naziv not in _ucitani_modeli:
        _ucitani_modeli[naziv] = SentenceTransformer(naziv)
    return _ucitani_modeli[naziv]


def reranker_model(naziv):
    if naziv not in _ucitani_modeli:
        _ucitani_modeli[naziv] = CrossEncoder(naziv, max_length=512)
    return _ucitani_modeli[naziv]


def u_vektore(model, tekstovi, podesavanja):
    # za HNSW sa skalarnim proizvodom vektori moraju biti normalizovani, tada je to kosinusna sličnost
    return model.encode(
        tekstovi,
        batch_size=32,
        normalize_embeddings=podesavanja["indeks"] == "hnsw",
        convert_to_numpy=True,
    ).astype(np.float32)


def napravi_faiss_indeks(vektori, podesavanja):
    dimenzija = vektori.shape[1]
    if podesavanja["indeks"] == "flat_l2":
        # poredi upit sa svakim vektorom, tačno ali sporije na velikim bazama
        indeks = faiss.IndexFlatL2(dimenzija)
    else:
        # graf u više slojeva, približna ali brza pretraga
        indeks = faiss.IndexHNSWFlat(dimenzija, podesavanja["hnsw_m"], faiss.METRIC_INNER_PRODUCT)
        indeks.hnsw.efConstruction = podesavanja["hnsw_ef_construction"]
    indeks.add(vektori)
    return indeks


def izgradi(naziv):
    podesavanja = PRISTUPI[naziv]
    fragmenti = napravi_fragmente(ucitaj_dokumente(FOLDER_PODACI), podesavanja)
    print(f"Pristup {naziv}: {len(fragmenti)} fragmenata, računam embedinge...")

    pocetak = time.perf_counter()
    model = embeding_model(podesavanja["model"])
    vektori = u_vektore(model, [podesavanja["prefiks_dokument"] + f["tekst"] for f in fragmenti], podesavanja)
    print(f"  embedinzi gotovi za {time.perf_counter() - pocetak:.0f} s (dimenzija {vektori.shape[1]})")

    indeks = napravi_faiss_indeks(vektori, podesavanja)

    FOLDER_INDEKSI.mkdir(exist_ok=True)
    faiss.write_index(indeks, str(FOLDER_INDEKSI / f"{naziv}.faiss"))
    with open(FOLDER_INDEKSI / f"{naziv}_fragmenti.json", "w", encoding="utf-8") as f:
        json.dump(fragmenti, f, ensure_ascii=False)


def milisekunde_od(pocetak):
    return (time.perf_counter() - pocetak) * 1000


class Pretrazivac:
    """Jedan pristup pretrage. Vraća top k fragmenata i koliko je trajao svaki korak."""

    def __init__(self, naziv):
        self.naziv = naziv
        self.podesavanja = PRISTUPI[naziv]

        naziv_indeksa = self.podesavanja.get("indeks_iz", naziv)
        self.indeks = faiss.read_index(str(FOLDER_INDEKSI / f"{naziv_indeksa}.faiss"))
        if self.podesavanja["indeks"] == "hnsw":
            self.indeks.hnsw.efSearch = self.podesavanja["hnsw_ef_search"]
        with open(FOLDER_INDEKSI / f"{naziv_indeksa}_fragmenti.json", encoding="utf-8") as f:
            self.fragmenti = json.load(f)

        self.model = embeding_model(self.podesavanja["model"])
        self.reranker = None
        if "reranker" in self.podesavanja:
            self.reranker = reranker_model(self.podesavanja["reranker"])

        self.poslednji_upit = None
        self.prepravke = {}  # isto pitanje ne šaljemo LLM-u dvaput

    def pretrazi(self, pitanje, k=TOP_K):
        vremena = {}

        if self.podesavanja.get("prepravka_upita"):
            if pitanje not in self.prepravke:
                self.prepravke[pitanje] = prepravi_upit(pitanje)
            pitanje, vremena["prepravka_ms"] = self.prepravke[pitanje]
        self.poslednji_upit = pitanje

        # sa rerankingom prvo uzimamo više kandidata, pa reranker bira najboljih k
        broj = max(k, self.podesavanja.get("broj_kandidata", k))
        rezultati = self.vektorska_pretraga(pitanje, broj, vremena)

        if self.reranker is not None:
            rezultati = self.rerankuj(pitanje, rezultati, vremena)

        return rezultati[:k], vremena

    def vektorska_pretraga(self, pitanje, k, vremena):
        pocetak = time.perf_counter()
        vektor = u_vektore(self.model, [self.podesavanja["prefiks_upit"] + pitanje], self.podesavanja)
        vremena["embeding_ms"] = milisekunde_od(pocetak)

        pocetak = time.perf_counter()
        skorovi, pozicije = self.indeks.search(vektor, k)
        vremena["pretraga_ms"] = milisekunde_od(pocetak)

        rezultati = []
        for rang, (pozicija, skor) in enumerate(zip(pozicije[0], skorovi[0]), 1):
            if pozicija != -1:
                rezultati.append({**self.fragmenti[pozicija], "skor": float(skor), "rang": rang})
        return rezultati

    def rerankuj(self, pitanje, kandidati, vremena):
        # cross-encoder čita pitanje i fragment zajedno, pa preciznije ocenjuje relevantnost
        pocetak = time.perf_counter()
        skorovi = self.reranker.predict([(pitanje, f["tekst"]) for f in kandidati])
        vremena["rerank_ms"] = milisekunde_od(pocetak)

        poredjani = sorted(zip(skorovi, kandidati), key=lambda par: par[0], reverse=True)
        return [
            {**fragment, "skor": float(skor), "rang": novi_rang, "rang_pre_rerankinga": fragment["rang"]}
            for novi_rang, (skor, fragment) in enumerate(poredjani, 1)
        ]
