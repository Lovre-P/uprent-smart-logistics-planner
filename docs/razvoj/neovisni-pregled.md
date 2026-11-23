# Neovisni pregled

23. studenoga 2026. · Claude · pregledani commit `858f193`. Javni demo poslužuje istu izgradnju kao `a68165c`.

## Sažetak

**Logika planera je ispravna.** U 400 slučajnih scenarija egzaktni solver dao je isti broj naloga, kamiona, cilj i kilometražu kao neovisna provjera. U 100 scenarija to je referentni solver, a u 300 iscrpna pretraga. Iscrpnoj pretrazi odgovaraju i druga tumačenja, krivulja km ↔ kraj dana, granica limita i razlike u tablici „Zašto ovakva raspodjela”. Samo u četiri retka te tablice, uz isključen djelomičan plan, tekst ne opisuje točno razlog (NP-12). Validator je stvarno neovisan, a nijedan plan nije prošao uz kršenje pravila.

Prije predaje treba upisati stvarne sate i ispraviti dvije vidljive pojedinosti u sučelju:

- kilometraža ponekad gubi decimalu („217 km”, „17 km”);
- plan prikazan s krivulje ili tablice „Zašto” i dalje nosi oznaku „Dokazano optimalno”, a nigdje na zaslonu ne piše da su nalozi prikvačeni.

Ostalo su manje dopune dokumentacije i neobavezna poboljšanja.

## Što je provjereno

| Područje | Način | Ishod |
|---|---|---|
| Dokumenti razvoja | `qa-izvjestaj.md`, `implementacija-sazetak.md`, `odstupanja.md` | Odluke su dosljedno zabilježene. Prekinute poveznice opisuje NP-11. |
| Egzaktni solver (`exact.py`) | Čitanje koda prema spec. §9.1 | DP nad (preuzeti, isporučeni, lokacija) je ispravan. Svaki prijelaz dodaje točno jednu radnju, pa obrada sloj po sloj daje najkraće putove. Dijeljenje tablica po tipu kamiona ispravno je i uz različite brzine, jer je za isti skup naloga najkraća ruta ujedno najbrža. Kombiniranje je leksikografsko: nalozi → kamioni → cilj → km. Prečac komplementa na zadnjem kamionu ne mijenja rezultat. |
| OR-Tools (`ortools_solver.py`) | Čitanje koda prema spec. §9.2 | Dimenzije `limit_time` i `work_time` su odvojene i počinju od nule. Svaka dionica i radnja zaokružuje se naviše, a limit naniže, pa plan OR-Toolsa ne može prekršiti limit. Disjunkcije su zasebne. Kazna za izostavljeni nalog veća je od svih kazni za kamione zajedno, a kazna za kamion veća je od cijelog cilja. Provjera raspona int64 je ispravna. Brojač radnji osigurava redoslijed na istoj lokaciji. |
| Validator (`validator.py`) | Čitanje koda | Uvozi samo `domain` i `plan`. Dionice računa vlastitom formulom (`Fraction` i `isqrt`) i vrijeme točno. Teret i broj strojeva provjerava nakon svake radnje. `svi_kamioni` je samo informativna provjera. |
| Predprovjera (`precheck.py`) | Čitanje koda i ciljani primjer | Floyd–Warshall nad bazom i svim lokacijama naloga daje valjanu donju granicu. Protuprimjer iz v4.2 daje `OPTIMAL`, 2/2 i 11,3 km. |
| Analiza (`analysis.py`) | Čitanje koda i iscrpna pretraga | Druga tumačenja, „Zašto”, krivulja i gornja granica limita podudaraju se s iscrpnom pretragom (vidi dolje). Izuzetak je tekst opisan u NP-12. |
| Usporedba s referentnim solverom | `compare_with_app.py --seeds 100 --start 5000` | **100/100** scenarija bez greške. OR-Tools je u 91 scenariju dao optimum. U 7 je bio lošiji za 3,9–14,1 %, a u 2 je izvršio manje naloga (NP-06). |
| Rubni slučajevi izvan QA-a | Vlastita iscrpna pretraga nad tablicama referentnog solvera, 300 scenarija (sjemena 7000–7299) | **Nijedno odstupanje u planu ni statusu.** Provjereno je 30 slučajeva `NO_FULL_PLAN`, 64 s ciljem najranijeg završetka, 540 drugih tumačenja, 165 krivulja s gornjom granicom limita i 1.060 redaka „Zašto”. Četiri retka „Zašto” uz isključen djelomičan plan imaju netočan tekst (NP-12). OR-Tools je izvršen 270 puta. Nijedan njegov plan nije prekršio pravila ni izvršio više naloga od optimuma. Uz cilj km nijednom nije dao kraću rutu. Dva puta izvršio je manje naloga. |
| Ciljani slučajevi | Pojedinačni izračuni | Vidi tablicu „Ciljani slučajevi”. |
| Sučelje | Javni demo u ugrađenom pregledniku, 1280 px | Plan, „Zašto?”, Analiza, klik na krivulju, Provjera i Karta rade. Nalazi NP-02, NP-03 i NP-09. |
| Dokumentacija | README, upute, LOGIKA, PRETPOSTAVKE, AI_ALATI, VRIJEME | Referentne vrijednosti u PRETPOSTAVKE.md odgovaraju ranijim izračunima referentnim solverom i QA-u. Četiri vrijednosti koje dosad nisu bile potvrđene sada su izračunate i točne su: strogo 8 h, 5 h 45 min, 5 h 30 min te N04 na A uz ostale na B. Nalazi NP-01, NP-04, NP-05 i NP-11. |
| Tajne i povijest | `git log --all -p`, `git grep` | ID Cloudflare računa ne pojavljuje se nigdje u povijesti. U praćenim datotekama nema lokalnih putanja. |

