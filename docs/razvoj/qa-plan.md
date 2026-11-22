# QA plan – UP RENT Smart Logistics Planner

**Izvršava:** Codex, nakon što su zadaci 1–18 iz `docs/razvoj/plan-implementacije.md` gotovi.
**Nakon toga:** Claude radi neovisni pregled (logika, neovisnost validatora, usporedba s referentnim solverom na više scenarija, upute u sučelju, dokumentacija).
**Izlaz:** `docs/razvoj/qa-izvjestaj.md` prema predlošku na kraju ovog dokumenta.

## Pravila izvođenja

1. QA provjerava i bilježi; **tijekom QA prolaza ne mijenja kod aplikacije**. Pomoćne skripte za QA smiju se pisati samo u `qa/out/` (ne commitaju se).
2. Svaka provjera ima: ID, način provjere (naredba ili koraci), očekivani rezultat, **dokaz** (isječak izlaza, snimka zaslona u `qa/out/screens/`) i ishod: `PASS`, `FAIL` ili `BLOCKED` (s razlogom).
3. Očekivane vrijednosti iz ovog dokumenta su mjerodavne. Ako se aplikacija i dokument razilaze, to je `FAIL` – QA ne smije „prilagoditi" očekivanje. Ako QA misli da je dokument pogrešan, zapisuje to kao zaseban nalaz.
4. Kad su svi nalazi ispravljeni (u zasebnim commitima s ID-om nalaza u poruci), **cijeli QA se ponavlja** i izvještaj se ažurira.
5. Sve naredbe se pokreću iz korijena repozitorija, osim gdje piše drugačije.

Pomoćna naredba za čitanje rezultata (koristi se u QA-3):

```
uv run uprent solve data/default_scenario.json --json <ARGUMENTI> | uv run python -c "import json,sys; r=json.load(sys.stdin); print(r['status'], r['totals'], {t['id']: t['orders'] for t in r['trucks']}, [u['order'] + ':' + u['reason'] for u in r['unserved']])"
```

## QA-0 Okruženje

| ID | Provjera | Očekivano |
|---|---|---|
| 0.1 | `uv --version`, `uv run python --version` | uv radi; Python 3.11.x |
| 0.2 | `node --version` (samo za testove sučelja) | v20 ili noviji |
| 0.3 | čisti klon s GitHuba: `gh repo clone uprent-smart-logistics-planner ../uprent-qa`; QA-1 se radi u toj mapi | klon uspješan; time se provjerava ono što je stvarno na GitHubu |

## QA-1 Instalacija i pokretanje iz čistog klona (bez Nodea)

| ID | Provjera | Očekivano |
|---|---|---|
| 1.1 | `uv sync` | bez greške |
| 1.2 | `uv run uprent serve --port 8000`, zatim `curl http://127.0.0.1:8000/api/health` | `{"status":"ok"}` |
| 1.3 | otvori `http://127.0.0.1:8000/` | sučelje se učita bez pokretanja `npm`; prikazan plan 182,2 km |
| 1.4 | `web/dist/index.html` je u gitu (`git ls-files web/dist`) | postoji |

## QA-2 Automatski testovi

| ID | Provjera | Očekivano |
|---|---|---|
| 2.1 | `uv run pytest -q` | svi prolaze; zabilježi broj testova |
| 2.2 | `cd web && npm ci && npm test` | svi prolaze |
| 2.3 | `cd web && npx playwright install chromium && npm run e2e` | svi prolaze |
| 2.4 | postoje testovi svih 16 skupina iz spec §15 (popiši datoteku i ime testa za svaku) | sve skupine pokrivene |

## QA-3 Referentne brojke kroz CLI

