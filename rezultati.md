# Poređenje RAG pristupa: propisi o Narodnoj skupštini i izborima

Baza znanja: Ustav i 10 zakona/poslovnika o skupštini, izborima i političkom sistemu (paragraf.rs). Pristup A ima 1756 fragmenata, pristupi B, C i D 1310. Odgovore piše `openai/gpt-oss-120b` preko Groq-a, a LLM dobija top 5 fragmenata. Pokrenuto 19.11.2026.

## Pristupi

- **A**: fiksni fragmenti od 600 karaktera (preklapanje 150) + paraphrase-multilingual-MiniLM-L12-v2 + IndexFlatL2
- **B**: fragment = jedan član zakona + multilingual-e5-base + HNSW (M=32, efSearch=64)
- **C**: fragment = jedan član zakona + multilingual-e5-base + HNSW (M=32, efSearch=64) + reranking top 20
- **D**: fragment = jedan član zakona + multilingual-e5-base + HNSW (M=32, efSearch=64) + reranking top 20 + prepravka upita preko LLM-a

## Ukratko

Broj u tabeli je mesto na kom se našao tačan član (od 5), a crtica znači da ga nema.

| Pitanje | A | B | C | D |
|---|---|---|---|---|
| 1. Koliko potpisa građana mora da skupi izborna lista da bi mogla da izađe na parlamentarne izbore? | – | 4 | – | 5 |
| 2. Koji je cenzus, odnosno koliko procenata glasova lista mora da osvoji da bi dobila poslanička mesta? | 1 | 1 | 1 | 1 |
| 3. Ko raspisuje izbore za Narodnu skupštinu i koliko pre kraja mandata to mora da uradi? | 5 | 2 | 1 | 1 |
| **MRR** | **0.40** | **0.58** | **0.67** | **0.73** |
| Prosečno vreme pretrage | 14 ms | 32 ms | 1226 ms | 2083 ms |

Najprecizniji je pristup **D** (MRR 0.73), a najbrži **A** (14 ms). MRR je prosek vrednosti 1/rang, pa je 1.00 savršen rezultat (tačan član uvek na prvom mestu). Vreme ne uključuje pisanje odgovora, to je medijana od 20 merenja.

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

> Na osnovu priloženih fragmenata ne može se utvrditi koliko potpisa građana je potrebno da izborna lista prikupi da bi se prijavila na parlamentarne (izbore narodnih poslanika). U fragmentima Zakon o lokalnim izborima (čl. 43 i čl. 44) navode se uslovi za lokalne izbore, a u fragmentima Zakona o izboru narodnih poslanika (čl. 72 i čl. 73) su regulisani drugi aspekti (objava overenih izjava i zastupljenost polova), ali ne i minimalni broj potpisa za parlamentarne izbore. Dakle, taj podatak nije pronađen u priloženom tekstu.

**B:**

> Za parlamentarne izbore (izbori za narodne poslanike) izabrana lista mora da priloži **najmanje 10 000 pismenih izjava birača** koji podržavaju tu listu.  
> 
> **Propis:** Zakon o izboru narodnih poslanika, član 71, stav 3 – „najmanje 10.000 pismenih izjava birača da podržavaju izbornu listu na obrascu koji propisuje Republička izborna komisija…“.  
> 
> Dakle, da bi izbornu listu mogla da podnese Republičkoj izbornoj komisiji i učestvuje na parlamentarnim izborima, mora da prikupi najmanje deset hiljada potpisanih izjava birača.

**C:**

> Na osnovu priloženih fragmenata ne može se utvrditi koliko potpisa građana je potrebno da izborna lista prikupi da bi se prijavila na parlamentarne (izbore za narodne poslanike). U fragmentu iz Zakona o izboru narodnih poslanika (član 65) navode se uslovi za formiranje grupe građana koja podnosi izbornu listu, ali se ne navodi konkretan broj potrebnih potpisa birača. Slično tome, Zakon o lokalnim izborima (član 43) reguliše broj potpisa za lokalne izbore, a ne za parlamentarne. Stoga u priloženom tekstu ne postoji odredba o broju potpisa za parlamentarne izbore.

**D:**

> Za izbornu listu koja želi da učestvuje na parlamentarnim (izborima za narodne poslanike) neophodno je da priloži **najmanje 10 000 pismenih izjava birača** koje podržavaju tu listu i koje su overene pre isteka roka za podnošenje izborne liste.
> 
> **Osnova:** Zakon o izboru narodnih poslanika, član 71, stav 3 – „najmanje 10.000 pismenih izjava birača da podržavaju izbornu listu na obrascu koji propisuje Republička izborna komisija …“.
> 
> *(Napomena: za izbornu listu nacionalne manjine propis je drugačiji – 5 000 overenih izjava (član 139), ali za opštu listu važi uslov od 10 000 potpisa.)*

</details>

## Pitanje 2

> Koji je cenzus, odnosno koliko procenata glasova lista mora da osvoji da bi dobila poslanička mesta?

Odgovor je u: **Zakon o izboru narodnih poslanika, član 128**, „najmanje 3% glasova od broja birača koji su glasali“

