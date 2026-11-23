# QA izvještaj

Snimke zaslona i izlazi provjera nalaze se u lokalnoj mapi `qa/out/`, koja nije u repozitoriju.

22.–23. studenoga 2026. (Europe/Zagreb) · Codex · Windows, uv 0.11.25, Python 3.11.9, Node v24.13.1. Prvi prolaz `2955b9d`. Provjerena završna revizija `a68165c`.

## Sažetak

Prvi prolaz (120 provjera) · PASS **116** · FAIL **3** · BLOCKED **1**.

Ponovljeni prolaz (120 provjera) · PASS **117** · FAIL **2** · BLOCKED **1**.

Prvi izvještaj pohranjen je u commitu `0abe52e`. Cijeli drugi prolaz izvršen je u novom klonu `../uprent-qa2` preuzetom s privatnog GitHuba nakon ispravka. Za QA-12.1 u klon je lokalno kopiran ignorirani izvornik. Prije QA-13 javni demo ponovno je objavljen iz glavne mape projekta.

**Konačna ocjena: NIJE SPREMNO za cjelovitu predaju.** Referentna kilometraža i javni demo potvrđeni su. Kandidat treba upisati stvarnu procjenu sati. Tablica u nastavku razlikuje tu stavku predaje od tehničkih rezultata.

## Rezultati

Kontrolne točke izvršene su po skupinama QA-0–QA-14. Naredbe, ulazi, koraci i mjerodavna očekivanja po istim ID-ovima navedeni su u [QA planu](qa-plan.md). Za mjerenja vremena korišten je monotoni sat, a javni hladni start uključuje i otvaranje kartice. Izlazi su u lokalnim mapama `qa/out/p1`, `qa/out/p2` i `qa/out/screens`. Klikovi, unos, prelazak mišem, tipkovnica, konzola i mreža provjereni su u Codexovu ugrađenom pregledniku.