| ID | `<ARGUMENTI>` | Očekivano |
|---|---|---|
| 3.1 | (ništa) | `OPTIMAL`, km 182.2, served 10, A `[]` |
| 3.2 | `--set limit_includes_handling=true` | `OPTIMAL`, km 200.1, A `["N03"]` |
| 3.3 | `--set require_all_trucks=true` | km 200.1, A `["N03"]` |
| 3.4 | `--set limit_includes_handling=true --set load_min=21 --set unload_min=21` | km 217.0 |
| 3.5 | `--set limit_includes_handling=true --set load_min=10 --set unload_min=10` | km 182.2 |
| 3.6 | `--set load_min=30 --set unload_min=30` | km 182.2 |
| 3.7 | `--set day_limit_min=150` | km 239.2 |
| 3.8 | `--set limit_includes_handling=true --set day_limit_min=300` | `OPTIMAL_PARTIAL`, served 8, km 203.8, dva naloga s `DOES_NOT_FIT_TOGETHER` |
| 3.9 | `--set limit_includes_handling=true --set day_limit_min=300 --set allow_partial=false` | `NO_FULL_PLAN` |
| 3.10 | `--set objective=makespan` | km 284.2 |
| 3.11 | `--solver ortools` | `FEASIBLE`, served 10, km između 182.2 i 185.8, `validation.passed` true |
| 3.12 | scenarij s dodanim M11 (12000 kg) i N11 (L1→L3) | `OPTIMAL_PARTIAL`, 10/11, km 182.2, N11 `TOO_HEAVY` |
| 3.13 | scenarij s 13 naloga (dodaj N11–N13 lakih strojeva) | `solver` = `ortools`, `optimality` = `best_found`, nigdje riječ „optimalno" u porukama |
| 3.14 | `--solver ortools --set objective=makespan` | najveći `total_min` među kamionima ≤ 351,7 (ne oko 384,8: to bi značilo da OR-Tools mjeri samo vožnju) |
| 3.15 | `--set pinned_orders={"N04":"A"}` | km 217.0, A `["N01","N04"]` |

## QA-4 Neovisni referentni solver

| ID | Provjera | Očekivano |
|---|---|---|
| 4.1 | `uv run python qa/oracle/oracle_exact.py data/default_scenario.json` | 10/10, 182.2 km – isto kao 3.1 |
| 4.2 | isto s `--set limit_includes_handling=true` | 200.1 km – isto kao 3.2 |
| 4.3 | `uv run python qa/oracle/compare_with_app.py --seeds 30` | „Ukupno: 30 scenarija, 0 s greškom." Zabilježi najveću razliku OR-Toolsa. |
| 4.4 | `grep -rn "qa.oracle\|oracle_exact" src/` | nema pogodaka (aplikacija ne koristi referentni solver) |

## QA-5 Validator preko API-ja (mutacije)

Pokreni server (`uv run uprent serve`). Napiši `qa/out/mutations.py` koji za svaki slučaj šalje `POST /api/validate` sa zadanim scenarijem i planom (rute iz `tests/fixtures/routes.py`) i ispisuje provjere koje su pale.

| ID | Plan | Očekivano |
|---|---|---|
| 5.1 | `B_ALONE` (zadane postavke) | `passed` true |
| 5.2 | `B_ALONE` uz `limit_includes_handling=true` | pada `vrijeme` |
| 5.3 | `STRICT_B` s „D:N06 P:N10" → „P:N10 D:N06" | pada `kapacitet_kg`, detalj sadrži „13.300" |
| 5.4 | B: `P:N01 P:N02 P:N03 P:N04 D:N01 D:N02 D:N03 D:N04` | pada `mjesta` |
| 5.5 | A: `D:N03 P:N03` | pada `redoslijed` |
| 5.6 | A: `P:N03`, B: `D:N03` | padaju `isti_kamion` i `baza` |
| 5.7 | `STRICT_A` s `reported_km {"A": 26.4}` | pada `km_dosljedno` |
| 5.8 | `BOUNDARY_A` + `BOUNDARY_B` uz `limit_includes_handling=true` | pada `vrijeme` (540,4 min) |
| 5.9 | `B_ALONE` uz `require_all_trucks=true` | `passed` true; `svi_kamioni` je `info` i javlja nekorišteni kamion A |

## QA-6 API ugovor