| Pristup | Mesto tačnog člana | Šta je pronađeno (redom) |
|---|---|---|
| A | 1 | **Zakon o izboru narodnih poslanika 128, 129**; Poslovnik Narodne skupštine 127; Zakon o izboru narodnih poslanika 112; Zakon o lokalnim izborima 52; Zakon o lokalnim izborima 52 |
| B | 1 | **Zakon o lokalnim izborima 61**; **Zakon o izboru narodnih poslanika 128**; Zakon o lokalnim izborima 62; Zakon o lokalnim izborima 78; Zakon o izboru narodnih poslanika 5 |
| C | 1 | **Zakon o izboru narodnih poslanika 128**; **Zakon o lokalnim izborima 61**; Zakon o izboru narodnih poslanika 73; Zakon o lokalnim izborima 41; Zakon o izboru narodnih poslanika 129 |
| D | 1 | **Zakon o izboru narodnih poslanika 128**; Zakon o izboru narodnih poslanika 140; Zakon o izboru narodnih poslanika 73; Zakon o izboru narodnih poslanika 129; Zakon o izboru narodnih poslanika 45 |

Pristup D je pitanje prepravio u: _Koji je cenzus, odnosno koliko procenata glasova lista mora da osvoji da bi dobila mesta za narodne poslanike?_

<details><summary>Odgovori LLM-a</summary>

**A:**

> Prema **Zakon o izboru narodnih poslanika**, član **128**, u raspodeli mandata mogu učestvovati samo izborne liste koje su dobile **najmanje 3 % glasova od broja birača koji su glasali**. (Ukoliko nijedna lista ne dostigne taj prag, tada sve liste koje su dobile glasove učestvuju u raspodeli.)  
> 
> Dakle, cenzus iznosi **3 %** od ukupnog broja glasova izabranih birača.

**B:**

> Prema **Zakon o izboru narodnih poslanika**, član 128 (Izborni cenzus):
> 
> - „U raspodeli mandata mogu učestvovati samo izborne liste koje su dobile najmanje **3 %** glasova od broja birača koji su glasali.“  
> - „Ako nijedna izborna lista nije dobila 3 % glasova od broja birača koji su glasali, onda sve izborne liste koje su dobile glasove mogu učestvovati u raspodeli mandata.“
> 
> Dakle, da bi izbornu listu kvalifikovala za dodelu poslaničkih mesta, mora da osvoji najmanje **3 %** od ukupnog broja glasova izdatih od strane birača koji su glasali (uz izuzetak da, ako nijedna lista ne pređe taj prag, u raspodeli učestvuju sve liste koje su dobile bar jedan glas).

**C:**

> Cenzus iznosi **najmanje 3 % glasova od broja birača koji su glasali**.  
> 
> - **Zakon o izboru narodnih poslanika**, član 128: „U raspodeli mandata mogu učestvovati samo izborne liste koje su dobile najmanje 3 % glasova od broja birača koji su glasali. Ako nijedna izborna lista nije dobila 3 % glasova od broja birača koji su glasali, onda sve izborne liste koje su dobile glasove mogu učestvovati u raspodeli mandata.“  
> 
> - **Zakon o lokalnim izborima**, član 61 (isto pravilo za lokalne izbore).  
> 
> Dakle, da bi lista mogla da učestvuje u raspodeli poslaničkih mesta, mora da ostvari najmanje 3 % od ukupnog broja glasova koji su odani od strane glasača. Ako nijedna lista ne pređe taj prag, tada se u raspodeli mandata uzimaju sve liste koje su dobile bilo koji broj glasova.

**D:**

> Prema Zakon o izboru narodnih poslanika, član 128, da bi izborna lista mogla učestvovati u raspodeli mandata (i tako potencijalno osvojila poslanička mesta), mora da dobije najmanje 3 % glasova od broja birača koji su glasali.  
> 
> Ukoliko **nijedna** lista ne postigne taj prag, tada sve liste koje su dobile bilo koje glasove mogu učestvovati u raspodeli mandata (isto iz čl. 128).  
> 
> Za izborne liste nacionalnih manjina važi poseban režim: po članu 140, one učestvuju u raspodeli mandata i kada dobiju **manje od 3 %** glasova, a pri tome im se količnici u sistemu najvećeg količnika uvećavaju za 35 %.  
> 
> **Dakle:**  
> - Opšti cenzus = **3 %** glasova od birača koji su glasali (član 128).  
> - Izuzetak – liste nacionalnih manjina mogu osvojiti mandata i sa manjim udelom glasova zahvaljujući pojačanju količnika (član 140).

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

> Prema Ustavu Republike Srbije, član 101, izbore za narodne poslanike (tj. za Narodnu skupštinu) raspisuje **predsednik Republike**, i to **90 dana pre isteka mandata Narodne skupštine**. [Ustav RS, čl. 101]

**B:**

> **Ko raspisuje izbore:**  
> Izbore za narodne poslanike (t.j. za Narodnu skupštinu) raspisuje **predsednik Republike**.
> 
> **Koliko pre kraja mandata to mora da uradi:**  
> Raspisivanje izbora mora da se izvrši **90 dana pre isteka mandata Narodne skupštine** (tj. 90 dana pre nego što isteknu četiri godine od dana konstituisanja Skupštine).  
> 
> **Propisi na koje se oslanjam:**  
> - Ustav Republike Srbije, član 101 – „Izbore za narodne poslanike raspisuje predsednik Republike, 90 dana pre isteka mandata Narodne skupštine…“  
> - Zakon o izboru narodnih poslanika, član 60 – „Odluka o raspisivanju izbora donosi se 90 dana pre nego što isteknu četiri godine od dana kada je konstituisana Narodna skupština.“

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
> *Reference:* Ustav Republike Srbije, član 101 – „Izbore za narodne poslanike raspisuje predsednik Republike, 90 dana pre isteka mandata Narodne skupštine.“ (takođe se to potvrđuje i članom 109, koji navodi da predsednik, istovremeno sa raspuštanjem Skupštine, raspisuje izbore).

</details>

