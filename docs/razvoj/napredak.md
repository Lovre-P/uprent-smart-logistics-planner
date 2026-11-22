# Napredak implementacije

| Datum | Zadatak | Stanje | Testovi aplikacije | Commit |
|---|---|---|---:|---|
| 22. 11. 2026. | Prije zadatka 1 | Zaustavljeno pri početnoj provjeri specifikacije. Izostavljanje naloga prema §11 može onemogućiti valjan potpuni plan. | 0 pokrenutih | — |
| 22. 11. 2026. | 1 | Domenski modeli, provjera ulaza i zeleni GitHub Actions. | 36 | `8b842bf` |
| 22. 11. 2026. | 2 | Matrični izračun udaljenosti, zaokruživanje i točno vrijeme vožnje. | 40 | `a97a975` |
| 22. 11. 2026. | 3 | Neovisni validator. Nakon pregleda ispravljen je prikaz malih razlika vremena i udaljenosti. | 62 Python + 17 web | `bd8b276` |
| 22. 11. 2026. | 12 | Sučelje, JSON klijent, hrvatsko formatiranje i pristupačne upute. | 62 Python + 17 web | `be63287` |
| 22. 11. 2026. | 4 | Predprovjera v4.2. Regresijski primjer potvrđuje granicu od 11,2 km. | 69 Python + 17 web | `9743ea3` |
| 22. 11. 2026. | 5 | 65.562 stanja. Neovisno provjereno svih 1.056 ruta i kilometraža. | 80 Python + 17 web | `9aa29ff` |
| 22. 11. 2026. | 13 | Postavke, uređivanje i uvoz podataka. Neispravna izmjena čuva zadnji valjani scenarij. | 80 Python + 26 web | `6aaedbb` |
| 22. 11. 2026. | 6 | Kombiniranje ruta i tri prolaza za najraniji završetak. Neovisna provjera potvrdila je 192 usporedbe. | 113 Python + 26 web | `939c818` |
| 22. 11. 2026. | 7 | OR-Tools 9.15. Provjerene su obje vremenske dimenzije, prikvačivanja i statusi nakon predprovjere. | 144 Python + 32 web | `99dcb2e` |
| 22. 11. 2026. | 8 | Servis razlikuje dokazani ishod i istek heurističke pretrage. Regresijski primjer vraća OPTIMAL, 2/2 i 11,3 km. | 166 Python + 32 web | `6b7dd04` |
| 22. 11. 2026. | 9 | Analiza pinova, granica i 14 nedominiranih raspodjela. Provjera na 72 konfiguracije. | 189 Python + 32 web | `53716b1` |
| 22. 11. 2026. | 10 | CLI i šest unaprijed zadanih usporedbi. Provjeren je UTF-8 JSON kroz stvarnu naredbu. | 212 Python + 32 web | `7cd265b` |
| 22. 11. 2026. | 11 | FastAPI, validacija ulaza, usporedba i posluživanje aplikacije. | 223 Python + 32 web | `ef68fdc` |
| 22. 11. 2026. | 14 | Plan po kamionu, neovisne provjere i usporedba solvera uz odbacivanje zastarjelih odgovora. | 223 Python + 46 web | `90d717d` |
| 22. 11. 2026. | 15 | Karta s 10 lokacija, vremenska crta, 14 raspodjela i svih šest kartica na 390 i 1280 px. | 223 Python + 66 web | `af278a3` |
| 22. 11. 2026. | 16 | Produkcijska izgradnja u Gitu, šest testova s pravim API-jem te zeleni Python i web CI. | 223 Python + 66 web + 6 E2E | `b3597ae` |
| 22. 11. 2026. | 17 | Upute provjerene pokretanjem svih navedenih naredbi, uključujući portove 8000 i 8010. Priložena je snimka iz stvarne aplikacije. | 223 Python + 67 web + 6 E2E | `4c3a2ef` |
| 22. 11. 2026. | 18 | Cloudflare Containers objavljen i provjeren u ugrađenom pregledniku. Aktivna aplikacija ima ograničenje od jedne instance. | 223 Python + 67 web + 6 E2E | `b8412b9` |

Naknadni pregled zadatka 13 otkrio je da je uređivač prihvaćao nevaljano trajanje na nalogu, pogrešan tip postavke u JSON-u i zadržavao nacrt nakon vraćanja zadanih vrijednosti. Ispravci su u commitu `38cbb0d`, uz 113 prolaznih Python testova i 32 testa sučelja.

Vlasnik je 22. 11. odobrio specifikaciju v4.2. Predprovjera koristi donju granicu od 11,2 km za N01 u regresijskom primjeru, a potpuni plan ima 11,3 km. [Odluka i primjer](odstupanja.md).

Završna provjera potvrdila je 223 Python testa, 67 testova sučelja i šest E2E testova. Nakon pregleda stvarne karte dodan je test čitljivosti oznake L7 i ispravak u commitu `40f7969`. Oba prolaza usporedbe s referentnim solverom na istih 30 scenarija završila su bez grešaka.

Javni demo provjeren je 22. 11. 2026. Ugrađeni preglednik prikazao je odgovor `{"status":"ok"}` i zadani plan od 182,2 km s oznakom „Dokazano optimalno”. Cloudflare je potvrdio aktivnu aplikaciju, 1 GiB memorije i najviše jednu instancu. [Otvori planer](https://uprent-smart-logistics-planner.lovre-petrina2.workers.dev/)