| QA ID | Prvi prolaz | Ponovljeno | Dokaz ponovljenog prolaza |
|---|---|---|---|
| 0.1 | PASS | PASS | `uv 0.11.25`; `uv run python --version` → Python 3.11.9. |
| 0.2 | PASS | PASS | `node --version` → v24.13.1. |
| 0.3 | PASS | PASS | Čisti klon privatnog GitHuba u ../uprent-qa2, HEAD a68165c, bez web/node_modules. Iz tog je klona poslužen novi index-DUrFn9Lm.js. |
| 1.1 | PASS | PASS | U čistom klonu `uv sync` izradio je .venv i instalirao 34 paketa. |
| 1.2 | PASS | PASS | `uv run uprent serve --port 8000` i GET /api/health → 200, `{"status":"ok"}`. |
| 1.3 | PASS | PASS | Bez npm-a, automatski 182,2 km. [1.3](../../qa/out/screens/p2-1.3.jpg) |
| 1.4 | PASS | PASS | `git ls-files web/dist` → index.html, JavaScript i CSS. |
| 2.1 | PASS | PASS | 223 passed, 4 warnings in 53.29s |
| 2.2 | PASS | PASS | Tests  67 passed |
| 2.3 | PASS | PASS | 6 passed (27.3s) |
| 2.4 | PASS | PASS | Pokriveno svih 16 traženih skupina. Datoteke i nazivi testova navedeni su ispod tablice. |
| 3.1 | PASS | PASS | OPTIMAL, 10/10, 182.2 km, A = []. |
| 3.2 | PASS | PASS | OPTIMAL, 10/10, 200.1 km, A = ['N03']. |
| 3.3 | PASS | PASS | OPTIMAL, 10/10, 200.1 km, A = ['N03']. |
| 3.4 | PASS | PASS | OPTIMAL, 10/10, 217.0 km, A = ['N01', 'N04']. |
| 3.5 | PASS | PASS | OPTIMAL, 10/10, 182.2 km, A = []. |
| 3.6 | PASS | PASS | OPTIMAL, 10/10, 182.2 km, A = []. |
| 3.7 | PASS | PASS | OPTIMAL, 10/10, 239.2 km, A = ['N03', 'N05']. |
| 3.8 | PASS | PASS | OPTIMAL_PARTIAL, 8/10, 203.8 km, A = ['N03', 'N02', 'N01', 'N04']. [('N08', 'DOES_NOT_FIT_TOGETHER'), ('N09', 'DOES_NOT_FIT_TOGETHER')] |
| 3.9 | PASS | PASS | NO_FULL_PLAN, 0/10, 0.0 km, A = []. |
| 3.10 | PASS | PASS | OPTIMAL, 10/10, 284.2 km, A = ['N03', 'N05', 'N02', 'N01', 'N04']. |
| 3.11 | PASS | PASS | FEASIBLE, 10/10, 182.2 km, A = []. Validator = True. |
| 3.12 | PASS | PASS | OPTIMAL_PARTIAL, 10/11, 182.2 km, A = []. [('N11', 'TOO_HEAVY')] |
| 3.13 | PASS | PASS | FEASIBLE, 13/13, 189.3 km, A = []. ortools, best_found, messages = []. |
| 3.14 | PASS | PASS | FEASIBLE, 10/10, 284.2 km, A = ['N03', 'N05', 'N02', 'N01', 'N04']. Najdulji dan 344.8 min. |
| 3.15 | PASS | PASS | OPTIMAL, 10/10, 217.0 km, A = ['N01', 'N04']. |
| 4.1 | PASS | PASS | Referenca 10/10, 182.2 km. |
| 4.2 | PASS | PASS | Referenca 10/10, 200.1 km. |
| 4.3 | PASS | PASS | Ukupno: 30 scenarija, 0 s greškom. Najveća razlika OR-Toolsa pri istom broju naloga 0.00 % (seed 1029). |
| 4.4 | PASS | PASS | rg nad src/ vratio 1, bez pogodaka. |
| 5.1 | PASS | PASS | passed=True.   |
| 5.2 | PASS | PASS | passed=False. vrijeme B: 582,2 min prelazi limit od 540 min. |
| 5.3 | PASS | PASS | passed=False. kapacitet_kg B: 13.300 / 10.000 kg. |
| 5.4 | PASS | PASS | passed=False. mjesta B: 4 / 3 mjesta. |
| 5.5 | PASS | PASS | passed=False. baza, redoslijed A: istovar M03 za N03 prije utovara u taj kamion. |
| 5.6 | PASS | PASS | passed=False. baza, redoslijed, isti_kamion N03: radnje su raspoređene na A, B. · A: pri povratku u bazu ostaju M03. |
| 5.7 | PASS | PASS | passed=False. km_dosljedno A: prijavljeno 26,4 km, prijeđeno 37,2 km. |
| 5.8 | PASS | PASS | passed=False. vrijeme B: 540,4 min prelazi limit od 540 min. |
| 5.9 | PASS | PASS | passed=True. svi_kamioni Nekorišteni kamioni: A. |
| 6.1 | PASS | PASS | GET 200, 10 naloga, limit 540, radnje 20/20, auto, km, djelomični plan i usporedba uključeni, 07:00. Potpuni ispis u `6.txt`. |
| 6.2 | PASS | PASS | POST 200, svih devet obveznih ključeva. A ima 0 koraka, B ima 21, zadnji je RETURN u L0. |
| 6.3 | PASS | PASS | 422, `body.scenario: orders.N01.pickup: nepoznata lokacija L99.` |
| 6.4 | PASS | PASS | HTTP 200, šest redaka s 182.2, 200.1, 200.1, 182.2, 284.2, 209.0 km. |
| 6.5 | PASS | PASS | GET /docs → 200, Swagger UI prikazuje OAS 3.1 i pet API operacija. [6.5](../../qa/out/screens/p2-6.5.jpg) |
| 6.6 | PASS | PASS | Dvije alternative po 200,1 km, A vozi N03 u obje. |
| 7.1 | PASS | PASS | Prvi koraci, 182,2 km, Dokazano optimalno, A nije korišten, B 9 h 42 min, drugo tumačenje 200,1 km. [7.1](../../qa/out/screens/p2-7.1.jpg) |
| 7.2 | PASS | PASS | Primijeni → 200,1 km, N03 na A, prekidač uključen. [7.2](../../qa/out/screens/p2-7.2.jpg) |
| 7.3 | PASS | PASS | Povratak na početno pravilo i uključivanje svih kamiona → 200,1 km. [7.3](../../qa/out/screens/p2-7.3.jpg) |
| 7.4 | FAIL | PASS | Ciljana provjera na javnom demou 23. 11. 2026. (`3408d82`). Uključen utovar i istovar u limit, oba trajanja 21 min. Plan prikazuje **217,0 km** i 10/10 naloga. Ispravljeno u `89dfb7c` nakon drugog prolaza (FAIL). [Snimka 7.4](../../qa/out/screens/np08-7.4.jpg) |
| 7.5 | PASS | PASS | Limit 300 min uz 20/20 → 8/10, N08 i N09 imaju zasebna upozorenja „Dokazano”. [7.5](../../qa/out/screens/p2-7.5.jpg) |
| 7.6 | PASS | PASS | M11 od 12.000 kg i N11 L1→L3 → 10/11, objašnjenje s najvećom nosivošću 10.000 kg. [7.6](../../qa/out/screens/p2-7.6.jpg) |
| 7.7 | PASS | PASS | Uređivanje N01 → „N01: nepoznata lokacija L99.” Prethodni plan ostao je 10/11. [7.7](../../qa/out/screens/p2-7.7.jpg) [7.7-plan](../../qa/out/screens/p2-7.7-plan.jpg) |
| 7.8 | PASS | PASS | L0–L9, ruta u boji B, stvarni prelazak mišem na korak 5 → Istovar N09, L1, 09:17. [7.8](../../qa/out/screens/p2-7.8.jpg) |
| 7.9 | PASS | PASS | Trake razlikuju vožnju, utovar i istovar, limit ima oznaku „samo vožnja” uz 3 h 02 min od 9 h. [7.9](../../qa/out/screens/p2-7.9.jpg) |
| 7.10 | PASS | PASS | 14 točaka, N03 +17,9 km. Klik pokazivačem na krajnju točku → 284,2 km. Ponovljeno i jednim običnim klikom bez snimanja cijele stranice neposredno prije klika. [7.10](../../qa/out/screens/p2-7.10.jpg) [7.10-krivulja](../../qa/out/screens/p2-7.10-krivulja.jpg) |
| 7.11 | PASS | PASS | Deset oznaka Prolazi uz kvačice; redci Egzaktni i OR-Tools. [7.11](../../qa/out/screens/p2-7.11.jpg) |
| 7.12 | PASS | PASS | Pomoć → Vrati podatke i postavke iz zadatka → 182,2 km. [7.12](../../qa/out/screens/p2-7.12.jpg) |
| 7.13 | PASS | PASS | 390 CSS px, dokument 375 px. Mobilne postavke otvaraju se i zatvaraju, tablica ima vlastito pomicanje (687 px unutar 349 px). [7.13](../../qa/out/screens/p2-7.13.jpg) [7.13-tablica](../../qa/out/screens/p2-7.13-tablica.jpg) |
| 7.14 | PASS | PASS | Konzola lokalne kartice za pogreške i upozorenja: []. [Izlaz](../../qa/out/p2/7.14.txt). [7.14](../../qa/out/screens/p2-7.14.jpg) |
| 7.15 | PASS | PASS | Mreža za QA-7: 34 solve zahtjeva uključujući usporedbe, 11 prekinutih. Neočekivani HTTP 4xx/5xx: []. L99 je zaustavljen uz polje prije slanja. [Mrežni događaji](../../qa/out/screens/p2-network.json). [7.15](../../qa/out/screens/p2-7.15.jpg) |
| 7.16 | PASS | PASS | Pet klikova u 1,474 s. Promatrač promjena prikazane brojke zabilježio je samo 182,2 → 200,1 km. [Vremena i promjene](../../qa/out/p2/7.16.txt). [7.16](../../qa/out/screens/p2-7.16.jpg) |
| 8.1 | PASS | PASS | Ciljana provjera na javnom demou 23. 11. 2026. Otvoreno svih 13 osnovnih i naprednih uputa te dodatna uputa za prikvačene naloge. Uputa uz limit navodi 182,2 i 200,1 km. U obrascu „Uredi A” uz „Brzina (km/h)” otvorena je uputa o prosječnih 60 km/h za oba kamiona i utjecaju brzine na trajanje vožnje. NP-08 ispravljen u `3408d82` nakon drugog prolaza (FAIL). [Tumačenje limita](../../qa/out/screens/np08-8.1-limit.jpg) · [Brzina kamiona](../../qa/out/screens/np08-8.1-brzina.jpg) · [Svi očitani tekstovi](../../qa/out/screens/np08-7.4-8.1.json) |
| 8.2 | PASS | PASS | Bez automatskog modala na šest kartica. Prvi koraci dopuštaju rad. Zapis 8.2-4.txt. |
| 8.3 | PASS | PASS | Prigušeni podnaslovi na šest kartica i dosljedna ikona ⓘ uz postavke, uključujući napredne. [8.1](../../qa/out/screens/p2-8.1.jpg) [7.9](../../qa/out/screens/p2-7.9.jpg) |
| 8.4 | PASS | PASS | Svih šest kartica ima opis neposredno ispod naslova. Tekstovi u 8.2-4.txt. |
| 8.5 | PASS | PASS | Oznaka Dokazano optimalno pri prelasku ima objašnjenje „Egzaktni solver pregledao je sve dopuštene rasporede.” [8.5](../../qa/out/screens/p2-8.5.jpg) |
| 8.6 | FAIL | PASS | Nakon brisanja svih naloga prikazan je 0/0 i odobreni tekst „Nema naloga. Dodajte nalog ili vratite podatke iz zadatka.” Prihvaćeno odstupanje UPR-Q03. [8.6](../../qa/out/screens/p2-8.6.jpg) |
| 8.7 | PASS | PASS | Tab s dnevnog limita fokusira ⓘ, Enter otvara tekst, Escape zatvara, 0 otvorenih oblačića. [8.7](../../qa/out/screens/p2-8.7.jpg) |
| 8.8 | PASS | PASS | Upozorenja imaju tekst, provjere kvačicu i naziv, rute brojeve i oznake, vremenska crta različite uzorke. [7.6](../../qa/out/screens/p2-7.6.jpg) [7.9](../../qa/out/screens/p2-7.9.jpg) [7.11](../../qa/out/screens/p2-7.11.jpg) |
| 8.9 | PASS | PASS | U istom planu vidljivi su 9.400 kg, 182,2 km i 9 h 42 min. [7.1](../../qa/out/screens/p2-7.1.jpg) |
| 8.10 | FAIL | PASS | Pri „Dodaj nalog” aplikacija odmah navodi da nema slobodnog stroja i upućuje na „Dodaj stroj”. Nakon spremanja stroja novi nalog je prihvaćen. Objašnjenje za A i plan s N04 također su dostupni. [8.10-zastoj](../../qa/out/screens/p2-8.10-zastoj.jpg) [8.10-zasto](../../qa/out/screens/p2-8.10-zasto.jpg) [8.10-n04](../../qa/out/screens/p2-8.10-n04.jpg) |
| 9.1 | PASS | PASS | 10 naredbi iz dokumenta. Izlazni kodovi [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]. [Naredbe i isječci](../../qa/out/p2/9.1.json) |
| 9.2 | PASS | PASS | 8 naredbi iz dokumenta. Izlazni kodovi [0, 0, 0, 0, 0, 0, 0, 0]. [Naredbe i isječci](../../qa/out/p2/9.2.json) |
| 9.3 | PASS | PASS | CLI, dokumenti i pytest referentne vrijednosti podudaraju se. Dodatno provjereno 16 varijanti trajanja, limita i broja mjesta iz PRETPOSTAVKE.md. [Ispis](../../qa/out/p2/9.3.txt). |
| 9.4 | PASS | PASS | U docs/ postoje LOGIKA.md, PRETPOSTAVKE.md, AI_ALATI.md, VRIJEME.md i deploy.md. |
| 9.5 | PASS | PASS | Svih pet faza i ukupni iznos sati prazni su u docs/VRIJEME.md. |
| 9.6 | PASS | PASS | Svih sedam stavki predaje ima odredište u §16. Procjenu stvarnih sati prije predaje upisuje kandidat. |
| 10.1 | PASS | PASS | POST /api/solve, sekunde 0.150, 0.159, 0.138, 0.138, 0.156; medijan 0.150. |
| 10.2 | PASS | PASS | CLI s pokretanjem procesa 1.646 s. exact, 12/12, validator=True. Seed 88731. |
| 10.3 | PASS | PASS | CLI s pokretanjem procesa 3.451 s. ortools, 40/40, validator=True. Seed 88731. |
| 10.4 | PASS | PASS | Uvoz istog scenarija od 40 naloga. Tijekom izračuna piše „Računam…”, prijelaz na Kartu radi. [10.4](../../qa/out/screens/p2-10.4.jpg) |
| 11.1 | PASS | PASS | API 200, 0/0 i 0 km. Na kartici Plan poruka „Nema naloga…” iz QA-8.6. [8.6](../../qa/out/screens/p2-8.6.jpg) |
| 11.2 | PASS | PASS | HTTP 200. {'km': 0.0, 'served': 0, 'orders': 10, 'trucks_used': 0} ['Nijedan nalog nije moguće izvršiti.'] 10 × TOO_HEAVY. |
| 11.3 | PASS | PASS | HTTP 422. body.scenario: orders.N02.machine: stroj M01 pojavljuje se u dva naloga. |
| 11.4 | PASS | PASS | HTTP 422. body.scenario: orders.N01.delivery: isto mjesto utovara i istovara. |
| 11.5 | PASS | PASS | HTTP 422. body.scenario.trucks.0.speed_kmh: vrijednost mora biti veća od nule / HTTP 422. body.scenario.settings.day_limit_min: vrijednost mora biti veća od nule / HTTP 422. body.scenario.settings.load_min: vrijednost je manja od dopuštenog minimuma |
| 11.6 | PASS | PASS | HTTP 200. {'km': 2.0, 'served': 1, 'orders': 1, 'trucks_used': 1} [] Dionice [1.0, 0.0, 1.0], radnje 40.0 min. |
| 11.7 | PASS | PASS | HTTP 200. {'km': 150.5, 'served': 8, 'orders': 10, 'trucks_used': 1} [] |
| 11.8 | PASS | PASS | HTTP 200. {'km': 182.2, 'served': 10, 'orders': 10, 'trucks_used': 1} [] Zadane postavke uspoređene po ključu. Uvezeno i kroz preglednik. [11.8](../../qa/out/screens/p2-11.8.jpg) |
| 11.9 | PASS | PASS | Uvoz datoteke s neispravnim JSON-om → „Datoteka ne sadrži valjan JSON.” Postojeći plan ostaje 182,2 km. [11.9](../../qa/out/screens/p2-11.9.jpg) |
| 11.10 | PASS | PASS | HTTP 200. {'km': 41.7, 'served': 1, 'orders': 1, 'trucks_used': 1} ['Nekorišteni kamioni: B. Uz najveći broj izvršenih naloga nije moguće koristiti više kamiona.'] ['Nekorišteni kamioni: B.'] |
| 11.11 | PASS | PASS | HTTP 422. body.scenario.trucks: popis mora imati barem jednu stavku |
| 11.12 | PASS | PASS | HTTP 422. body.scenario: depot: nepoznata lokacija baze L99. |
| 11.13 | PASS | PASS | HTTP 422. body.scenario.settings.day_start: unesite vrijeme u obliku HH:MM (00:00–23:59) |
| 11.14 | PASS | PASS | HTTP 422. body.scenario.settings.ortools_time_limit_s: vrijednost je manja od dopuštenog minimuma / HTTP 422. body.scenario.settings.ortools_time_limit_s: vrijednost prelazi dopušteni maksimum |
| 11.15 | PASS | PASS | HTTP 422. body.scenario: settings.pinned_orders.N06: stroj je teži od nosivosti kamiona A (3.500 kg). |
| 11.16 | PASS | PASS | HTTP 200. {'km': 146.1, 'served': 12, 'orders': 12, 'trucks_used': 1} ['Egzaktni solver prekinut: prevelik prostor stanja ili istek vremena.', 'Plan je od OR-Toolsa, bez dokaza optimalnosti.'] ortools, 5.482 s. |
| 12.1 | PASS | PASS | dc7fb375abf4b77d7e732b4ed15350da0fe44edac39862375725162e3dd28e91 |
| 12.2 | PASS | PASS | git ls-files priprema → 0 putanja. |
| 12.3 | PASS | PASS | 0 praćenih putanja s obrascima za tajne, 0 pogodaka za provjerene vrste tokena i ključeva. |
| 12.4 | PASS | PASS | git status --short prazan; git check-ignore potvrđuje qa/out/common.py. |
| 12.5 | PASS | PASS | Nula praćenih putanja i nula commitova u dostupnim refovima. |
| 12.6 | PASS | PASS | Čisti klon: origin/main..HEAD prazan. GitHub Actions Tests za a68165c završio success, run 45082159620. Provjeren i privatni origin/main prije objave. |
| 12.7 | PASS | PASS | dd67d08 docs → 2b0f4c7 test → faea944 feat. Povijest prati iste korake i poslije; dostupni refovi ne mogu dokazati da nikad nije bilo prepisivanja. |
| 12.8 | PASS | PASS | {"visibility":"PRIVATE"} |
| 13.1 | PASS | PASS | docker build -t uprent-planner . → #16 DONE 8.2s |
| 13.2 | PASS | PASS | Samostalni kontejner na portu 8000. GET /api/health → {"status":"ok"} |
| 13.3 | PASS | PASS | Na javnom URL-u učitan je isti index-DUrFn9Lm.js kao u novom klonu. Health ok; 182,2 km, Primijeni → 200,1 km i A/N03; novo objašnjenje slobodnog stroja; teški N11 → 10/11 i razlog 12.000 kg > 10.000 kg. [13.3-health](../../qa/out/screens/p2-13.3-health.jpg) [13.3-default](../../qa/out/screens/p2-13.3-default.jpg) [13.3-alt](../../qa/out/screens/p2-13.3-alt.jpg) [13.3-ispravak](../../qa/out/screens/p2-13.3-ispravak.jpg) [13.3-heavy](../../qa/out/screens/p2-13.3-heavy.jpg) |
| 13.4 | PASS | PASS | Cloudflare je prije prvog zahtjeva prikazivao inactive. Do vidljivog odgovora health 3.232 s. |
| 14.1 | PASS | PASS | 5.1 ulazni podaci — 7.6, 7.7, 1.3 |
| 14.2 | PASS | PASS | 5.2 raspodjela — 3.1–3.3 |
| 14.3 | PASS | PASS | 5.3 redoslijed — 6.2, 7.1 |
| 14.4 | PASS | PASS | 5.4 nosivost i mjesta — 5.3, 5.4, 2.1 |
| 14.5 | PASS | PASS | 5.5 isti kamion i utovar prije istovara — 5.5, 5.6 |
| 14.6 | PASS | PASS | 5.6 učinkovitost — 3.1, 4.3 |
| 14.7 | PASS | PASS | 5.7 km po kamionu i ukupno — 6.2, 7.1 |
| 14.8 | PASS | PASS | 5.8 upozorenja — 3.8, 3.12, 7.5, 7.6 |
| 14.9 | PASS | PASS | 6 prikaz po kamionu — 7.1, 21 korak s teretom, radnjom i lokacijom |
| 14.10 | BLOCKED | BLOCKED | 8 predaja — 9.1–9.6, 13.3; sedam odredišta postoji, nedostaje kandidatov broj sati. |
| 14.11 | PASS | PASS | Vrijeme, brzina i baza — 3.2, 3.4, 5.2, 6.2 |