### Rubni slučajevi izvan QA-a

Generator mijenja ono što QA-4 drži stalnim:

- brzine 45, 60, 68, 75,5 i 90 km/h, pa vožnja nije cijeli broj sekundi;
- treći kamion (6.000 kg, dva mjesta);
- trajanje radnji po nalogu, uključujući nulu;
- trajanja s decimalama (20,5 i 7,25 min);
- limiti 100,5 i 539,9 min;
- dvije lokacije na istoj točki;
- preteški strojevi;
- isključen djelomičan plan;
- cilj najranijeg završetka.

Za svaki scenarij iscrpna pretraga nabraja sve raspodjele skupova naloga po kamionima nad tablicama najkraćih ruta referentnog solvera. Uspoređuje se sljedeće:

- broj izvršenih naloga, broj kamiona, cilj i km;
- `NO_FULL_PLAN` kad djelomičan plan nije dopušten;
- svako drugo tumačenje i njegov izostanak;
- svaki redak „Zašto” s razlikom km;
- svaka točka krivulje;
- gornja granica limita;
- validator i OR-Tools na istom ulazu.

### Ciljani slučajevi

| Slučaj | Ishod |
|---|---|
| Strogi limit od 100 min (Geminijev nalaz 1) | 2/10, 71,7 km. N06 je `TOO_LONG_ALONE`. Drugo tumačenje „samo vožnja” daje **7/10 i 130,5 km**, isto kao referentni solver. |
| 13 naloga, tri preteška, automatski izbor | Odabran je OR-Tools: `FEASIBLE_PARTIAL`, 10/13, 182,2 km. Kod broji sve naloge (NP-04). |
| Strogi limit od 300 min bez djelomičnog plana | `NO_FULL_PLAN` uz poruku „najviše 8 od 10”. Drugo tumačenje se ne nudi, iako „samo vožnja” daje 10/10 i 182,2 km (NP-07). |
| N04 prikvačen na A | 217,0 km. A vozi N01 i N04, kao u tablici „Zašto”. |
| N04 na A, ostali na B | 218,8 km, kao u PRETPOSTAVKE.md. |
| Strogi limit od 480 / 345 / 330 min | 235,1 km / 284,2 km / 9 od 10 naloga, kao u PRETPOSTAVKE.md. |
| Zadano: analiza | Druga tumačenja 200,1 i 200,1 km. Krivulja ima 14 točaka (182,2/582,2 → 284,2/344,8). A nije korišten jer bi svaki prebačeni nalog dodao najmanje 17,9 km. Limit vožnje nije aktivan. |
| Strogo: osjetljivost | Najviše 20,95 min po radnji. Pri 21 min plan ima 217,0 km. Gornja granica limita: bolji plan od 182,2 km postoji uz limit od 582,2 min. |

## Nalazi

