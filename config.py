"""Sva podešavanja projekta na jednom mestu: putanje, propisi, modeli i pristupi koji se porede."""
import sys
from pathlib import Path

# Windows konzola inače ne ume da ispiše č, ć, š, ž, đ
sys.stdout.reconfigure(encoding="utf-8")

KOREN = Path(__file__).parent
FOLDER_PODACI = KOREN / "data"
FOLDER_INDEKSI = KOREN / "indeksi"

# naziv fajla -> (pun naziv propisa, stranica na paragraf.rs)
PROPISI = {
    "ustav_republike_srbije": ("Ustav Republike Srbije", "ustav_republike_srbije.html"),
    "zakon_o_narodnoj_skupstini": ("Zakon o Narodnoj skupštini", "zakon_o_narodnoj_skupstini.html"),
    "poslovnik_narodne_skupstine": ("Poslovnik Narodne skupštine", "poslovnik-narodne-skupstine-republike-srbije.html"),
    "zakon_o_izboru_narodnih_poslanika": ("Zakon o izboru narodnih poslanika", "zakon_o_izboru_narodnih_poslanika.html"),
    "zakon_o_lokalnim_izborima": ("Zakon o lokalnim izborima", "zakon_o_lokalnim_izborima.html"),
    "zakon_o_jedinstvenom_birackom_spisku": ("Zakon o jedinstvenom biračkom spisku", "zakon_o_jedinstvenom_birackom_spisku.html"),
    "zakon_o_referendumu_i_narodnoj_inicijativi": ("Zakon o referendumu i narodnoj inicijativi", "zakon_o_referendumu_i_narodnoj_inicijativi.html"),
    "zakon_o_politickim_strankama": ("Zakon o političkim strankama", "zakon_o_politickim_strankama.html"),
    "zakon_o_finansiranju_politickih_aktivnosti": ("Zakon o finansiranju političkih aktivnosti", "zakon_o_finansiranju_politickih_aktivnosti.html"),
    "zakon_o_vladi": ("Zakon o Vladi", "zakon_o_vladi.html"),
    "zakon_o_predsedniku_republike": ("Zakon o predsedniku Republike", "zakon_o_predsedniku_republike.html"),
}


def naziv_propisa(izvor):
    return PROPISI[izvor][0] if izvor in PROPISI else izvor


TOP_K = 5  # koliko fragmenata se šalje LLM-u

GROQ_MODEL = "openai/gpt-oss-120b"          # pravi odgovor korisniku
GROQ_MODEL_PREPRAVKA = "openai/gpt-oss-20b"  # prepravlja pitanje (pristup D), manji i brži

# Pristupi koji se porede. C i D ne prave svoj indeks, nego koriste indeks pristupa B.
PRISTUPI = {
    "A": {
        "fragmentacija": "fiksna",
        "velicina": 600,
        "preklapanje": 150,
        "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "prefiks_upit": "",
        "prefiks_dokument": "",
        "indeks": "flat_l2",
    },
    "B": {
        "fragmentacija": "po_clanovima",
        "maks_duzina": 1500,
        "model": "intfloat/multilingual-e5-base",
        # e5 modeli su trenirani sa ovim prefiksima, bez njih rade lošije
        "prefiks_upit": "query: ",
        "prefiks_dokument": "passage: ",
        "indeks": "hnsw",
        "hnsw_m": 32,
        "hnsw_ef_construction": 200,
        "hnsw_ef_search": 64,
    },
}

PRISTUPI["C"] = {
    **PRISTUPI["B"],
    "indeks_iz": "B",
    "reranker": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
    "broj_kandidata": 20,
}

PRISTUPI["D"] = {
    **PRISTUPI["C"],
    "prepravka_upita": True,
}


def opis_pristupa(naziv):
    p = PRISTUPI[naziv]
    if p["fragmentacija"] == "fiksna":
        delovi = [f"fiksni fragmenti od {p['velicina']} karaktera (preklapanje {p['preklapanje']})"]
    else:
        delovi = ["fragment = jedan član zakona"]
    delovi.append(p["model"].split("/")[-1])
    if p["indeks"] == "flat_l2":
        delovi.append("IndexFlatL2")
    else:
        delovi.append(f"HNSW (M={p['hnsw_m']}, efSearch={p['hnsw_ef_search']})")
    if "reranker" in p:
        delovi.append(f"reranking top {p['broj_kandidata']}")
    if p.get("prepravka_upita"):
        delovi.append("prepravka upita preko LLM-a")
    return " + ".join(delovi)
