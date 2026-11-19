"""Pravi FAISS indekse za sve pristupe koji imaju svoj indeks (A i B).

    python izgradi_indekse.py        svi
    python izgradi_indekse.py B      samo B
"""
import sys

from config import PRISTUPI
from indeksi import izgradi

if __name__ == "__main__":
    for naziv in sys.argv[1:] or PRISTUPI:
        if "indeks_iz" not in PRISTUPI[naziv]:
            izgradi(naziv)
