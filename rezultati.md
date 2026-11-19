# Poređenje RAG pristupa: propisi o Narodnoj skupštini i izborima

Baza znanja: Ustav i 10 zakona/poslovnika o skupštini, izborima i političkom sistemu (paragraf.rs). Pristup A ima 1756 fragmenata, a pristupi koji dele na članove 1310. Odgovore piše `openai/gpt-oss-120b` preko Groq-a, a LLM dobija top 5 fragmenata. Pokrenuto 19.11.2026.

## Pristupi

- **A**: fiksni fragmenti od 600 karaktera (preklapanje 150) + paraphrase-multilingual-MiniLM-L12-v2 + IndexFlatL2
- **B**: fragment = jedan član zakona + multilingual-e5-base + HNSW (M=32, efSearch=64)
- **C**: fragment = jedan član zakona + multilingual-e5-base + HNSW (M=32, efSearch=64) + reranking top 20
- **D**: fragment = jedan član zakona + multilingual-e5-base + HNSW (M=32, efSearch=64) + reranking top 20 + prepravka upita preko LLM-a

Pomoćni pristupi (služe samo da se izdvoji efekat jedne promene):

- **E** (kao A, ali fragment = član): fragment = jedan član zakona + paraphrase-multilingual-MiniLM-L12-v2 + IndexFlatL2
- **G** (kao B, ali tačna pretraga umesto HNSW): fragment = jedan član zakona + multilingual-e5-base + IndexFlatIP (tačna pretraga, kosinusna sličnost)
- **F** (kao G, ali model bge-m3): fragment = jedan član zakona + bge-m3 + IndexFlatIP (tačna pretraga, kosinusna sličnost)
- **H** (kao F, plus reranking): fragment = jedan član zakona + bge-m3 + IndexFlatIP (tačna pretraga, kosinusna sličnost) + reranking top 20

## Tri glavna pitanja

Broj je mesto na kom se našao tačan član (od 5), a crtica znači da ga nema.

| Pitanje | A | B | C | D |
|---|---|---|---|---|
| 1. Koliko potpisa građana mora da skupi izborna lista da bi mogla da izađe na parlamentarne izbore? | – | 4 | – | 5 |
| 2. Koji je cenzus, odnosno koliko procenata glasova lista mora da osvoji da bi dobila poslanička mesta? | 1 | 2 | 1 | 1 |
| 3. Ko raspisuje izbore za Narodnu skupštinu i koliko pre kraja mandata to mora da uradi? | 5 | 2 | 1 | 1 |
| **MRR** | **0.40** | **0.42** | **0.67** | **0.73** |
| Prosečno vreme pretrage | 14 ms | 31 ms | 1173 ms | 1843 ms |

MRR (Mean Reciprocal Rank) je prosek vrednosti 1/rang: 1.00 znači da je tačan član uvek prvi. Vreme je cela pretraga bez pisanja odgovora (medijana od 10 merenja).

## Provera na 14 pitanja

Tri pitanja su premalo za pouzdan zaključak, pa su svi pristupi pušteni i na dodatna pitanja (kraća i kolokvijalnija, vidi `pitanja.py`). Hit@5 je u koliko pitanja je tačan član uopšte pronađen.

| Pristup | Opis | Hit@5 | MRR |
|---|---|---|---|
| **A** | fiksni fragmenti od 600 karaktera (preklapanje 150) + paraphrase-multilingual-MiniLM-L12-v2 + IndexFlatL2 | 7/14 | 0.35 |
| **B** | fragment = jedan član zakona + multilingual-e5-base + HNSW (M=32, efSearch=64) | 10/14 | 0.47 |
| **C** | fragment = jedan član zakona + multilingual-e5-base + HNSW (M=32, efSearch=64) + reranking top 20 | 11/14 | 0.58 |
| **D** | fragment = jedan član zakona + multilingual-e5-base + HNSW (M=32, efSearch=64) + reranking top 20 + prepravka upita preko LLM-a | 12/14 | 0.56 |
| **E** | fragment = jedan član zakona + paraphrase-multilingual-MiniLM-L12-v2 + IndexFlatL2 | 5/14 | 0.25 |
| **G** | fragment = jedan član zakona + multilingual-e5-base + IndexFlatIP (tačna pretraga, kosinusna sličnost) | 10/14 | 0.47 |
| **F** | fragment = jedan član zakona + bge-m3 + IndexFlatIP (tačna pretraga, kosinusna sličnost) | 11/14 | 0.61 |
| **H** | fragment = jedan član zakona + bge-m3 + IndexFlatIP (tačna pretraga, kosinusna sličnost) + reranking top 20 | 12/14 | 0.60 |