### Pokrivenost 16 skupina iz QA-2.4

Datoteke su u mapi `tests/`.

| Skupina | Datoteke | Testovi |
|---|---|---|
| 1 Udaljenost | test_distance.py | test_task_legs, test_identical_coordinates_zero |
| 2 Zadani optimum | test_service.py, test_validator.py | test_default_result, test_b_alone_valid_by_default |
| 3 Drugo tumačenje | test_exact_solve.py, test_validator.py | test_handling_counts, test_require_all_trucks, test_strict_plan_valid |
| 4 Trajanje radnji | test_exact_solve.py | test_handling_time_drive_mode, test_handling_time_strict |
| 5 Dnevni limit | test_exact_solve.py | test_drive_limit, test_strict_day_limit, test_no_partial |
| 6 Najraniji završetak | test_exact_solve.py | test_makespan |
| 7 Granično vrijeme | test_validator.py | test_boundary_plan |
| 8 Masa | test_validator.py | test_exact_capacity_allowed, test_capacity_l7_swap |
| 9 Broj strojeva | test_validator.py, test_exact_solve.py | test_slots_exceeded, test_slots_only_truck_a |
| 10 Redoslijed i identitet | test_validator.py | test_delivery_before_pickup, test_other_truck_delivers, test_double_pickup, test_machine_left_on_truck, test_reported_km_without_return |
| 11 Pretežak stroj | test_service.py, test_ortools.py | test_n11_partial, test_too_heavy_does_not_crash |
| 12 Usporedba solvera | test_ortools.py | test_random_ortools_never_beats_exact |
| 13 Generativna svojstva | test_ortools.py | test_small_plans_pass_validator |
| 14 Provjera ulaza | test_domain.py | test_rejects_machine_in_two_orders, test_rejects_unknown_location, test_rejects_nonpositive_speed |
| 15 API i CLI | test_api.py, test_cli.py | test_solve_default, test_solve_invalid_422, test_cli_set_override |
| 16 Granični ulazi | test_service.py | test_zero_orders, test_all_too_heavy, test_thirteen_orders_uses_ortools |