| ID | Ozbiljnost | Gdje | Nalaz | Prijedlog |
|---|---|---|---|---|
| NP-01 | blokira predaju | `docs/VRIJEME.md` | Tablica stvarnog vremena je prazna, a točka 8 zadatka traži procjenu (UPR-Q05). | Kandidat upisuje vlastite sate. |
| NP-02 | važno za dojam | `web/src/lib/format.ts:2`, `src/uprent/analysis.py:18` | `formatKm` ima najviše jednu decimalu, ali ne zahtijeva nijednu. Tablica koraka zato miješa „10,8 km” sa „17 km”, „18 km”, „57 km” i „163 km”. Ukupno piše „217 km” (UPR-Q02), a tekst osjetljivosti „uz 217 km”. Spec. §13 traži hrvatski format s jednom decimalom („182,2 km”). | U `formatKm` dodati `minimumFractionDigits: 1`. Za km u tekstovima analize koristiti formater s fiksnom jednom decimalom. Minute i kg ostaju kakvi jesu. Dodati test za „217,0 km” i dionicu „17,0 km”. |
| NP-03 | važno (UX demonstracije) | `CurveChart.tsx:13–17`, `AnalysisView.tsx:58`, `SettingsPanel.tsx:81` | Klik na točku krivulje ili na „Prikaži plan” prikvači naloge i ponovno izračuna plan. Na Planu je tada npr. 284,2 km, a zaglavlje piše „Dokazano optimalno. Egzaktni solver pregledao je sve dopuštene rasporede.” Cilj je i dalje „Najmanje kilometara”. Prikvačeni nalozi vidljivi su samo u zatvorenom dijelu Napredno, a na Planu nema povratka na optimum. Izjava je točna samo uz prikvačene naloge. Promatraču izgleda kao da je 284,2 km optimum. | Kad `pinned_orders` nije prazan, iznad Plana i Analize prikazati traku: „Prikazan je raspored uz prikvačene naloge (N03 → A, …). Optimalan je uz ta prikvačivanja.” Dodati gumb **Vrati optimalni plan** koji briše prikvačene naloge. Oznaku statusa promijeniti u „Optimalno uz prikvačene naloge”. Dodati test: nakon klika na točku vidljivi su traka i gumb, a gumb vraća 182,2 km. |
| NP-04 | manje (dokumentacija) | `README.md:61`, `docs/upute.md:46`, `docs/razvoj/implementacija-sazetak.md:10` | Tekst kaže da se egzaktni solver bira za 12 naloga „koji prođu predprovjeru”. Kod broji sve naloge (`service.py:28`), kao i spec. §9.3 i LOGIKA.md. Primjer: 13 naloga od kojih su 3 preteška ide u OR-Tools. | Tekst uskladiti s kodom: „do 12 naloga i 3 kamiona”. |
| NP-05 | manje (dokumentacija) | `docs/AI_ALATI.md` | Redak „Claude” još je samo najava pregleda i ne navodi stvarnu ulogu. Claude je usporedio tri pristupa i egzaktnim izračunom potvrdio 182,2 i 200,1 km. Napisao je specifikaciju, plan implementacije, QA plan i referentni solver, a zatim napravio ovaj pregled. Odlomak o usporedbi spominje samo 30 scenarija. | Ispraviti redak „Claude”. Dodati brojke ovog pregleda (100 + 300 scenarija, NP-06) i ocjenu Geminijevih nalaza (dolje). |
| NP-06 | informativno | `ortools_solver.py` | U 3 s OR-Tools je na 100 scenarija dao optimum 91 put. Sedam puta bio je lošiji za 3,9–14,1 %, uglavnom uz „Svaki kamion mora voziti” ili tijesan limit, a dva je puta izvršio manje naloga. U dva provjerena slučaja dulja pretraga dosegla je optimum: 5011 za 10 s, 5065 za 30 s. To nije pogreška modela, nego svojstvo heuristike, pa oznaka „Najbolje pronađeno” odgovara. Rezultat QA-4.3 od 0,00 % ne treba poopćavati. | Nije potrebna izmjena koda. U AI_ALATI.md ili LOGIKA.md može se pošteno navesti ova brojka. |
| NP-07 | manje (UX) | `service.py:113` | Uz isključen djelomičan plan i rezultat `NO_FULL_PLAN` analiza se preskače, pa nema trake „Drugo tumačenje”. Drugo tumačenje tada je najkorisnije: strogi limit od 300 min nema potpunog plana, a „samo vožnja” daje 10/10. | Nije nužno prije predaje. Kasnije se za egzaktni `NO_FULL_PLAN` mogu izračunati samo druga tumačenja. |
| NP-08 | sitno | obrazac kamiona | Uz brzinu nema ⓘ (UPR-Q06). | Neobavezno. |
| NP-09 | sitno | kartica Provjera | Provjera „Korištenje svih kamiona — nije primjenjivo” ima zelenu oznaku „Prolazi”. | Neobavezno: oznaka „Nije primjenjivo”. |
| NP-10 | neobavezno (robusnost demoa) | `api.py` | Veličina ulaza nije ograničena. `/api/compare` prima proizvoljno mnogo varijanti, a svaka je puni izračun (OR-Tools do 30 s). Demo ima jednu instancu, pa jedan velik zahtjev može zauzeti demo tijekom razgovora. | Ograničiti npr. 100 naloga, 100 lokacija i 10 varijanti, uz poruku 422. |
| NP-11 | sitno | `docs/razvoj/qa-izvjestaj.md` | Postoji 36 poveznica na `qa/out/…`, a ta je mapa izvan repozitorija. Na GitHubu poveznice vode na 404. | Na vrhu izvještaja napisati da su dokazi lokalni. Po želji commitati desetak ključnih snimki u `docs/razvoj/qa-dokazi/`. |
| NP-12 | sitno | `src/uprent/analysis.py:111–114` | Uz isključen djelomičan plan redak „Zašto” javlja npr. „Uz prikvačivanje na A odabrani plan izostavlja N08.” Provjera pokazuje da s tim prikvačivanjem ne postoji nijedan potpuni plan: najbolji izvršava 7/8 i N08 je u njemu. Zaključak da se nalog ne može premjestiti je točan, ali razlog nije. Primjeri: sjemena 7154 i 7222. | Kad izračun uz prikvačivanje nema potpunog plana, napisati: „S nalogom N08 na A potpuni plan nije moguć.” |

