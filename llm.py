"""Komunikacija sa LLM-om preko Groq-a: generisanje odgovora i prepravka upita."""
import os
import time

from dotenv import load_dotenv
from groq import Groq

from config import GROQ_MODEL, GROQ_MODEL_PREPRAVKA, naziv_propisa

load_dotenv()  # čita GROQ_API_KEY iz fajla .env

UPUTSTVO_ZA_ODGOVOR = (
    "Ti si asistent koji odgovara na pitanja o Ustavu, Narodnoj skupštini, izborima i političkom sistemu "
    "Republike Srbije. Odgovaraj isključivo na osnovu priloženih fragmenata propisa, na srpskom jeziku (latinica). "
    "Navedi propis i član na koji se oslanjaš. "
    "Ako odgovor nije u fragmentima, reci da ga ne možeš pronaći u priloženom tekstu."
)

UPUTSTVO_ZA_PREPRAVKU = (
    "Korisnik postavlja pitanje o političkom sistemu Republike Srbije: Ustav, Narodna skupština i njen Poslovnik, "
    "izbori, referendum, političke stranke, Vlada i predsednik Republike. Tumači pitanje isključivo u tom kontekstu. "
    "Prepiši ga u jedno kratko, potpuno pitanje na srpskom (latinica), terminologijom kakva se koristi u zakonima: "
    "kolokvijalne izraze zameni zvaničnim (npr. premijer → predsednik Vlade, parlament → Narodna skupština, "
    "poslanik → narodni poslanik) i razreši skraćenice. "
    "Ako nivo izbora nije naveden, podrazumevaj izbore za narodne poslanike. "
    "Ne dodaji činjenice, brojeve, rokove, nazive zakona ni brojeve članova koje korisnik nije naveo. "
    "Vrati samo prepravljeno pitanje, bez objašnjenja."
)

_groq = None


def groq():
    global _groq
    if _groq is None:
        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("Nedostaje GROQ_API_KEY. Napravi fajl .env po uzoru na .env.example.")
        _groq = Groq()
    return _groq


def pitaj_model(model, uputstvo, poruka):
    pocetak = time.perf_counter()
    odgovor = groq().chat.completions.create(
        model=model,
        temperature=0,  # bez nasumičnosti, da rezultati budu ponovljivi
        messages=[
            {"role": "system", "content": uputstvo},
            {"role": "user", "content": poruka},
        ],
    )
    return odgovor.choices[0].message.content.strip(), (time.perf_counter() - pocetak) * 1000


def prepravi_upit(pitanje):
    return pitaj_model(GROQ_MODEL_PREPRAVKA, UPUTSTVO_ZA_PREPRAVKU, pitanje)


def generisi_odgovor(pitanje, fragmenti):
    kontekst = "\n\n".join(
        f"[{i}] {naziv_propisa(f['izvor'])}, član {f['clan']}:\n{f['tekst']}"
        for i, f in enumerate(fragmenti, 1)
    )
    return pitaj_model(GROQ_MODEL, UPUTSTVO_ZA_ODGOVOR, f"Fragmenti:\n{kontekst}\n\nPitanje: {pitanje}")