### Prvi korisnik (QA-8.10)

Broje se klikovi na gumbe i kartice. Unos u polje broji se zasebno. Zadaci o nekorištenom A i N04 počinju od zadanih podataka. U strogom planu A već vozi.

| Zadatak | Prvi prolaz i mjesta zastoja |
|---|---|
| Izračunaj plan | 0 klikova za automatski rezultat ili 1 za „Izračunaj plan”. Traka Prvi koraci objašnjava automatski izračun. |
| Primijeni drugo tumačenje | 1 klik na prvi „Primijeni”. Dva isto ispisana gumba zahtijevaju čitanje pripadajućeg retka. |
| Dodaj nalog | 8 klikova do spremanja, još 1 na Plan za potvrdu 11/11. Slijed: Ulazni podaci → Dodaj nalog → Spremi nalog → Odustani → Dodaj stroj → Spremi stroj → Dodaj nalog → Spremi nalog. Dodatno je upisana masa 800 kg. Novi nalog nema slobodnog stroja, a poruka traži samo unos. Korisnik mora sam povezati dvije tablice. |
| Pronađi zašto A ne vozi | 1 klik na „Zašto?” uz A. Piše da B stigne sam i da prebacivanje dodaje najmanje 17,9 km. Nakon strogog tumačenja trebalo je vratiti zadano stanje kroz Pomoć. |
| Prikaži N04 na A | 2 klika, Analiza → „Prikaži plan” u retku N04. Na dugoj kartici treba pronaći tablicu ispod grafa i razlikovati jednake natpise gumba. Plan prikazuje i N01 na A. |