## Ocjena Geminijeva pregleda koda

| Geminijev nalaz | Ocjena | Obrazloženje |
|---|---|---|
| 1. Druga tumačenja bez naloga `TOO_LONG_ALONE` | **Ne vrijedi u stvarnom toku** | `service.py:37` gradi tablice od svih naloga osim preteških, upravo da bi analiza mogla promijeniti tumačenje. Gemini je to naveo kao uvjet. Na njegovom scenariju drugo tumačenje daje 7/10 i 130,5 km, kao referentni solver. Sva druga tumačenja u 300 rubnih scenarija također se podudaraju. Neobavezno: regresijski test za ovaj scenarij, da buduća izmjena servisa ne uvede grešku. |
| 2. „217” umjesto „217,0” | **Vrijedi** | Isto kao NP-02. U sučelju je opseg veći: zahvaća i dionice i zbrojeve u tablici koraka. |
| 3. `VehicleVar.SetValues` umjesto `SetAllowedVehiclesForIndex` | Ispravno opaženo, bez učinka | Razlog je zabilježen u `odstupanja.md`. Po želji jednom rečenicom uskladiti spec. §9.2. |
| 4. `NOT_FOUND` umjesto `NO_FULL_PLAN` pri izravnom pozivu | **Nedostižno kroz aplikaciju** | `service.py:29–33` vraća `NO_FULL_PLAN` prije poziva OR-Toolsa kad predprovjera izbaci nalog, a djelomičan plan nije dopušten. Izmjena nije potrebna. |

## Napomene iz QA izvještaja

- Usporedba na dodatnim ulazima: obavljena (100 + 300 scenarija, gore).
- Klik na zadnju točku krivulje: na javnom demou prvim je klikom prikazan plan od 284,2 km. Tu je uočen NP-03.
- N04 na A: 217,0 km. A vozi N01 i N04 u planu i u tablici „Zašto”.
- Tajne: u cijeloj dostupnoj povijesti ID računa ne pojavljuje se nijednom.

## Preporuka prije predaje

1. **NP-01:** upisati stvarne sate u `docs/VRIJEME.md`. To radi kandidat.
2. **NP-02:** jedna decimala za km svugdje. Ispravak je kratak.
3. **NP-03:** traka i povratak na optimalni plan kod prikvačenih naloga. Ispravak je mali i sprječava zabunu u demonstraciji.
4. **NP-04 i NP-05:** uskladiti tekst o pragu i dopuniti AI_ALATI.md.
5. Ponovno izgraditi sučelje i pokrenuti testove i CI, zatim objaviti demo i na javnom URL-u provjeriti 182,2 km, „Primijeni” → 200,1 km i klik na krivulju.
6. Pri predaji repozitorij učiniti javnim.

Neobavezno, ako ostane vremena: NP-11, NP-12, NP-08, NP-09 i NP-10. NP-07 je za kasnije.

## Ponovljivost

Usporedba s referentnim solverom pokreće se naredbom `uv run python qa/oracle/compare_with_app.py --seeds 100 --start 5000`. Skripta za 300 rubnih scenarija pokrenuta je izvan repozitorija. Na tablicama `qa/oracle/oracle_exact.py` nabraja sve raspodjele i uspoređuje ih s izlazom funkcije `uprent.service.solve`. Na zahtjev se može dodati u `qa/oracle/`.

