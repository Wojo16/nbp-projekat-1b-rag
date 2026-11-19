# NBP/BP 2026 – Projekat 1b: RAG sistem nad propisima o Narodnoj skupštini

RAG sistem koji odgovara na pitanja o Ustavu, Narodnoj skupštini, izborima i političkom sistemu Srbije.
Pitanje se pretvori u vektor, u vektorskom indeksu se nađu najsličniji delovi propisa, a LLM
(preko Groq-a) na osnovu njih napiše odgovor i navede član zakona.

Poredim četiri pristupa i gledam koji tačan član stavlja više na listi i koliko je brz.

## Baza znanja

Ustav i 10 propisa preuzetih sa [paragraf.rs](https://www.paragraf.rs), ukupno oko 1.230 članova,
na srpskom jeziku:

Ustav Republike Srbije, Poslovnik Narodne skupštine, Zakon o Narodnoj skupštini, Zakon o izboru
narodnih poslanika, Zakon o lokalnim izborima, Zakon o jedinstvenom biračkom spisku, Zakon o referendumu
i narodnoj inicijativi, Zakon o političkim strankama, Zakon o finansiranju političkih aktivnosti,
Zakon o Vladi, Zakon o predsedniku Republike.

Zakoni su dobar izvor za ovakav projekat jer su podeljeni na članove (prirodne celine), pa za svako
pitanje tačno znam gde je odgovor.

## Pristupi

| | Fragmentacija | Embedding model | Indeks | Dodatno |
|---|---|---|---|---|
| **A** | fiksno 600 karaktera, preklapanje 150 (1756 fragmenata) | paraphrase-multilingual-MiniLM-L12-v2 (384 dim) | IndexFlatL2 | – |
| **B** | jedan član = jedan fragment (1310 fragmenata) | multilingual-e5-base (768 dim) | HNSW, kosinusna sličnost | – |
| **C** | kao B | kao B | kao B | reranking: uzima top 20, cross-encoder ih ponovo rangira |
| **D** | kao B | kao B | kao B | reranking + LLM pre pretrage prepravi pitanje u pravni jezik |

A je osnovni pristup (baseline). B menja sve tri stvari odjednom: fragmentaciju, model i indeks.
C i D su nadogradnje na B i koriste njegov indeks.

## Rezultati

Detaljno, sa svim pronađenim članovima i odgovorima LLM-a: [rezultati.md](rezultati.md).

| Pitanje | Tačan član | A | B | C | D |
|---|---|---|---|---|---|
| Koliko potpisa treba izbornoj listi za parlamentarne izbore? | ZINP čl. 71 | – | 4 | – | 5 |
| Koji je cenzus? | ZINP čl. 128 | 1 | 1 | 1 | 1 |
| Ko raspisuje izbore i koliko pre kraja mandata? | Ustav čl. 101 | 5 | 2 | 1 | 1 |
| **MRR** | | 0.40 | 0.58 | 0.67 | **0.73** |
| Vreme pretrage | | **14 ms** | 32 ms | ~1,2 s | ~2,1 s |

(broj = mesto tačnog člana među 5 pronađenih, – = nije pronađen; ZINP = Zakon o izboru narodnih poslanika)

## Zaključak

- **Fragmentacija po članovima je bolja od fiksne dužine.** Fiksni fragment često preseče član na pola
  ili spoji kraj jednog i početak drugog, pa se značenje razvodni. Kod A je tačan član za pitanje 3 tek
  na 5. mestu, a kod B na 2.
- **Bolji embedding model pravi razliku na srpskom.** e5-base je sporiji (32 ms naspram 14 ms po upitu),
  ali bolje razume pitanja postavljena drugim rečima nego u zakonu.
- **Reranking pomera tačan član na vrh** kada je već među kandidatima (pitanje 3: sa 2. na 1. mesto).
  Cena je oko 1,2 s po upitu, jer cross-encoder čita pitanje zajedno sa svakim od 20 kandidata.
  Probao sam i veći reranker `bge-reranker-v2-m3`: bio je oko 10 puta sporiji i nije bio bolji.
- **Prepravka upita najviše pomaže kod kratkih i kolokvijalnih pitanja**, npr. „ko bira premijera“ ili
  „može li predsednik da raspusti parlament“. U zakonima piše „predsednik Vlade“ i „Narodna skupština“,
  pa bez prepravke pretraga promaši. Prva verzija instrukcije je pravila greške („cenzus“ je shvatila
  kao popis stanovništva i izmišljala članove), pa je instrukcija pooštrena: samo kontekst izbora i
  bez dodavanja činjenica.
- **Pitanje 1 je najteže.** Zakon o lokalnim izborima ima skoro isti član o broju potpisa, pa ga svi
  pristupi stavljaju na prvo mesto. Kada tačan član nije među fragmentima, LLM uglavnom pošteno kaže da
  odgovor ne može da pronađe, umesto da izmisli broj. To je i glavna prednost RAG-a.
- **Brzina:** sama pretraga indeksa traje ispod 1 ms za oba indeksa, jer je baza mala (oko 1.300–1.800
  vektora). Vreme odlazi na pretvaranje pitanja u vektor, reranking i pozive LLM-u.

Pretpostavka: kada pitanje ne kaže o kojim izborima se radi, podrazumevaju se izbori za narodne poslanike.

## Pokretanje

Potreban je Python 3.13 (FAISS još nema verziju za 3.15).

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env      # pa u .env upisati svoj Groq ključ
.venv\Scripts\python.exe preuzmi_zakone.py     # skida propise u data/
.venv\Scripts\python.exe izgradi_indekse.py    # pravi FAISS indekse (prvi put skida modele, par minuta)
.venv\Scripts\python.exe pitaj.py              # postavljanje sopstvenih pitanja
.venv\Scripts\python.exe evaluacija.py         # poređenje pristupa -> rezultati.md
```

## Fajlovi

| Fajl | Šta radi |
|---|---|
| `config.py` | sva podešavanja: propisi, modeli, parametri pristupa |
| `preuzmi_zakone.py` | skida propise sa paragraf.rs u `data/` |
| `fragmentacija.py` | učitava tekst i deli ga na fragmente (fiksno ili po članovima) |
| `indeksi.py` | pravi FAISS indekse i pretražuje ih (uz reranking i prepravku upita) |
| `llm.py` | pozivi Groq-u: odgovor na pitanje i prepravka upita |
| `pitanja.py` | test pitanja sa tačnim članom i ključnom frazom |
| `evaluacija.py` | poredi pristupe i piše `rezultati.md` |
| `pitaj.py` | interaktivno postavljanje pitanja |