| ID | Provjera | Očekivano |
|---|---|---|
| 6.1 | `GET /api/scenario/default` | 10 naloga, postavke jednake zadanima iz spec §6 |
| 6.2 | `POST /api/solve` zadano | 200; ključevi `status, optimality, solver, totals, trucks, unserved, validation, analysis, messages`; svaki kamion ima `steps`, zadnji korak `RETURN` (za korišteni kamion) |
| 6.3 | `POST /api/solve` s nalogom na lokaciji „L99" | 422; poruka na hrvatskom sadrži „L99" |
| 6.4 | `POST /api/compare` | 6 redaka: 182.2, 200.1, 200.1, 182.2, 284.2, 209.0 |
| 6.5 | `GET /docs` | OpenAPI stranica se učita |
| 6.6 | `analysis.alternatives` u 6.2 | dva retka, oba 200.1 |

## QA-7 Sučelje – funkcionalni scenariji

Izvedi u **Codexovom ugrađenom pregledniku**, kao stvarni korisnik. Pokreni `uv run uprent serve`, otvori `http://127.0.0.1:8000`, klikni i unosi kroz sučelje, i za svaki scenarij spremi snimku zaslona u `qa/out/screens/`. Ne zaključuj iz koda. Playwright testovi iz repozitorija (QA-2.3) su dopuna, ne zamjena. Ako ugrađeni preglednik nije dostupan, napiši Playwright skriptu u `qa/out/` i to navedi u izvještaju.

| ID | Koraci | Očekivano na ekranu |
|---|---|---|
| 7.1 | prvo otvaranje (prazna lokalna pohrana) | traka „Prvi koraci"; „182,2 km"; oznaka „Dokazano optimalno"; „Kamion A" + „nije korišten"; za B ukupno radno vrijeme „9 h 42 min"; traka „Drugo tumačenje" s „200,1 km" |
| 7.2 | klik „Primijeni" na traci drugog tumačenja | „200,1 km"; A vozi N03; prekidač „U 9 h ulazi utovar/istovar" uključen |
| 7.3 | vrati zadano; uključi „Svaki kamion mora voziti" | „200,1 km" |
| 7.4 | uključi „U 9 h ulazi utovar/istovar", utovar i istovar 21 | „217,0 km" |
| 7.5 | uz uključeno pravilo iz 7.4 i trajanje 20, dnevni limit 5 h | „8/10"; dva upozorenja s „Dokazano" |
| 7.6 | Podaci: dodaj M11 12.000 kg i N11 L1→L3 | upozorenje „N11 nije moguće izvršiti…"; „10/11" |
| 7.7 | Podaci: N01 preuzimanje promijeni u „L99" | poruka uz polje; prethodni plan i dalje vidljiv |
| 7.8 | Karta | 10 lokacija; rute u boji kamiona; prelazak mišem prikazuje korak |
| 7.9 | Vremenska crta | trake vožnje i radnji; crta limita s oznakom na što se odnosi |
| 7.10 | Analiza | redak N03 „+17,9 km"; krivulja s 14 točaka; klik na točku 284,2 → plan 284,2 km |
| 7.11 | Provjera | sve provjere zelene; usporedba s OR-Toolsom prikazana |
| 7.12 | izbornik „?" → „Vrati podatke i postavke iz zadatka" | „182,2 km" |
| 7.13 | širina 390 px | nema vodoravnog pomicanja; postavke iza gumba „Postavke"; tablica koraka čitljiva |
| 7.14 | konzola preglednika tijekom svih scenarija 7.1–7.13 | nema JavaScript grešaka ni upozorenja Reacta |
| 7.15 | mrežni zahtjevi tijekom 7.1–7.13 | nema neočekivanih odgovora 4xx/5xx (jedini očekivani je 422 u 7.7); svaki odgovor `/api/solve` stiže prije sljedeće promjene ili je stari odbačen |
| 7.16 | brzo uzastopno mijenjanje postavki (5 promjena u 2 s) | na kraju prikazan rezultat zadnje promjene, bez treperenja starog rezultata |

## QA-8 Upute u sučelju i UX

