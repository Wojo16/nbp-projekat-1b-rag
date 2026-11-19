"""Test pitanja za poređenje pristupa.

Za svako pitanje znamo gde je odgovor (propis i član) i ključnu frazu iz tog člana.
Fragment se računa kao pogodak ako sadrži ključnu frazu.
Pitanja su namerno formulisana drugim rečima nego u zakonu.
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