## Šta pravi razliku

Svaki red poredi dva pristupa koji se razlikuju u samo jednoj stvari (MRR na svih 14 pitanja).

| Promena | Pre | Posle |
|---|---|---|
| Fragmentacija: fiksna dužina → po članovima (MiniLM) | A: 0.35 | E: 0.25 |
| Model: MiniLM → multilingual-e5-base (po članovima) | E: 0.25 | G: 0.47 |
| Model: multilingual-e5-base → bge-m3 (po članovima, tačna pretraga) | G: 0.47 | F: 0.61 |
| Indeks: tačna pretraga → HNSW (e5-base) | G: 0.47 | B: 0.47 |
| Reranking (e5-base) | B: 0.47 | C: 0.58 |
| Reranking (bge-m3) | F: 0.61 | H: 0.60 |
| Prepravka upita | C: 0.58 | D: 0.56 |

HNSW je u proseku vratio 100% istih fragmenata kao tačna pretraga. Sama pretraga indeksa traje 0.224 ms (tačna) naspram 0.192 ms (HNSW): sa ~1.300 vektora razlika je zanemarljiva, HNSW se isplati tek na mnogo većim bazama.

## Pitanje 1

> Koliko potpisa građana mora da skupi izborna lista da bi mogla da izađe na parlamentarne izbore?

Odgovor je u: **Zakon o izboru narodnih poslanika, član 71**, „najmanje 10.000 pismenih izjava birača“

| Pristup | Mesto tačnog člana | Šta je pronađeno (redom) |
|---|---|---|
| A | – | Zakon o lokalnim izborima 43; Zakon o lokalnim izborima 44; Zakon o finansiranju političkih aktivnosti 17; Zakon o izboru narodnih poslanika 73; Zakon o izboru narodnih poslanika 72 |
| B | 4 | Zakon o lokalnim izborima 43; Zakon o referendumu i narodnoj inicijativi 65; Zakon o izboru narodnih poslanika 65; **Zakon o izboru narodnih poslanika 71**; Zakon o izboru narodnih poslanika 45 |
| C | – | Zakon o lokalnim izborima 43; Zakon o izboru narodnih poslanika 65; Zakon o referendumu i narodnoj inicijativi 58; Zakon o izboru narodnih poslanika 72; Zakon o lokalnim izborima 41 |
| D | 5 | Zakon o lokalnim izborima 43; Zakon o izboru narodnih poslanika 65; Zakon o izboru narodnih poslanika 72; Zakon o izboru narodnih poslanika 139; **Zakon o izboru narodnih poslanika 71** |

Pristup D je pitanje prepravio u: _Koliko potpisa građana mora da skupi izborna lista da bi mogla da izađe na izbore za narodne poslanike?_

<details><summary>Odgovori LLM-a</summary>

**A:**

> Na osnovu priloženih fragmenata ne mogu da pronađem odredbu koja propisuje koliko potpisa građana je potrebno da izabrana lista prikupi da bi se prijavila na parlamentarne (izbore narodnih poslanika). U fragmentima su navedeni:
> 
> * Zakon o lokalnim izborima – članovi 43 i 44 (broj potpisa za lokalne izborne liste);
> * Zakon o izboru narodnih poslanika – članovi 72 i 73 (pitanja objavljivanja potpisa i zastupljenost polova), ali nijedan od njih ne definiše minimalni broj potpisa za parlamentarne izbore.
> 
> Stoga, u dostavljenom tekstu ne postoji relevantna odredba o broju potrebnih potpisa za parlamentarne izbore.

**B:**