| ID | Provjera | Očekivano |
|---|---|---|
| 8.1 | svaka postavka ima ⓘ | da; tekst odgovara spec §6 (brojke 182,2 i 200,1 kod tumačenja limita) |
| 8.2 | upute ne iskaču same i ne blokiraju rad | nema modala osim na izričit klik |
| 8.3 | dosljedan stil uputa (ista komponenta, ikona, prigušena boja) | da, na svim karticama |
| 8.4 | svaka kartica ima jednoredni opis | da |
| 8.5 | status ima objašnjenje (prelazak mišem ili ⓘ) | „Dokazano optimalno: …" |
| 8.6 | prazno stanje (obriši sve naloge) | „Nema naloga. Dodaj nalog ili vrati podatke iz zadatka." |
| 8.7 | tipkovnica: Tab dolazi do ⓘ, Enter otvara, Esc zatvara | da |
| 8.8 | boja nikad nije jedini nositelj značenja | uz boju uvijek ikona ili tekst |
| 8.9 | hrvatski format brojeva svugdje | „9.400 kg", „182,2 km", „9 h 42 min" |
| 8.10 | test bez uputa u ugrađenom pregledniku, bez gledanja koda i dokumentacije: zadaci „izračunaj plan, primijeni drugo tumačenje, dodaj nalog, pronađi zašto A ne vozi, prikaži plan s N04 na A" | sve izvedivo; zapiši broj klikova i svako mjesto zastoja |

## QA-9 Dokumentacija

| ID | Provjera | Očekivano |
|---|---|---|
| 9.1 | pokreni doslovno svaku naredbu iz `README.md` | sve rade |
| 9.2 | pokreni doslovno svaku naredbu iz `docs/upute.md` | sve rade |
| 9.3 | brojke u dokumentima jednake izlazu aplikacije | da |
| 9.4 | postoje `docs/LOGIKA.md`, `PRETPOSTAVKE.md`, `AI_ALATI.md`, `VRIJEME.md`, `deploy.md` | da |
| 9.5 | `VRIJEME.md` ne sadrži izmišljene sate | stupac sati prazan ili ga je popunio kandidat |
| 9.6 | svaka stavka predaje iz točke 8 zadatka ima svoje mjesto (spec §16) | da |

## QA-10 Performanse

| ID | Provjera | Očekivano |
|---|---|---|
| 10.1 | `POST /api/solve` zadano, 5 mjerenja | medijan < 1 s |
| 10.2 | slučajni scenarij s 12 naloga, `--solver exact` | < 5 s |
| 10.3 | slučajni scenarij s 40 naloga i 4 kamiona, `--solver ortools` | ≤ limit pretrage + 1 s; plan prolazi validator |
| 10.4 | sučelje tijekom računanja 10.3 | prikazuje „Računam…", ostaje upotrebljivo |

## QA-11 Robusnost ulaza

| ID | Ulaz | Očekivano |
|---|---|---|
| 11.1 | nula naloga | plan 0 km, bez pada, poruka praznog stanja |
| 11.2 | svi strojevi teži od 10.000 kg | 0/N, svaki nalog `TOO_HEAVY` |
| 11.3 | isti stroj u dva naloga | greška ulaza s porukom |
| 11.4 | isto mjesto utovara i istovara | greška ulaza s porukom |
| 11.5 | brzina 0, limit 0, negativno trajanje radnje | greška ulaza s porukom |
| 11.6 | dvije lokacije s istim koordinatama | plan bez pada; dionica 0 km; radnje se računaju |
| 11.7 | koordinate ±10.000 km | plan ili jasna poruka, bez pada |
| 11.8 | uvoz JSON-a bez `settings` | primijenjene zadane postavke |
| 11.9 | uvoz neispravnog JSON-a | poruka, postojeći scenarij ostaje |
| 11.10 | `require_all_trucks` uz samo jedan nalog | plan s jednim kamionom i upozorenje da pravilo nije moguće ispuniti |
| 11.11 | prazan popis kamiona | greška ulaza s porukom (bez pada predprovjere) |
| 11.12 | `depot` koji nije među lokacijama | greška ulaza s porukom |
| 11.13 | `day_start` „7h" | greška ulaza s porukom |
| 11.14 | `ortools_time_limit_s` 0 ili 31 | greška ulaza s porukom |
| 11.15 | `pinned_orders` `{"N06":"A"}` | greška ulaza s „3.500 kg" |
| 11.16 | kamion s 12 mjesta i 12 naloga od 800 kg | egzaktni se prekida, plan dolazi od OR-Toolsa, poruka „prekinut"; bez pada i bez čekanja duljeg od 8 s + limit OR-Toolsa |

