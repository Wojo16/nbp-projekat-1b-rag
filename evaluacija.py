"""Poredi pristupe na test pitanjima i pravi izveštaj rezultati.md.

    python evaluacija.py             sa odgovorima LLM-a
    python evaluacija.py --bez-llm   samo pretraga (brže, ne troši Groq)
"""
import re
import statistics
import sys
from datetime import date

from config import GLAVNI_PRISTUPI, GROQ_MODEL, KOREN, TOP_K, naziv_propisa, opis_pristupa
from indeksi import Pretrazivac
from llm import generisi_odgovor
from pitanja import DODATNA_PITANJA, PITANJA

SVI_PRISTUPI = GLAVNI_PRISTUPI + ["E", "G", "F", "H"]
BROJ_MERENJA = 10  # vreme merimo više puta i uzimamo medijanu, jedno merenje zna da odstupa


def normalizuj(tekst):
    return re.sub(r"\s+", " ", tekst).lower()


def je_pogodak(fragment, pitanje):
    return (fragment["izvor"] == pitanje["izvor"]
            and normalizuj(pitanje["kljucna_fraza"]) in normalizuj(fragment["tekst"]))


def rang_pogotka(fragmenti, pitanje):
    return next((f["rang"] for f in fragmenti if je_pogodak(f, pitanje)), None)


def mrr(rangovi):
    """Mean Reciprocal Rank: prosek od 1/rang, a 0 ako tačan član nije pronađen. 1.00 je savršeno."""
    return statistics.mean(1 / r if r else 0 for r in rangovi)


def izmeri(pretrazivac, pitanje):
    ukupno, samo_indeks = [], []
    for _ in range(BROJ_MERENJA):
        _, vremena = pretrazivac.pretrazi(pitanje)
        ukupno.append(sum(vremena.values()))
        samo_indeks.append(vremena["pretraga_ms"])
    return statistics.median(ukupno), statistics.median(samo_indeks)


def oceni(pretrazivaci, sa_llm):
    glavna, dodatna = [], []

    for pitanje in PITANJA:
        po_pristupu = {}
        for naziv in GLAVNI_PRISTUPI:
            p = pretrazivaci[naziv]
            fragmenti, _ = p.pretrazi(pitanje["pitanje"])
            vreme, _ = izmeri(p, pitanje["pitanje"])
            po_pristupu[naziv] = {
                "rang": rang_pogotka(fragmenti, pitanje),
                "vreme_ms": vreme,
                "fragmenti": fragmenti,
                "upit": p.poslednji_upit,
                "odgovor": generisi_odgovor(pitanje["pitanje"], fragmenti)[0] if sa_llm else None,
            }
        glavna.append((pitanje, po_pristupu))
        print(f"glavno: {pitanje['pitanje'][:60]}")

    for pitanje in PITANJA + DODATNA_PITANJA:
        rangovi, top5 = {}, {}
        for naziv, p in pretrazivaci.items():
            fragmenti, _ = p.pretrazi(pitanje["pitanje"])
            rangovi[naziv] = rang_pogotka(fragmenti, pitanje)
            top5[naziv] = [(f["izvor"], f["clan"]) for f in fragmenti]
        dodatna.append((pitanje, rangovi, top5))
        print(f"provera: {pitanje['pitanje'][:60]}")

    # brzina samog indeksa: HNSW (B) naspram tačne pretrage (G), isti vektori
    brzina_indeksa = {
        naziv: statistics.mean(izmeri(pretrazivaci[naziv], q["pitanje"])[1] for q in PITANJA + DODATNA_PITANJA)
        for naziv in ("B", "G")
    }
    return glavna, dodatna, brzina_indeksa


def tabela(zaglavlje, redovi):
    linije = ["| " + " | ".join(zaglavlje) + " |", "|---" * len(zaglavlje) + "|"]
    linije += ["| " + " | ".join(str(c) for c in red) + " |" for red in redovi]
    return "\n".join(linije) + "\n"