## Ispravci nakon pregleda

23. studenoga 2026. · Codex · svih šest zatraženih nalaza je ispravljeno. Izvorni pregled pohranjen je zasebno u commitu `c49dddc`. Za svaki je nalaz provjera prije izmjene pokazala opisani problem, a nakon izmjene prošla.

| Nalaz | Commit | Što je potvrđeno |
|---|---|---|
| NP-02 | `89dfb7c` | Uz strogi limit i trajanje utovara i istovara od po 21 min plan prikazuje **217,0 km**. Tablica koraka prikazuje **17,0 km**, a tekst analize također zadržava decimalu. |
| NP-03 | `f854443` | Iznad Plana i Analize vidi se koji su nalozi prikvačeni. Egzaktni raspored ima oznaku „Optimalno uz prikvačene naloge”. OR-Tools zadržava „Najbolje pronađeno”. Gumb „Vrati optimalni plan” uklanja prikvačivanja. |
| NP-04 | `f909004` | README, upute i sažetak implementacije navode isti prag automatskog izbora egzaktnog solvera, do 12 naloga i 3 kamiona. |
| NP-05 | `64d88cf` | U dokumentu o AI alatima provjereni su opis Claudeova rada, poveznica na ovaj pregled, zaključak o Geminijevoj primjedbi i odlomak o dodatnih 100 i 300 scenarija. |
| NP-11 | `79a65e2` | Na vrhu QA izvještaja piše da se snimke i izlazi čuvaju lokalno u `qa/out/`. |
| NP-12 | `ce461d6` | Ulaz za sjeme 7154 spremljen je u `tests/fixtures/review_7154.json`. Početni plan izvršava 8/8 naloga. Uz N08 na A potpuni je plan neizvediv, a dopušteni djelomični izvršava 7/8, uključujući N08. Redak „Zašto” sada glasi „S nalogom N08 na A potpuni plan nije moguć.” |

**Izgradnja i testovi.** `npm run build` je prošao. Lokalno su prošla 224 testa za Python, 68 za sučelje i 8 Playwright testova. Prvi istodobni pokušaj iscrpio je memoriju. Paketi su zatim pokrenuti redom, uz `--maxWorkers=2` za Vitest. Na GitHubu su za commit `ce461d6` prošla oba posla, `python` i `web`. [CI za ispravke](https://github.com/Lovre-P/uprent-smart-logistics-planner/actions/runs/45132669747).

**Javni demo.** Nakon CI-ja objavljena je verzija `ff7aac49-31fd-4962-a99d-3e31a3a86b5c` uz `max_instances: 1`. Pri prvom otvaranju preglednik je još učitao prethodnu izgradnju. Nakon osvježavanja učitao je `index-CU6mLAyk.js`, koji odgovara završnoj izgradnji. Sljedeće su provjere izvedene klikovima u ugrađenom pregledniku na toj verziji. [Otvori javni demo](https://uprent-smart-logistics-planner.lovre-petrina2.workers.dev/).

| Radnja | Ishod | Lokalni dokaz u `qa/out/screens/` |
|---|---|---|
| Otvoriti početni plan i pregledati korake kamiona B | PASS · **182,2 km**. Svih 21 dionica ima jednu decimalu, uključujući **17,0 km**, **18,0 km** i **0,0 km**. | `np-01-pocetni.jpg`, `np-02-dionice.jpg` |
| Kliknuti „Primijeni” za uključivanje utovara i istovara u limit | PASS · **200,1 km**. | `np-03-primijeni.jpg` |
| Vratiti početne postavke, otvoriti Analizu i kliknuti točku 284,2 km / 344,8 min | PASS · Plan prikazuje **284,2 km** i status „Optimalno uz prikvačene naloge”. Traka u Planu i Analizi navodi svih deset dodjela, uključujući N03 → A, i gumb za povratak. | `np-04-prikvaceni-plan.jpg`, `np-05-prikvacena-analiza.jpg` |
| U Analizi kliknuti „Vrati optimalni plan” | PASS · Plan ponovno prikazuje **182,2 km** i „Dokazano optimalno”. Traka je nestala. | `np-06-povratak.jpg` |

Svi zabilježeni odgovori API-ja tijekom javne provjere imali su status HTTP 200. Konzola nije zabilježila upozorenja ni pogreške. Očitane dionice, tekst trake, završni status i mrežni odzivi spremljeni su u `qa/out/screens/np-javna-provjera.json`.
