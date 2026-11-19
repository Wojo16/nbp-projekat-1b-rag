"""Preuzima propise sa paragraf.rs i čuva ih kao običan tekst u folderu data/."""
import re

import requests
from bs4 import BeautifulSoup

from config import FOLDER_PODACI, PROPISI

OSNOVNI_URL = "https://www.paragraf.rs/propisi/"


def preuzmi(izvor, stranica):
    odgovor = requests.get(OSNOVNI_URL + stranica, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    odgovor.raise_for_status()
    odgovor.encoding = "utf-8"
    stranica_html = BeautifulSoup(odgovor.text, "html.parser")

    # tekst zakona počinje od prvog "Član" i nalazi se u <main>, ostalo su meniji i reklame
    prvi_clan = stranica_html.find("p", class_="clan")
    if prvi_clan is None:
        raise RuntimeError(f"Na stranici {stranica} nije pronađen nijedan član")
    sadrzaj = prvi_clan.find_parent("main") or prvi_clan.parent
    pasusi = sadrzaj.find_all("p")

    linije = []
    for p in pasusi[pasusi.index(prvi_clan):]:
        tekst = re.sub(r"\s+", " ", p.get_text(" ", strip=True))
        if not tekst:
            continue
        if "clan" in (p.get("class") or []):
            linije.append("")  # prazan red pre svakog člana, lakše se čita
        linije.append(tekst)

    putanja = FOLDER_PODACI / f"{izvor}.txt"
    putanja.write_text("\n".join(linije).strip() + "\n", encoding="utf-8")

    broj_clanova = sum(1 for linija in linije if re.fullmatch(r"Član \d+[a-zA-Z]*", linija))
    print(f"{PROPISI[izvor][0]}: {broj_clanova} članova")


if __name__ == "__main__":
    FOLDER_PODACI.mkdir(exist_ok=True)
    for izvor, (_, stranica) in PROPISI.items():
        preuzmi(izvor, stranica)