> Za parlamentarne izbore (izbor narodnih poslanika) izbornu listu mora da podupiru **najmanje 10 000 pismenih izjava birača**.  
> 
> **Propis:** Zakon o izboru narodnih poslanika, član 71, stav 3 – „najmanje 10.000 pismenih izjava birača da podržavaju izbornu listu…“.

**C:**

> Na osnovu priloženih fragmenata ne može se utvrditi koliko potpisa građana je potrebno da izborna lista prikupi da bi se prijavila na parlamentarne (izbore za narodne poslanike). U fragmentu iz Zakona o izboru narodnih poslanika (član 65) navode se uslovi za formiranje grupe građana koja podnosi izbornu listu, ali se ne navodi konkretan broj potrebnih potpisa birača. Slično tome, Zakon o lokalnim izborima (član 43) reguliše broj potpisa za lokalne izbore, a ne za parlamentarne. Stoga u priloženom tekstu ne postoji odredba o broju potpisa za parlamentarne izbore.

**D:**

> Za izbornu listu koja želi da učestvuje na parlamentarnim (izborima za narodne poslanike) neophodno je da priloži **najmanje 10 000 pismenih izjava birača** koje podržavaju tu listu i koje su overene pre isteka roka za podnošenje izborne liste.
> 
> **Propis:** Zakon o izboru narodnih poslanika, član 71 („Dokumentacija koja se dostavlja uz izbornu listu“), stav 3 – „najmanje 10.000 pismenih izjava birača da podržavaju izbornu listu…“.
> 
> *(Napomena: za izbornu listu nacionalne manjine propis je drugačiji – 5.000 overenih izjava (Zakon o izboru narodnih poslanika, član 139), ali za opštu izbornu listu važi uslov od 10.000 potpisa.)*

</details>

## Pitanje 2

> Koji je cenzus, odnosno koliko procenata glasova lista mora da osvoji da bi dobila poslanička mesta?

Odgovor je u: **Zakon o izboru narodnih poslanika, član 128**, „najmanje 3% glasova od broja birača koji su glasali“

| Pristup | Mesto tačnog člana | Šta je pronađeno (redom) |
|---|---|---|
| A | 1 | **Zakon o izboru narodnih poslanika 128, 129**; Poslovnik Narodne skupštine 127; Zakon o izboru narodnih poslanika 112; Zakon o lokalnim izborima 52; Zakon o lokalnim izborima 52 |
| B | 2 | Zakon o lokalnim izborima 61; **Zakon o izboru narodnih poslanika 128**; Zakon o lokalnim izborima 62; Zakon o lokalnim izborima 78; Zakon o izboru narodnih poslanika 5 |
| C | 1 | **Zakon o izboru narodnih poslanika 128**; Zakon o lokalnim izborima 61; Zakon o izboru narodnih poslanika 73; Zakon o lokalnim izborima 41; Zakon o izboru narodnih poslanika 129 |
| D | 1 | **Zakon o izboru narodnih poslanika 128**; Zakon o izboru narodnih poslanika 140; Zakon o izboru narodnih poslanika 73; Zakon o izboru narodnih poslanika 129; Zakon o izboru narodnih poslanika 45 |

Pristup D je pitanje prepravio u: _Koji je cenzus, odnosno koliko procenata glasova lista mora da osvoji da bi dobila mesta za narodne poslanike?_

<details><summary>Odgovori LLM-a</summary>

**A:**

> Prema **Zakon o izboru narodnih poslanika**, član **128**, u raspodeli mandata mogu učestvovati samo izborne liste koje su dobile **najmanje 3 % glasova od broja birača koji su glasali**. (Ukoliko nijedna lista ne dostigne taj prag, tada sve liste koje su dobile glasove učestvuju u raspodeli.)  
> 
> **Propis:** Zakon o izboru narodnih poslanika, čl. 128.

**B:**

