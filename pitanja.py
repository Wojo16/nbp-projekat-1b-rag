"""Test pitanja za poređenje pristupa.

Za svako pitanje znamo gde je odgovor (propis i član) i ključnu frazu iz tog člana.
Fragment se računa kao pogodak ako sadrži ključnu frazu.
Pitanja su namerno formulisana drugim rečima nego u zakonu.

PITANJA su tri glavna pitanja iz zadatka (za njih se prikazuju i odgovori LLM-a).
DODATNA_PITANJA služe kao provera: tri pitanja su premalo za pouzdan zaključak, a parametri
(reranker model, uputstvo za prepravku) su birani gledajući glavna pitanja, pa ih proveravamo i na drugima.
"""

PITANJA = [
    {
        "pitanje": "Koliko potpisa građana mora da skupi izborna lista da bi mogla da izađe na parlamentarne izbore?",
        "izvor": "zakon_o_izboru_narodnih_poslanika",
        "clan": "71",
        "kljucna_fraza": "najmanje 10.000 pismenih izjava birača",
    },
    {
        "pitanje": "Koji je cenzus, odnosno koliko procenata glasova lista mora da osvoji da bi dobila poslanička mesta?",
        "izvor": "zakon_o_izboru_narodnih_poslanika",
        "clan": "128",
        "kljucna_fraza": "najmanje 3% glasova od broja birača koji su glasali",
    },
    {
        "pitanje": "Ko raspisuje izbore za Narodnu skupštinu i koliko pre kraja mandata to mora da uradi?",
        "izvor": "ustav_republike_srbije",
        "clan": "101",
        "kljucna_fraza": "raspisuje predsednik Republike, 90 dana pre isteka mandata",
    },
]


def pitanje(tekst, izvor, clan, fraza):
    return {"pitanje": tekst, "izvor": izvor, "clan": clan, "kljucna_fraza": fraza}


USTAV = "ustav_republike_srbije"

DODATNA_PITANJA = [
    pitanje("Koliko ima poslanika u skupštini?", USTAV, "100", "Narodnu skupštinu čini 250 narodnih poslanika"),
    pitanje("Koliko dugo traje mandat poslanika?", USTAV, "102", "traje četiri godine"),
    pitanje("Na koliko godina se bira predsednik države?", USTAV, "116", "Mandat predsednika Republike traje pet godina"),
    pitanje("Može li ista osoba tri puta da bude predsednik?", USTAV, "116",
            "Niko ne može više od dva puta da bude biran za predsednika Republike"),
    pitanje("Kako se smenjuje predsednik Republike?", USTAV, "118",
            "glasovima najmanje dve trećine narodnih poslanika"),
    pitanje("Može li poslanik da bude krivično gonjen?", USTAV, "103", "Narodni poslanik uživa imunitet"),
    pitanje("Koliko građana treba da bi sami predložili zakon?", USTAV, "107", "najmanje 30.000 birača"),
    pitanje("Koliko ljudi je potrebno da se osnuje stranka?", "zakon_o_politickim_strankama", "8",
            "najmanje 10.000 punoletnih"),
    pitanje("Koliko osnivača treba stranci nacionalne manjine?", "zakon_o_politickim_strankama", "9",
            "najmanje 1.000 punoletnih"),
    pitanje("Od kada počinje izborna tišina?", "zakon_o_izboru_narodnih_poslanika", "6",
            "Zabranjeno je 48 časova pre dana glasanja"),
    pitanje("Koliko birača može da traži referendum o pitanju iz nadležnosti skupštine?",
            "zakon_o_referendumu_i_narodnoj_inicijativi", "46", "na zahtev najmanje 100.000 birača"),
]