## Nalazi

| ID | QA ID | Ozbiljnost | Koraci | Očekivano | Dobiveno u prvom prolazu |
|---|---|---|---|---|---|
| UPR-Q01 | 8.10 | važno | Zadani podaci → Dodaj nalog → Spremi nalog | Početnik može ustanoviti preduvjet i dovršiti zadatak | Svi strojevi su zauzeti. Obrazac nudi prazno polje i poruku „Upišite polje Stroj.” |
| UPR-Q02 | 7.4 | manje | Strogi limit, 21 min za obje radnje | 217,0 km | Prikaz 217 km. Numerički rezultat je ispravan. |
| UPR-Q03 | 8.6 | manje (očekivanje plana) | Obriši sve naloge i otvori Plan | Prvotni plan tražio je „Dodaj nalog ili vrati …” | „Dodajte nalog ili vratite …”. Vlasnik je nakon prvog prolaza prihvatio postojeći tekst kao ispravan jer odgovara načinu obraćanja u sučelju. |
| UPR-Q04 | 2.4 | manje (QA plan) | Usporedi tekst QA-2.4 sa spec. §15 | Plan spominje 16 skupina | §15 sada numerira 27. Mapiranje iznad zadržava traženih prvih 16. |
| UPR-Q05 | 14.10 | blokira predaju | Otvori tablicu stvarnog vremena | Procjena pri predaji | Prazna je, što QA-9.5 dopušta. Podatak može dati kandidat. |