> Cenzus iznosi **najmanje 3 % glasova od broja birača koji su glasali**.  
> 
> - **Zakon o izboru narodnih poslanika, član 128** (Izborni cenzus):  
>   „U raspodeli mandata mogu učestvovati samo izborne liste koje su dobile najmanje 3 % glasova od broja birača koji su glasali. Ako nijedna izborna lista nije dobila 3 % glasova od broja birača koji su glasali, onda sve izborne liste koje su dobile glasove mogu učestvovati u raspodeli mandata.“  
> 
> Dakle, da bi izbornu listu kvalifikovala za dodelu poslanickih mesta, mora da osvoji najmanje 3 % od ukupnog broja glasova izdatih od strane svih glasača. (U slučaju da nijedna lista ne dostigne taj prag, sve liste koje su dobile glasove učestvuju u raspodeli.)

**C:**

> Prema **Zakon o izboru narodnih poslanika**, član 128 (Izborni cenzus), i **Zakon o lokalnim izborima**, član 61 (Izborni cenzus), u raspodeli mandata mogu učestvovati samo izborne liste koje su dobile **najmanje 3 % glasova od broja birača koji su glasali**.  
> 
> - Ako nijedna lista ne postigne taj prag, tada sve izborne liste koje su dobile glasove mogu učestvovati u raspodeli mandata (isto je predviđeno u oba pomenuta člana).  
> 
> Dakle, cenzus iznosi **3 %** od ukupnog broja odabranih glasova.  
> 
> **Reference:**  
> - Zakon o izboru narodnih poslanika, član 128.  
> - Zakon o lokalnim izborima, član 61.

**D:**

> Prema Zakon o izboru narodnih poslanika:
> 
> - **Opšti cenzus** – da bi izbornа lista mogla učestvovati u raspodeli mandata, mora da dobije najmanje **3 % glasova od broja birača koji su glasali**. (Zakon o izboru narodnih poslanika, čl. 128)
> 
> - **Izuzetak** – izborne liste nacionalnih manjina mogu učestvovati i kada dobiju **manje od 3 % glasova**, a pri raspodeli mandata njihov se količnik uvećava za 35 % (član 140).  
> 
> - **Posebna situacija** – ako **nijedna lista ne dostigne 3 %**, tada **sve liste koje su dobile glasove** učestvuju u raspodeli mandata. (član 128, stav 2)
> 
> Dakle, u standardnim uslovima cenzus iznosi **3 %** glasova od ukupnog broja glasača koji su glasali; manjinske liste imaju poseban režim koji im omogućava da osvoje mandata i sa manjim udelom glasova.

</details>

## Pitanje 3

> Ko raspisuje izbore za Narodnu skupštinu i koliko pre kraja mandata to mora da uradi?

Odgovor je u: **Ustav Republike Srbije, član 101**, „raspisuje predsednik Republike, 90 dana pre isteka mandata“

| Pristup | Mesto tačnog člana | Šta je pronađeno (redom) |
|---|---|---|
| A | 5 | Zakon o izboru narodnih poslanika 179; Poslovnik Narodne skupštine 265; Zakon o izboru narodnih poslanika 179; Zakon o jedinstvenom biračkom spisku 24; **Ustav Republike Srbije 101** |
| B | 2 | Zakon o izboru narodnih poslanika 60; **Ustav Republike Srbije 101**; Poslovnik Narodne skupštine 87; Zakon o izboru narodnih poslanika 179; Zakon o izboru narodnih poslanika 22 |
| C | 1 | **Ustav Republike Srbije 101**; Zakon o izboru narodnih poslanika 60; Ustav Republike Srbije 109; Zakon o lokalnim izborima 35; Zakon o izboru narodnih poslanika 179 |
| D | 1 | **Ustav Republike Srbije 101**; Zakon o izboru narodnih poslanika 60; Ustav Republike Srbije 109; Zakon o lokalnim izborima 35; Zakon o izboru narodnih poslanika 179 |

<details><summary>Odgovori LLM-a</summary>

**A:**

> Prema Ustavu Republike Srbije, član 101, izbore za narodne poslanike (tj. za Narodnu skupštinu) raspisuje **predsednik Republike**, i to **90 dana pre isteka mandata Narodne skupštine**.  
> 
> *Propis:* Ustav Republike Srbije, član 101.

**B:**

