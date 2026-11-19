"""Postavljanje sopstvenih pitanja: svaki pristup ispisuje šta je našao i šta je LLM odgovorio.

    python pitaj.py                      interaktivno
    python pitaj.py Ko bira premijera?   jedno pitanje
"""
import sys

from config import PRISTUPI, naziv_propisa, opis_pristupa
from indeksi import Pretrazivac
from llm import generisi_odgovor


def odgovori(pitanje, pretrazivaci):
    for p in pretrazivaci:
        rezultati, vremena = p.pretrazi(pitanje)

        print(f"\n=== Pristup {p.naziv}: {opis_pristupa(p.naziv)}")
        if p.poslednji_upit != pitanje:
            print(f"Prepravljeno pitanje: {p.poslednji_upit}")
        print(f"Pretraga: {sum(vremena.values()):.0f} ms")

        for r in rezultati:
            print(f"  {r['rang']}. {naziv_propisa(r['izvor'])}, član {r['clan']}")

        odgovor, trajanje = generisi_odgovor(pitanje, rezultati)
        print(f"\nOdgovor ({trajanje:.0f} ms):\n{odgovor}")


if __name__ == "__main__":
    print("Učitavam modele...")
    pretrazivaci = [Pretrazivac(naziv) for naziv in PRISTUPI]

    if len(sys.argv) > 1:
        odgovori(" ".join(sys.argv[1:]), pretrazivaci)
    else:
        while pitanje := input("\nPitanje (Enter za kraj): ").strip():
            odgovori(pitanje, pretrazivaci)