### Dodatni nalaz drugog prolaza

| ID | QA ID | Ozbiljnost | Koraci | Očekivano | Dobiveno |
|---|---|---|---|---|---|
| UPR-Q06 | 8.1 | manje | Ulazni podaci → Uredi A → Brzina (km/h) | Objašnjenje ⓘ i za brzinu iz §6 | Prikazane su jedinica i vrijednost 60, ali nema ikone ni objašnjenja. Do ovog se polja dolazi izvan ploče Postavke. |

## Ispravci nakon prvog prolaza

| Nalaz | Commit ili odluka | Ponovljeni QA ID-evi | Ishod |
|---|---|---|---|
| UPR-Q01 | `a68165c` (izvorni kod, postojeći regresijski test i izgrađeno sučelje) | QA-0 do QA-14, izravno 7.6, 8.10 i 13.3 | PASS za ispravak. Bez slobodnog stroja korisnik odmah vidi što treba učiniti. Nakon dodavanja novog stroja N11 se sprema. |
| UPR-Q03 | Odluka vlasnika za drugi prolaz, bez promjene aplikacije | 8.6 | PASS prema prihvaćenom odobrenju teksta. Prvi ishod ostaje zabilježen. |
| UPR-Q02, UPR-Q04, UPR-Q06 | Manji nalazi, bez commita ispravka | 7.4, 2.4, 8.1 | Kilometraža je točna. Uz cijeli broj nedostaje završna decimala. Brzina ima jedinicu, ali nema ⓘ. Specifikacija ima više skupina od broja koji navodi QA plan. |
| UPR-Q05 | Potrebna je stvarna procjena kandidata | 9.5, 9.6, 14.10 | Predložak zadovoljava QA-9.5. Za samu predaju nedostaju sati. |