def napisi_izvestaj(glavna, dodatna, brzina_indeksa, broj_fragmenata):
    r = []
    sva_pitanja = len(dodatna)

    r.append("# Poređenje RAG pristupa: propisi o Narodnoj skupštini i izborima\n")
    r.append(f"Baza znanja: Ustav i 10 zakona/poslovnika o skupštini, izborima i političkom sistemu "
             f"(paragraf.rs). Pristup A ima {broj_fragmenata['A']} fragmenata, a pristupi koji dele na "
             f"članove {broj_fragmenata['B']}. Odgovore piše `{GROQ_MODEL}` preko Groq-a, a LLM dobija "
             f"top {TOP_K} fragmenata. Pokrenuto {date.today():%d.%m.%Y}.\n")

    r.append("## Pristupi\n")
    for naziv in GLAVNI_PRISTUPI:
        r.append(f"- **{naziv}**: {opis_pristupa(naziv)}")
    r.append("\nPomoćni pristupi (služe samo da se izdvoji efekat jedne promene):\n")
    for naziv, objasnjenje in [("E", "kao A, ali fragment = član"),
                               ("G", "kao B, ali tačna pretraga umesto HNSW"),
                               ("F", "kao G, ali model bge-m3"),
                               ("H", "kao F, plus reranking")]:
        r.append(f"- **{naziv}** ({objasnjenje}): {opis_pristupa(naziv)}")
    r.append("")

    # --- glavna tri pitanja ---
    r.append("## Tri glavna pitanja\n")
    r.append(f"Broj je mesto na kom se našao tačan član (od {TOP_K}), a crtica znači da ga nema.\n")
    redovi = []
    for broj, (pitanje, po) in enumerate(glavna, 1):
        redovi.append([f"{broj}. {pitanje['pitanje']}"] + [po[n]["rang"] or "–" for n in GLAVNI_PRISTUPI])
    redovi.append(["**MRR**"] + [f"**{mrr([po[n]['rang'] for _, po in glavna]):.2f}**" for n in GLAVNI_PRISTUPI])
    redovi.append(["Prosečno vreme pretrage"]
                  + [f"{statistics.mean(po[n]['vreme_ms'] for _, po in glavna):.0f} ms" for n in GLAVNI_PRISTUPI])
    r.append(tabela(["Pitanje"] + GLAVNI_PRISTUPI, redovi))
    r.append(f"MRR (Mean Reciprocal Rank) je prosek vrednosti 1/rang: 1.00 znači da je tačan član uvek prvi. "
             f"Vreme je cela pretraga bez pisanja odgovora (medijana od {BROJ_MERENJA} merenja).\n")

    # --- provera na svim pitanjima ---
    r.append(f"## Provera na {sva_pitanja} pitanja\n")
    r.append("Tri pitanja su premalo za pouzdan zaključak, pa su svi pristupi pušteni i na dodatna pitanja "
             "(kraća i kolokvijalnija, vidi `pitanja.py`). Hit@5 je u koliko pitanja je tačan član uopšte "
             "pronađen.\n")
    redovi = []
    for naziv in SVI_PRISTUPI:
        rangovi = [rang[naziv] for _, rang, _ in dodatna]
        pogodaka = sum(1 for x in rangovi if x)
        redovi.append([f"**{naziv}**", opis_pristupa(naziv), f"{pogodaka}/{sva_pitanja}", f"{mrr(rangovi):.2f}"])
    r.append(tabela(["Pristup", "Opis", "Hit@5", "MRR"], redovi))

    # --- šta pravi razliku ---
    m = {n: mrr([rang[n] for _, rang, _ in dodatna]) for n in SVI_PRISTUPI}
    isti_top5 = statistics.mean(
        len(set(top5["B"]) & set(top5["G"])) / TOP_K for _, _, top5 in dodatna)
    r.append("## Šta pravi razliku\n")
    r.append("Svaki red poredi dva pristupa koji se razlikuju u samo jednoj stvari (MRR na svih "
             f"{sva_pitanja} pitanja).\n")
    r.append(tabela(["Promena", "Pre", "Posle"], [
        ["Fragmentacija: fiksna dužina → po članovima (MiniLM)", f"A: {m['A']:.2f}", f"E: {m['E']:.2f}"],
        ["Model: MiniLM → multilingual-e5-base (po članovima)", f"E: {m['E']:.2f}", f"G: {m['G']:.2f}"],
        ["Model: multilingual-e5-base → bge-m3 (po članovima, tačna pretraga)", f"G: {m['G']:.2f}", f"F: {m['F']:.2f}"],
        ["Indeks: tačna pretraga → HNSW (e5-base)", f"G: {m['G']:.2f}", f"B: {m['B']:.2f}"],
        ["Reranking (e5-base)", f"B: {m['B']:.2f}", f"C: {m['C']:.2f}"],
        ["Reranking (bge-m3)", f"F: {m['F']:.2f}", f"H: {m['H']:.2f}"],
        ["Prepravka upita", f"C: {m['C']:.2f}", f"D: {m['D']:.2f}"],
    ]))
    r.append(f"HNSW je u proseku vratio {isti_top5:.0%} istih fragmenata kao tačna pretraga. Sama pretraga "
             f"indeksa traje {brzina_indeksa['G']:.3f} ms (tačna) naspram {brzina_indeksa['B']:.3f} ms (HNSW): "
             f"sa ~1.300 vektora razlika je zanemarljiva, HNSW se isplati tek na mnogo većim bazama.\n")

    # --- detalji glavnih pitanja ---
    for broj, (pitanje, po) in enumerate(glavna, 1):
        r.append(f"## Pitanje {broj}\n")
        r.append(f"> {pitanje['pitanje']}\n")
        r.append(f"Odgovor je u: **{naziv_propisa(pitanje['izvor'])}, član {pitanje['clan']}**, "
                 f"„{pitanje['kljucna_fraza']}“\n")
        redovi = []
        for naziv in GLAVNI_PRISTUPI:
            pronadjeno = []
            for f in po[naziv]["fragmenti"]:
                oznaka = f"{naziv_propisa(f['izvor'])} {f['clan']}"
                pronadjeno.append(f"**{oznaka}**" if je_pogodak(f, pitanje) else oznaka)
            redovi.append([naziv, po[naziv]["rang"] or "–", "; ".join(pronadjeno)])
        r.append(tabela(["Pristup", "Mesto tačnog člana", "Šta je pronađeno (redom)"], redovi))

        if po["D"]["upit"] != pitanje["pitanje"]:
            r.append(f"Pristup D je pitanje prepravio u: _{po['D']['upit']}_\n")

        if po["A"]["odgovor"] is not None:
            r.append("<details><summary>Odgovori LLM-a</summary>\n")
            for naziv in GLAVNI_PRISTUPI:
                r.append(f"**{naziv}:**\n")
                r.append("> " + po[naziv]["odgovor"].replace("\n", "\n> ") + "\n")
            r.append("</details>\n")

    # --- dodatna pitanja po pristupima ---
    r.append("## Dodatna pitanja, mesto tačnog člana\n")
    redovi = []
    for pitanje, rang, _ in dodatna[len(PITANJA):]:
        izvor = f"{naziv_propisa(pitanje['izvor'])} {pitanje['clan']}"
        redovi.append([pitanje["pitanje"], izvor] + [rang[n] or "–" for n in SVI_PRISTUPI])
    r.append(tabela(["Pitanje", "Tačan član"] + SVI_PRISTUPI, redovi))

    return "\n".join(r)


if __name__ == "__main__":
    print("Učitavam modele...")
    pretrazivaci = {naziv: Pretrazivac(naziv) for naziv in SVI_PRISTUPI}
    broj_fragmenata = {naziv: len(p.fragmenti) for naziv, p in pretrazivaci.items()}

    glavna, dodatna, brzina_indeksa = oceni(pretrazivaci, sa_llm="--bez-llm" not in sys.argv)

    putanja = KOREN / "rezultati.md"
    putanja.write_text(napisi_izvestaj(glavna, dodatna, brzina_indeksa, broj_fragmenata), encoding="utf-8")
    print(f"\nIzveštaj je u {putanja}")
