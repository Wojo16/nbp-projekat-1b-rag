"""Učitavanje dokumenata i dve vrste fragmentacije: fiksna dužina i po članovima zakona."""
import re

from pypdf import PdfReader

from config import naziv_propisa

CLAN = re.compile(r"Član (\d+[a-zA-Z]*)")
CLAN_U_SVOM_REDU = re.compile(r"^Član (\d+[a-zA-Z]*)$", re.MULTILINE)


def ucitaj_dokumente(folder):
    """Čita sve .txt, .md i .pdf fajlove iz foldera."""
    dokumenti = []
    for putanja in sorted(folder.iterdir()):
        nastavak = putanja.suffix.lower()
        if nastavak in (".txt", ".md"):
            tekst = putanja.read_text(encoding="utf-8")
        elif nastavak == ".pdf":
            tekst = "\n".join(strana.extract_text() or "" for strana in PdfReader(putanja).pages)
        else:
            continue
        dokumenti.append({"izvor": putanja.stem, "tekst": tekst})
    return dokumenti


def fiksni_fragmenti(dokument, velicina, preklapanje):
    """Seče tekst na delove iste dužine, bez obzira na to gde počinje i završava se član."""
    tekst = re.sub(r"\s+", " ", dokument["tekst"]).strip()
    pozicije_clanova = [(m.start(), m.group(1)) for m in CLAN.finditer(tekst)]

    fragmenti = []
    for pocetak in range(0, len(tekst), velicina - preklapanje):
        deo = tekst[pocetak:pocetak + velicina]
        if len(deo) < 50 and fragmenti:  # ne pravimo fragment od par reči na kraju
            break

        # zapisujemo kojim članovima fragment pripada, da bi se video izvor u rezultatima
        clanovi = [clan for poz, clan in pozicije_clanova if pocetak <= poz < pocetak + velicina]
        if not clanovi:
            clanovi = [clan for poz, clan in pozicije_clanova if poz < pocetak][-1:]

        fragmenti.append({"izvor": dokument["izvor"], "clan": ", ".join(clanovi), "tekst": deo})
    return fragmenti


def je_naslov(red):
    """Naslovi članova su kratki i ne završavaju se interpunkcijom (npr. "Mandat narodnog poslanika")."""
    return 0 < len(red) < 120 and not red.endswith((".", ":", ";", ","))


def fragmenti_po_clanovima(dokument, maks_duzina):
    """Jedan član = jedan fragment. Predugački članovi se dele po stavovima."""
    tekst = dokument["tekst"]
    pogoci = list(CLAN_U_SVOM_REDU.finditer(tekst))

    fragmenti = []
    for i, pogodak in enumerate(pogoci):
        kraj = pogoci[i + 1].start() if i + 1 < len(pogoci) else len(tekst)
        redovi = tekst[pogodak.end():kraj].strip().split("\n")

        # poslednji red je često naslov sledećeg člana, on ne pripada ovom
        while len(redovi) > 1 and je_naslov(redovi[-1].strip()):
            redovi.pop()

        red_iznad = tekst[:pogodak.start()].rstrip().rsplit("\n", 1)[-1].strip()
        naslov = f" ({red_iznad})" if je_naslov(red_iznad) else ""
        zaglavlje = f"{naziv_propisa(dokument['izvor'])}, član {pogodak.group(1)}{naslov}"

        for deo in podeli_na_delove(redovi, maks_duzina):
            fragmenti.append({
                "izvor": dokument["izvor"],
                "clan": pogodak.group(1),
                "tekst": f"{zaglavlje}\n{deo}",
            })
    return fragmenti


def podeli_na_delove(stavovi, maks_duzina):
    delovi, trenutni = [], ""
    for stav in (s.strip() for s in stavovi):
        if not stav:
            continue
        if trenutni and len(trenutni) + len(stav) > maks_duzina:
            delovi.append(trenutni)
            trenutni = ""
        trenutni = f"{trenutni}\n{stav}" if trenutni else stav
    if trenutni:
        delovi.append(trenutni)
    return delovi


def napravi_fragmente(dokumenti, podesavanja):
    fragmenti = []
    for dokument in dokumenti:
        if podesavanja["fragmentacija"] == "fiksna":
            fragmenti += fiksni_fragmenti(dokument, podesavanja["velicina"], podesavanja["preklapanje"])
        else:
            fragmenti += fragmenti_po_clanovima(dokument, podesavanja["maks_duzina"])
    return fragmenti