> **Ko raspisuje izbore za Narodnu skupštinu?**  
> Izborе za narodne посланике (тј. за Народну скупштину) расписује **председник Републике**.
> 
> **Колико раније од краја мандата то мора да уради?**  
> Одлука о расписивању избора доноси се **90 дана пре истека мандата** (тј. 90 дана пре него што истеку четири године од дана конституисања Народне скупштине).
> 
> **Приводим одредбе на које се ослањам:**  
> - Устав Републике Србије, члан 101: „Изборе за народне посланике расписује председник Републике, **90 дана пред истека мандата** Народне скупштине…“  
> - Закон о избору народних посланика, члан 60: „Оdluka о расписивању избора доноси се **90 дана пре него што истеку** четири године од дана када је конституисана Народна скупштина.“  
> 
> Дакле, изборе расписује председник Републике, а то мора да уради најкасније 90 дана пре истека мандата Народне скупштине.

**C:**

> **Ko raspisuje izbore za Narodnu skupštinu?**  
> Izbore za narodne poslanike raspisuje **predsednik Republike**.
> 
> **Koliko pre kraja mandata to mora da uradi?**  
> Prema Ustavu Republike Srbije, član 101, predsednik Republike je dužan da izbore raspisuje **90 dana pre isteka mandata Narodne skupštine**.  
> 
> *Reference:* Ustav Republike Srbije, član 101 – „Izbore za narodne poslanike raspisuje predsednik Republike, 90 dana pre isteka mandata Narodne skupštine.“ (takođe potvrđeno i članom 109, koji navodi da predsednik raspisuje izbore istovremeno sa raspuštanjem Skupštine).

**D:**

> **Ko raspisuje izbore za Narodnu skupštinu?**  
> Izbore za narodne poslanike raspisuje **predsednik Republike**.
> 
> **Koliko pre kraja mandata to mora da uradi?**  
> Prema Ustavu Republike Srbije, član 101, predsednik Republike je dužan da izbore raspisuje **90 dana pre isteka mandata Narodne skupštine**.  
> 
> *Reference:* Ustav Republike Srbije, član 101 – „Izbore za narodne poslanike raspisuje predsednik Republike, 90 dana pre isteka mandata Narodne skupštine.“ (takođe potvrđeno i članom 109, koji predviđa da predsednik raspisuje izbore istovremeno sa raspuštanjem Skupštine).

</details>

## Dodatna pitanja, mesto tačnog člana

| Pitanje | Tačan član | A | B | C | D | E | G | F | H |
|---|---|---|---|---|---|---|---|---|---|
| Koliko ima poslanika u skupštini? | Ustav Republike Srbije 100 | – | 3 | 1 | 2 | – | 3 | 2 | 1 |
| Koliko dugo traje mandat poslanika? | Ustav Republike Srbije 102 | 5 | 1 | 1 | 1 | – | 1 | 1 | 1 |
| Na koliko godina se bira predsednik države? | Ustav Republike Srbije 116 | – | – | 2 | 2 | 5 | – | 3 | 2 |
| Može li ista osoba tri puta da bude predsednik? | Ustav Republike Srbije 116 | 2 | – | 2 | 1 | – | – | 2 | 2 |
| Kako se smenjuje predsednik Republike? | Ustav Republike Srbije 118 | – | – | – | – | – | – | – | 4 |
| Može li poslanik da bude krivično gonjen? | Ustav Republike Srbije 103 | – | 1 | 3 | 2 | 1 | 1 | 1 | 3 |
| Koliko građana treba da bi sami predložili zakon? | Ustav Republike Srbije 107 | 1 | 2 | 2 | 2 | 4 | 2 | 1 | 2 |
| Koliko ljudi je potrebno da se osnuje stranka? | Zakon o političkim strankama 8 | 1 | 1 | 1 | 2 | – | 1 | 1 | 1 |
| Koliko osnivača treba stranci nacionalne manjine? | Zakon o političkim strankama 9 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Od kada počinje izborna tišina? | Zakon o izboru narodnih poslanika 6 | – | – | – | – | – | – | – | – |
| Koliko birača može da traži referendum o pitanju iz nadležnosti skupštine? | Zakon o referendumu i narodnoj inicijativi 46 | – | 2 | 4 | 5 | – | 2 | 4 | 4 |