## QA-12 Repozitorij i integritet

| ID | Provjera | Očekivano |
|---|---|---|
| 12.1 | `sha256sum originalni-zadatak.md` | `dc7fb375abf4b77d7e732b4ed15350da0fe44edac39862375725162e3dd28e91` |
| 12.2 | `git ls-files priprema` | prazno |
| 12.3 | `git ls-files` ne sadrži `.env`, `.dev.vars`, ključeve ni tokene | da |
| 12.4 | `git status` nakon QA | čisto (osim `qa/out/`, koji je u `.gitignore`) |
| 12.5 | `git ls-files originalni-zadatak.md` i `git log --all -- originalni-zadatak.md` | oba prazna (tekst zadatka nikad nije commitan) |
| 12.6 | `git log origin/main..HEAD` i `gh run list --limit 3` | nema nepushanih commitova; zadnji CI je zelen |
| 12.7 | `git log --oneline --reverse` | povijest čitljivo pokazuje razvoj: dokumenti → testovi → kod; poruke su smislene; nema prepisane povijesti |
| 12.8 | `gh repo view --json visibility` | `PRIVATE` (javnim ga čini vlasnik pri predaji) |

## QA-13 Docker i javni demo

| ID | Provjera | Očekivano |
|---|---|---|
| 13.1 | `docker build -t uprent-planner .` | uspjeh |
| 13.2 | `docker run --rm -p 8000:8000 uprent-planner` + `curl …/api/health` | `{"status":"ok"}` |
| 13.3 | javni URL (ako je objavljen), u ugrađenom pregledniku: `/api/health`, zadani plan, scenariji 7.1, 7.2 i 7.6 | ok; 182,2 km; ponašanje isto kao lokalno |
| 13.4 | prvi zahtjev nakon mirovanja kontejnera | odgovor unutar 30 s; zabilježi vrijeme |

## QA-14 Sljedivost zahtjeva iz zadatka

| Zahtjev zadatka | Provjereno u |
|---|---|
| 5.1 prikaz i pregled ulaznih podataka | 7.6, 7.7, 1.3 |
| 5.2 automatska raspodjela na kamione | 3.1–3.3 |
| 5.3 redoslijed obilaska | 6.2, 7.1 |
| 5.4 nosivost i broj strojeva u svakom trenutku | 5.3, 5.4, 2.1 |
| 5.5 utovar prije istovara, isti kamion | 5.5, 5.6 |
| 5.6 što učinkovitiji raspored | 3.1, 4.3 |
| 5.7 km po kamionu i ukupno | 6.2, 7.1 |
| 5.8 jasno upozorenje za neizvedive naloge | 3.8, 3.12, 7.5, 7.6 |
| 6 prikaz po kamionu (lokacije, radnje, teret nakon radnje, km, broj naloga) | 7.1 |
| 8 predaja (kod, upute, demo, logika, testovi, AI osvrt, vrijeme) | 9.1–9.6, 13.3 |
| 9 h, 20 min, 60 km/h, povratak u bazu | 3.2, 3.4, 5.2, 6.2 |

---

## Predložak izvještaja (`docs/razvoj/qa-izvjestaj.md`)

```markdown
# QA izvještaj

Datum: … · Commit: … · Izvršio: Codex · Okruženje: OS, uv, Python, Node

## Sažetak
PASS: … · FAIL: … · BLOCKED: …
Konačna ocjena: SPREMNO / NIJE SPREMNO (razlog)

## Rezultati
| ID | Ishod | Dokaz (isječak ili putanja do snimke) |
|---|---|---|

## Nalazi
| ID nalaza | QA ID | Ozbiljnost (blokira / važno / manje) | Koraci | Očekivano | Dobiveno |
|---|---|---|---|---|---|

## Ispravci nakon prvog prolaza
| ID nalaza | Commit | Ponovljeni QA ID-evi | Ishod |
|---|---|---|---|

## Napomene za neovisni pregled (Claude)
Što QA nije mogao provjeriti ili gdje nije siguran.
```
