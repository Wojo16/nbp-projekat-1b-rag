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

A je osnovni pristup (baseline). B se od A razlikuje u tri stvari odjednom (fragmentacija, model i
indeks), pa sam dodao i pomoćne pristupe koji menjaju samo po jednu stvar, da bi se videlo šta zaista
pravi razliku:

| | Šta je promenjeno |
|---|---|
| **E** | A, ali fragment = član (isti MiniLM model i FlatL2) |
| **G** | B, ali tačna pretraga (IndexFlatIP) umesto HNSW |
| **F** | G, ali model `bge-m3` (1024 dim) umesto e5-base |
| **H** | F + reranking |

## Rezultati

Detaljno, sa svim pronađenim članovima i odgovorima LLM-a: [rezultati.md](rezultati.md).

### Tri glavna pitanja

| Pitanje | Tačan član | A | B | C | D |
|---|---|---|---|---|---|
| Koliko potpisa treba izbornoj listi za parlamentarne izbore? | ZINP čl. 71 | – | 4 | – | 5 |
| Koji je cenzus? | ZINP čl. 128 | 1 | 2 | 1 | 1 |
| Ko raspisuje izbore i koliko pre kraja mandata? | Ustav čl. 101 | 5 | 2 | 1 | 1 |
| **MRR** | | 0.40 | 0.42 | 0.67 | **0.73** |
| Vreme pretrage | | **14 ms** | 31 ms | ~1,2 s | ~1,8 s |

(broj = mesto tačnog člana među 5 pronađenih, – = nije pronađen; ZINP = Zakon o izboru narodnih poslanika)

### Provera na 14 pitanja (3 glavna + 11 dodatnih)

Tri pitanja su premalo, a parametre za C i D sam birao gledajući baš ta tri pitanja. Zato su svi
pristupi provereni i na 11 dodatnih pitanja, kraćih i kolokvijalnijih.

| Pristup | Hit@5 | MRR |
|---|---|---|
| A – fiksno + MiniLM + FlatL2 | 7/14 | 0.35 |
| B – članovi + e5-base + HNSW | 10/14 | 0.47 |
| C – B + reranking | 11/14 | 0.58 |
| D – C + prepravka upita | 12/14 | 0.56 |
| E – članovi + MiniLM + FlatL2 | 5/14 | 0.25 |
| G – članovi + e5-base + tačna pretraga | 10/14 | 0.47 |
| **F – članovi + bge-m3 + tačna pretraga** | 11/14 | **0.61** |
| H – F + reranking | **12/14** | 0.60 |

## Zaključak

- **Embedding model je najvažniji izbor, posebno za srpski.** Kada se menja samo model, MRR raste sa
  0.25 (MiniLM) na 0.47 (multilingual-e5-base) i na 0.61 (bge-m3). `bge-m3` je najbolji pojedinačni
  pristup bez ikakvih dodataka. Višejezični je (više od 100 jezika), ima veće vektore
  (1024) i čita do 8192 tokena, pa ceo član staje u jedan vektor. Cena je sporije pravljenje indeksa
  (6 min naspram 1,5 min za e5-base na procesoru).
- **Fragmentacija po članovima nije bolja sama po sebi, zavisi od modela.** Sa MiniLM-om je čak lošija
  (A 0.35 → E 0.25). MiniLM čita najviše 128 tokena, pa od dugačkog člana vidi samo početak, dok fiksni
  fragmenti od 600 karaktera uglavnom staju. Sa modelima koji čitaju 512+ tokena članovi su prirodna
  celina i daju čitljiv izvor (zakon + član) koji LLM može da citira.
- **HNSW i tačna pretraga daju iste rezultate** (100% istih fragmenata) i obe traju oko 0,2 ms. Na ~1.300
  vektora HNSW nema prednost, isplati se tek kod stotina hiljada vektora, gde je tačna pretraga spora.
- **Reranking pomaže slabijem modelu** (e5-base: 0.47 → 0.58) i podiže tačan član na prvo mesto kad je
  već među kandidatima (pitanje 3: sa 2. na 1. mesto). Kod bge-m3 ne menja MRR (0.61 → 0.60), ali
  pronađe jedno pitanje više. Cena je oko 1,2 s po upitu. Probao sam i veći reranker
  `bge-reranker-v2-m3`: bio je oko 10 puta sporiji i nije bio bolji.
- **Prepravka upita je mešovita.** Na tri glavna pitanja daje najbolji rezultat (0.73), a na svih 14 je
  malo ispod C (0.56 naspram 0.58), uz jedan pronađen član više. Najviše pomaže kod kolokvijalnih izraza
  („premijer“ → „predsednik Vlade“), a ponekad pitanje udalji od teksta zakona. Prva verzija instrukcije
  je pravila greške („cenzus“ je shvatila kao popis stanovništva i izmišljala članove), pa je pooštrena.
  Rezultat D se malo menja između pokretanja, jer LLM ne prepravi pitanje uvek isto.
- **Najteža pitanja su ona sa „blizancem“ u drugom zakonu.** Za pitanje 1 Zakon o lokalnim izborima ima
  skoro isti član o broju potpisa, pa ga svi pristupi stavljaju na prvo mesto. Izbornu tišinu nijedan
  pristup ne nalazi, jer je član 6 formulisan kao zabrana objavljivanja procena rezultata, bez reči
  „tišina“. Kada tačan član nije među fragmentima, LLM uglavnom kaže da odgovor ne može da pronađe,
  umesto da izmisli broj.
- **Preporuka:** bge-m3 + reranking (H) za najviše pronađenih odgovora, ili bge-m3 bez rerankinga (F)
  kada je brzina bitna.

Ograničenja: 14 pitanja je i dalje malo, pa razlike od ±0.05 MRR nisu pouzdane. Rezultati se malo
menjaju između pokretanja (sitne numeričke razlike na procesoru mogu da zamene mesta dva fragmenta
sa skoro istim skorom). Kada pitanje ne kaže o kojim izborima se radi, podrazumevaju se izbori za
narodne poslanike.

## Pokretanje

Potreban je Python 3.13 (FAISS još nema verziju za 3.15).

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env      # pa u .env upisati svoj Groq ključ
.venv\Scripts\python.exe preuzmi_zakone.py     # skida propise u data/
.venv\Scripts\python.exe izgradi_indekse.py    # pravi FAISS indekse (prvi put skida modele, ~10 min)
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
| `pitanja.py` | 3 glavna i 11 dodatnih pitanja, sa tačnim članom i ključnom frazom |
| `evaluacija.py` | poredi pristupe i piše `rezultati.md` |
| `pitaj.py` | interaktivno postavljanje pitanja |