U ponovljenom QA-8.10 izračun je tražio 0/1 klik, drugo tumačenje 1, dodavanje naloga 6 do spremanja te 1 na Plan za potvrdu. Slijed za dodavanje bio je Ulazni podaci → Dodaj nalog → Dodaj stroj → Spremi stroj → Dodaj nalog → Spremi nalog, uz zaseban unos mase od 800 kg. Zašto A ne vozi pronađeno je jednim klikom, a N04 na A prikazan je u dva. Za prvi klik na „Dodaj nalog” sada postoji jasno objašnjenje preduvjeta. Korisnik i dalje mora prijeći iz tablice naloga do tablice strojeva.

GitHub Actions završio je uspješno za ispravak prije ponovne objave. Cloudflare je objavio verziju `4c198a98-77ac-449d-b58a-19a0d63b7ded` uz postojeći `max_instances: 1`. [CI ispravka](https://github.com/Lovre-P/uprent-smart-logistics-planner/actions/runs/45082159620) · [Javni demo](https://uprent-smart-logistics-planner.lovre-petrina2.workers.dev/)

## Napomene za neovisni pregled (Claude)

- Usporedi referencu i aplikaciju na dodatnim ulazima. U QA-4.3 razlika u km računa se samo za jednak broj izvršenih naloga.
- Usporedi korake za N04 i učinak klika na zadnju točku krivulje. U prvom prolazu prvo očitanje nakon klika ostalo je na osnovnom planu, a ponovljeni klik dao je 284,2 km.
- QA-12.3 pretražuje praćena imena i prepoznatljive potpise tajni. QA-12.7 opisuje dostupnu povijest. U tim provjerama granice dokaza su obrasci i dostupni Git refovi.
- QA-8.10 je simulacija novog korisnika u sučelju. Isti je ispitivač prethodno izvršio propisane QA-7 korake. Neovisni prvi korisnik može utvrditi druga mjesta zastoja.
