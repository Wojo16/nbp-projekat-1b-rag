"""Poredi sve pristupe na test pitanjima i pravi izveštaj rezultati.md.

    python evaluacija.py             sa odgovorima LLM-a
    python evaluacija.py --bez-llm   samo pretraga (brže, ne troši Groq)
"""
import re
import statistics
import sys
from datetime import date

from config import GROQ_MODEL, KOREN, PRISTUPI, TOP_K, naziv_propisa, opis_pristupa
from indeksi import Pretrazivac
from llm import generisi_odgovor
from pitanja import PITANJA

BROJ_MERENJA = 20  # vreme merimo više puta i uzimamo medijanu, jedno merenje zna da odstupa


def normalizuj(tekst):
    return re.sub(r"\s+", " ", tekst).lower()


def je_pogodak(fragment, pitanje):
    return normalizuj(pitanje["kljucna_fraza"]) in normalizuj(fragment["tekst"])


def izmeri_vreme(pretrazivac, pitanje):
    ukupna_vremena = []
    for _ in range(BROJ_MERENJA):
        _, vremena = pretrazivac.pretrazi(pitanje)
        ukupna_vremena.append(sum(vremena.values()))
    return statistics.median(ukupna_vremena)


def oceni(pretrazivaci, sa_llm):
    """Za svako pitanje i svaki pristup: rang pogotka, vreme, pronađeni fragmenti i odgovor."""
    rezultati = []
    for pitanje in PITANJA:
        po_pristupu = {}
        for p in pretrazivaci:
            fragmenti, _ = p.pretrazi(pitanje["pitanje"])
            rang = next((f["rang"] for f in fragmenti if je_pogodak(f, pitanje)), None)
            po_pristupu[p.naziv] = {
                "rang": rang,
                "vreme_ms": izmeri_vreme(p, pitanje["pitanje"]),
                "fragmenti": fragmenti,
                "upit": p.poslednji_upit,
                "odgovor": generisi_odgovor(pitanje["pitanje"], fragmenti)[0] if sa_llm else None,
            }
            print(f"{pitanje['pitanje'][:50]}... pristup {p.naziv}: rang {rang or '-'}")
        rezultati.append((pitanje, po_pristupu))
    return rezultati


def napisi_izvestaj(rezultati, broj_fragmenata):
    pristupi = list(PRISTUPI)
    redovi = []
    dodaj = redovi.append

    dodaj("# Poređenje RAG pristupa: propisi o Narodnoj skupštini i izborima\n")
    dodaj(f"Baza znanja: Ustav i 10 zakona/poslovnika o skupštini, izborima i političkom sistemu "
          f"(paragraf.rs). Pristup A ima {broj_fragmenata['A']} fragmenata, pristupi B, C i D "
          f"{broj_fragmenata['B']}. Odgovore piše `{GROQ_MODEL}` preko Groq-a, a LLM dobija top {TOP_K} "
          f"fragmenata. Pokrenuto {date.today():%d.%m.%Y}.\n")

    dodaj("## Pristupi\n")
    for naziv in pristupi:
        dodaj(f"- **{naziv}**: {opis_pristupa(naziv)}")
    dodaj("")

    dodaj("## Ukratko\n")
    dodaj(f"Broj u tabeli je mesto na kom se našao tačan član (od {TOP_K}), a crtica znači da ga nema.\n")
    dodaj("| Pitanje | " + " | ".join(pristupi) + " |")
    dodaj("|---" * (len(pristupi) + 1) + "|")
    for broj, (pitanje, po_pristupu) in enumerate(rezultati, 1):
        rangovi = [str(po_pristupu[n]["rang"] or "–") for n in pristupi]
        dodaj(f"| {broj}. {pitanje['pitanje']} | " + " | ".join(rangovi) + " |")

    mrr = {n: statistics.mean(1 / r[n]["rang"] if r[n]["rang"] else 0 for _, r in rezultati) for n in pristupi}
    vreme = {n: statistics.mean(r[n]["vreme_ms"] for _, r in rezultati) for n in pristupi}
    dodaj("| **MRR** | " + " | ".join(f"**{mrr[n]:.2f}**" for n in pristupi) + " |")
    dodaj("| Prosečno vreme pretrage | " + " | ".join(f"{vreme[n]:.0f} ms" for n in pristupi) + " |")
    dodaj("")

    najprecizniji = max(pristupi, key=lambda n: mrr[n])
    najbrzi = min(pristupi, key=lambda n: vreme[n])
    dodaj(f"Najprecizniji je pristup **{najprecizniji}** (MRR {mrr[najprecizniji]:.2f}), a najbrži "
          f"**{najbrzi}** ({vreme[najbrzi]:.0f} ms). MRR je prosek vrednosti 1/rang, pa je 1.00 savršen "
          f"rezultat (tačan član uvek na prvom mestu). Vreme ne uključuje pisanje odgovora, to je "
          f"medijana od {BROJ_MERENJA} merenja.\n")

    for broj, (pitanje, po_pristupu) in enumerate(rezultati, 1):
        dodaj(f"## Pitanje {broj}\n")
        dodaj(f"> {pitanje['pitanje']}\n")
        dodaj(f"Odgovor je u: **{naziv_propisa(pitanje['izvor'])}, član {pitanje['clan']}**, "
              f"„{pitanje['kljucna_fraza']}“\n")

        dodaj("| Pristup | Mesto tačnog člana | Šta je pronađeno (redom) |")
        dodaj("|---|---|---|")
        for naziv in pristupi:
            r = po_pristupu[naziv]
            pronadjeno = []
            for f in r["fragmenti"]:
                oznaka = f"{naziv_propisa(f['izvor'])} {f['clan']}"
                pronadjeno.append(f"**{oznaka}**" if je_pogodak(f, pitanje) else oznaka)
            dodaj(f"| {naziv} | {r['rang'] or '–'} | {'; '.join(pronadjeno)} |")
        dodaj("")

        prepravke = [po_pristupu[n]["upit"] for n in pristupi if po_pristupu[n]["upit"] != pitanje["pitanje"]]
        if prepravke:
            dodaj(f"Pristup D je pitanje prepravio u: _{prepravke[0]}_\n")

        if po_pristupu[pristupi[0]]["odgovor"] is not None:
            dodaj("<details><summary>Odgovori LLM-a</summary>\n")
            for naziv in pristupi:
                dodaj(f"**{naziv}:**\n")
                dodaj("> " + po_pristupu[naziv]["odgovor"].replace("\n", "\n> ") + "\n")
            dodaj("</details>\n")

    return "\n".join(redovi) + "\n"


if __name__ == "__main__":
    print("Učitavam modele...")
    pretrazivaci = [Pretrazivac(naziv) for naziv in PRISTUPI]
    broj_fragmenata = {p.naziv: len(p.fragmenti) for p in pretrazivaci}

    rezultati = oceni(pretrazivaci, sa_llm="--bez-llm" not in sys.argv)

    putanja = KOREN / "rezultati.md"
    putanja.write_text(napisi_izvestaj(rezultati, broj_fragmenata), encoding="utf-8")
    print(f"\nIzveštaj je u {putanja}")
