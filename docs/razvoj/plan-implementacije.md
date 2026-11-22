# UP RENT Smart Logistics Planner – plan implementacije

> **Za izvršitelja (Codex):** radi zadatak po zadatak, redom. Koraci koriste checkbox sintaksu (`- [ ]`) – označi ih kad su gotovi. Ne prelazi na sljedeći zadatak dok testovi trenutnog ne prolaze. Ako se specifikacija i ovaj plan razilaze, vrijedi specifikacija; ako se specifikacija i `originalni-zadatak.md` razilaze, stani i zapiši to u `docs/razvoj/odstupanja.md`.

**Cilj:** web-aplikacija koja naloge raspoređuje na kamione s dokazanim optimumom, objašnjava plan i provjerava ga neovisnim validatorom.

**Arhitektura:** Python jezgra (`src/uprent`) s egzaktnim solverom, OR-Tools solverom i neovisnim validatorom; FastAPI izlaže API i poslužuje izgrađeno React sučelje (`web/dist`). Solveri vraćaju samo nizove radnji; sve prikazane brojke računa validator.

**Tehnologije:** Python 3.11, uv, Pydantic v2, OR-Tools 9.15, FastAPI, pytest, hypothesis; React 18, TypeScript, Vite, Tailwind CSS, lucide-react, Vitest, Testing Library, Playwright; Docker; Cloudflare Containers.

**Specifikacija:** `docs/razvoj/specifikacija.md` (čitaj je uz ovaj plan). QA nakon implementacije: `docs/razvoj/qa-plan.md`.

## Globalna ograničenja

- Python `3.11` (`.python-version`), upravljanje preko `uv`; `ortools` u rasponu `>=9.15,<9.16`.
- Zadane postavke (doslovno tumačenje): `day_limit_min=540`, `limit_includes_handling=false`, `load_min=20`, `unload_min=20`, `require_all_trucks=false`, `allow_partial=true`, `objective="km"`, `solver="auto"`, `ortools_time_limit_s=3`, `compare_with_ortools=true`, `day_start="07:00"`, `exact_max_orders=12`, `exact_max_trucks=3`.
- Udaljenost: euklidska, svaka dionica zaokružena na 0,1 km polovicom prema gore (`Decimal`, `ROUND_HALF_UP`), interno cijele desetinke km.
- Vrijeme: točno (`Fraction` sekundi); vožnja = desetinke × 360 / brzina_kmh sekundi; usporedba s limitom `<=`.
- Leksikografski cilj: najviše izvršenih naloga → (ako `require_all_trucks`) najviše korištenih kamiona → odabrani cilj → km.
- Validator: tvrde provjere daju `INVALID_PLAN`; `svi_kamioni` je samo informativna (`severity="info"`).
- `pinned_orders: {nalog: kamion}`: prikvačeni nalog smije samo na taj kamion, ostali su slobodni. Polje `fixed_assignment` ne postoji.
- Egzaktni solver: prekid kod 1.000.000 stanja ili 8 s → OR-Tools uz poruku koja sadrži „prekinut".
- OR-Tools: dvije vremenske dimenzije, `limit_time` (za limit) i `work_time` (uvijek vožnja + radnje; za redoslijed i `makespan`), obje s `fix_start_cumul_to_zero=True`.
- `originalni-zadatak.md` je u `.gitignore`: čitaj ga, ali ga nikad ne commitaj.
- `validator.py` ne uvozi ništa iz `uprent.solvers` ni `uprent.distance`.
- OR-Tools: nikad `AddDisjunction([p, d], …)`; nikad tvrdo `NextVar(Start(v)) != End(v)`.
- Oznaka „optimalno" samo uz `optimality == "proven"` (egzaktni solver).
- Sav tekst za korisnika na hrvatskom; brojke u hrvatskom formatu (182,2 km; 9.400 kg; 9 h 42 min). Identifikatori u kodu na engleskom.
- `qa/oracle/` i `data/default_scenario.json` već postoje; aplikacija ne uvozi `qa/`. Format scenarija ne mijenjati bez ažuriranja `qa/oracle/`.
- `originalni-zadatak.md` i `priprema/` se ne mijenjaju.
- Git: povijest commitova je dio predaje jer pokazuje proces razvoja.
  - Commitaj često i smisleno. Gdje je prirodno, prvo commitaj testove koji padaju (`test: …`), pa implementaciju (`feat: …`).
  - `git push` nakon svakog zadatka.
  - Povijest se nikad ne prepisuje: bez `--force` i bez `rebase` već pushanih commitova.
  - Repozitorij ostaje privatan; javnim ga čini vlasnik pri predaji.

## Fokus pregleda (rizici koje testovi inače ne bi pokrili)

1. **Neispravan unos usred rada** (npr. obrisana lokacija koju nalog koristi): poruka uz polje, zadnji valjani rezultat ostaje vidljiv. Test: Zadatak 13 `invalid edit keeps last result`.
2. **Brze uzastopne promjene postavki**: stariji odgovor ne smije prebrisati noviji. Test: Zadatak 14 `ignores stale responses`.
3. **Dugo računanje** (OR-Tools do 30 s, egzaktni na 12 naloga): sučelje pokazuje da računa i ostaje upotrebljivo; API računa izvan event loopa. Testovi: Zadatak 11 `solve runs in threadpool`, Zadatak 14 `shows computing state`.
4. **Lokacije s istim koordinatama**: dionica 0 km, radnje se i dalje računaju. Testovi: Zadatak 2 `test_identical_coordinates_zero`, Zadatak 3 `test_zero_leg_handling_counted`.
5. **Decimalni zarez** („20,5" u postavkama): prihvaća se kao 20,5 ili jasno odbija. Test: Zadatak 12 `parseHrNumber`.

---

### Zadatak 1: Kostur projekta i domenski modeli

**Datoteke:**
- Kreiraj: `pyproject.toml`, `.python-version`, `src/uprent/__init__.py`, `src/uprent/domain.py`, `tests/test_domain.py`, `tests/conftest.py`
- Postoji: `data/default_scenario.json`, `.gitignore`

**Sučelja:**
- Proizvodi: `Location(id: str, x: float, y: float, name: str | None)`, `Machine(id: str, weight_kg: int)`, `Truck(id: str, name: str | None, capacity_kg: int, slots: int, speed_kmh: float = 60)`, `Order(id: str, machine: str, pickup: str, delivery: str, load_min: float | None = None, unload_min: float | None = None)`, `Settings` (ključevi i zadano iz Globalnih ograničenja, plus `pinned_orders: dict[str, str] | None = None`), `Scenario(name: str, depot: str, locations, machines, trucks, orders, settings: Settings)`; `load_scenario(path: str | Path) -> Scenario`; `apply_overrides(scenario: Scenario, overrides: dict[str, object]) -> Scenario`; `Scenario.handling_seconds(order_id: str) -> tuple[int, int]`.
- `ScenarioError(ValueError)` s porukom na hrvatskom koja imenuje polje.

- [x] **Korak 0:** pripremi repozitorij:
  1. `git init`;
  2. provjeri da `git status` ne prikazuje `originalni-zadatak.md` ni `priprema/`;
  3. prvi commit, samo s postojećim dokumentima (`docs/`, `prompts/`, `qa/`, `data/`, `README.md`, `.gitignore`), poruka `docs: specification, implementation plan and QA plan`;
  4. `gh repo create uprent-smart-logistics-planner --private --source . --remote origin --push` (`gh` je već prijavljen).
- [x] **Korak 1:** `uv init --package --name uprent --python 3.11` (ili ručno `pyproject.toml` sa `[project.scripts] uprent = "uprent.cli:main"`); `uv add fastapi uvicorn pydantic "ortools>=9.15,<9.16"`; `uv add --dev pytest httpx hypothesis`. `uv init` ne smije prepisati postojeći `README.md` ni `.gitignore`; ako bi, napravi `pyproject.toml` ručno.
- [x] **Korak 2: Napiši testove koji padaju** (`tests/test_domain.py`):
  - `test_default_scenario_loads`: 10 lokacija, 10 strojeva, 2 kamiona, 10 naloga; `settings.limit_includes_handling is False`, `settings.require_all_trucks is False`, `settings.load_min == 20`.
  - `test_missing_settings_use_defaults`: scenarij bez ključa `settings` → `Settings()` zadane vrijednosti.
  - `test_rejects_unknown_location`: `pickup="L99"` → `ScenarioError` s „nepoznata lokacija" i „N01".
  - `test_rejects_same_pickup_and_delivery` → poruka sadrži „isto mjesto".
  - `test_rejects_machine_in_two_orders` → poruka sadrži „M01" i „dva naloga".
  - `test_rejects_duplicate_ids`, `test_rejects_nonpositive_speed`, `test_rejects_zero_slots`, `test_rejects_negative_handling`.
  - `test_apply_overrides_parses_types`: `{"limit_includes_handling": "true", "load_min": "10"}` → `True`, `10.0`.
  - `test_apply_overrides_json`: `{"pinned_orders": "{\"N04\": \"A\"}"}` → `{"N04": "A"}`; vrijednosti koje počinju s `{` ili `[` čitaju se kao JSON.
  - `test_rejects_empty_trucks`, `test_rejects_unknown_depot`, `test_rejects_bad_day_start` („7h"), `test_rejects_bad_ortools_limit` (0 i 31).
  - `test_pinned_validation`: nepoznati nalog ili kamion → greška; `{"N06": "A"}` → poruka sadrži „N06" i „3.500 kg".
- [x] **Korak 3:** `uv run pytest tests/test_domain.py -q` → očekuj FAIL (nema modula).
- [x] **Korak 4:** implementiraj `domain.py` (Pydantic `model_validator(mode="after")` za međusobne reference).
- [x] **Korak 5:** `uv run pytest tests/test_domain.py -q` → PASS.
- [x] **Korak 6:** dodaj `.github/workflows/ci.yml`: na svaki push i PR pokreće `astral-sh/setup-uv`, `uv sync` i `uv run pytest -q`. Commitovi `feat: domain models and default scenario` i `ci: run tests on push`; zatim `git push` i provjera da je CI zelen (`gh run list --limit 1`).

### Zadatak 2: Udaljenost i vrijeme

**Datoteke:** kreiraj `src/uprent/distance.py`, `tests/test_distance.py`

**Sučelja:**
- Proizvodi: `leg_tenths(a: Location, b: Location) -> int`; `drive_seconds(tenths: int, speed_kmh: float) -> Fraction`; `distance_matrix(scenario: Scenario) -> dict[tuple[str, str], int]`.

- [x] **Korak 1: Testovi:**
  - `test_task_legs`: L0→L9 == 94, L9→L4 == 170, L4→L0 == 108 (zbroj 372 = 37,2 km).
  - `test_half_up`: točke (0,0) i (0.05,0) → 1 (0,05 km → 0,1 km).
  - `test_identical_coordinates_zero`: dvije lokacije s istim (x, y) → 0.
  - `test_drive_seconds`: `drive_seconds(94, 60) == 564`; `drive_seconds(1822, 60) == 10932`.
- [x] **Korak 2:** pokreni → FAIL. **Korak 3:** implementiraj (`Decimal(...).sqrt()`, `quantize(Decimal("1"), ROUND_HALF_UP)` nad km×10). **Korak 4:** → PASS. **Korak 5:** commit `feat: distance and time`.

### Zadatak 3: Plan i neovisni validator

**Datoteke:** kreiraj `src/uprent/plan.py`, `src/uprent/validator.py`, `tests/fixtures/routes.py`, `tests/test_validator.py`

**Sučelja:**
- Proizvodi: `Op = tuple[Literal["PICKUP", "DELIVERY"], str]`; `Plan(routes: dict[str, list[Op]], reported_km: dict[str, float] | None = None, reported_unserved: list[str] | None = None)`. Lokacije i strojevi nisu dio plana; validator ih izvodi iz naloga.
- `validate(scenario: Scenario, plan: Plan) -> ValidationReport`, gdje je `ValidationReport(passed: bool, checks: list[Check], trucks: list[TruckView], total_km: float, served: list[str], unserved: list[str])`, `Check(rule: str, passed: bool, detail: str, severity: Literal["hard", "info"])` (`passed` u `ValidationReport` gleda samo `hard`), `TruckView(id, name, used, km, drive_min, handling_min, total_min, limit_min, limit_basis, slack_min, peak_kg, capacity_kg, peak_slots, slots, orders, steps: list[StepView])`, `StepView(seq, location, action: "PICKUP"|"DELIVERY"|"RETURN", order, machine, leg_km, cum_km, arrive, depart, load_kg, load_slots, onboard)`.
- Imena provjera (točno): `baza`, `kapacitet_kg`, `mjesta`, `redoslijed`, `isti_kamion`, `jednom`, `vrijeme`, `km_dosljedno`, `neizvrseni_dosljedno`, `svi_kamioni`.

Fiksne rute (`tests/fixtures/routes.py`; `P:` = PICKUP, `D:` = DELIVERY):
- `B_ALONE` (zadano, 182,2 km): `P:N08 P:N03 D:N08 P:N09 D:N09 P:N01 P:N05 D:N03 D:N05 P:N07 P:N02 D:N07 D:N01 D:N02 P:N06 D:N06 P:N10 D:N10 P:N04 D:N04`
- `STRICT_A` (37,2 km): `P:N03 D:N03`
- `STRICT_B` (162,9 km): `P:N05 P:N01 P:N02 D:N05 P:N07 D:N07 D:N01 D:N02 P:N06 D:N06 P:N10 D:N10 P:N04 P:N08 D:N08 P:N09 D:N09 D:N04`
- `BOUNDARY_A` (38,4 km): `P:N04 D:N04`
- `BOUNDARY_B` (180,4 km): `P:N05 P:N01 P:N02 D:N05 P:N07 D:N07 D:N01 D:N02 P:N06 D:N06 P:N10 D:N10 P:N08 P:N03 D:N08 P:N09 D:N09 D:N03`

- [x] **Korak 1: Testovi:**
  - `test_b_alone_valid_by_default`: `passed`; B: km 182,2, `drive_min` 182,2, `handling_min` 400, `total_min` 582,2, `peak_kg` 9400, `peak_slots` 3, 21 korak (zadnji `RETURN`); A: `used is False`, km 0.
  - `test_b_alone_invalid_when_handling_counts`: uz `limit_includes_handling=True` provjera `vrijeme` pada, `detail` sadrži „582,2".
  - `test_strict_plan_valid`: `STRICT_A`+`STRICT_B` uz `limit_includes_handling=True` → `passed`, ukupno 200,1; B `total_min` 522,9, `peak_kg` 9900; A `total_min` 77,2.
  - `test_boundary_plan`: `BOUNDARY_A`+`BOUNDARY_B` → prolazi zadano; uz `limit_includes_handling=True` pada `vrijeme` (540,4).
  - `test_capacity_l7_swap`: `STRICT_B` s „D:N06 P:N10" zamijenjenim u „P:N10 D:N06" → `kapacitet_kg` pada, `detail` sadrži „13.300".
  - `test_exact_capacity_allowed`: B = `P:N06 P:N08 D:N06 D:N08` → `kapacitet_kg` prolazi (10.000 kg).
  - `test_slots_exceeded`: B = `P:N01 P:N02 P:N03 P:N04 D:N01 D:N02 D:N03 D:N04` → `mjesta` pada („4 / 3").
  - `test_delivery_before_pickup` (`D:N03 P:N03` → `redoslijed`), `test_other_truck_delivers` (A `P:N03`, B `D:N03` → `isti_kamion` i `baza`), `test_double_pickup` (→ `jednom`), `test_machine_left_on_truck` (A `P:N03` → `baza`).
  - `test_reported_km_without_return`: `reported_km={"A": 26.4}` za `STRICT_A` → `km_dosljedno` pada.
  - `test_zero_leg_handling_counted`: dvije lokacije s istim koordinatama → dionica 0 km, a `handling_min` i dalje 40 za jedan nalog.
  - `test_unused_truck_is_info`: `B_ALONE` uz `require_all_trucks=True` → `passed` true; `svi_kamioni` ima `severity == "info"` i `passed is False`.
  - `test_reported_unserved_mismatch`: `STRICT_A`+`STRICT_B` s `reported_unserved=["N05"]` → `neizvrseni_dosljedno` pada; bez polja → „nije primjenjivo".
  - `test_validator_does_not_import_solvers`: čitaj izvor `validator.py`; ne smije sadržavati „uprent.solvers" ni „uprent.distance".
- [x] **Korak 2:** → FAIL. **Korak 3:** implementiraj; satnica iz `settings.day_start`; minute zaokruži na 0,1 samo za prikaz. **Korak 4:** → PASS. **Korak 5:** commit `feat: independent validator`.

### Zadatak 4: Predprovjera naloga

**Datoteke:** kreiraj `src/uprent/precheck.py`, `tests/test_precheck.py`

**Sučelja:** `Reason(order: str, code: Literal["TOO_HEAVY","TOO_LONG_ALONE","DOES_NOT_FIT_TOGETHER","NOT_FOUND"], message: str)`; `precheck(scenario: Scenario) -> dict[str, Reason]` (samo prva dva koda); `eligible_trucks(scenario: Scenario, order_id: str) -> list[str]`; `min_route_tenths(scenario: Scenario, order_id: str) -> int` vraća donju granicu iz spec §11: sp(baza, utovar) + sp(utovar, istovar) + sp(istovar, baza), gdje su sp najkraći putovi (Floyd–Warshall) u grafu zaokruženih dionica između baze i svih lokacija utovara i istovara. `TOO_LONG_ALONE` se dodjeljuje samo kad ta granica, pretvorena u vrijeme (uz radnje ako ulaze u limit), prelazi limit na svakom dopuštenom kamionu.

- [x] **Korak 1: Testovi:**
  - `test_too_heavy`: dodan M11 12000 kg i N11 L1→L3 → `TOO_HEAVY`, poruka == „N11 nije moguće izvršiti: stroj M11 teži 12.000 kg, a najveća nosivost kamiona je 10.000 kg."
  - `test_too_long_alone_drive`: `day_limit_min=60` → N06 ima `TOO_LONG_ALONE` (60,2 min vožnje), N09 nema (34,5).
  - `test_too_long_alone_with_handling`: `limit_includes_handling=True`, `day_limit_min=90` → N06 `TOO_LONG_ALONE` (100,2 min).
  - `test_eligible_trucks`: N10 → `["B"]`; N01 → `["A", "B"]`.
  - `test_too_long_alone_pinned`: A brzine 30 km/h, `day_limit_min=60`, `pinned_orders={"N04": "A"}` → N04 `TOO_LONG_ALONE` (76,8 min vožnje na A), iako bi na B stao (38,4 min).
  - `test_min_route_task_data`: `min_route_tenths` za N06, N09 i N04 iznosi 602, 345 i 384.
  - `test_rounding_shortcut_not_excluded` (scenarij iz spec §15, test 27): `min_route_tenths(N01) == 112`; N01 nije u rezultatu predprovjere, iako mu je samostalna ruta 11,4 km.
- [x] **Korak 2–5:** FAIL → implementacija → PASS → commit `feat: order precheck`.

### Zadatak 5: Egzaktni solver – tablice po kamionu

**Datoteke:** kreiraj `src/uprent/solvers/__init__.py`, `src/uprent/solvers/base.py`, `src/uprent/solvers/exact.py`, `tests/test_exact_tables.py`

**Sučelja:**
- `base.py`: `SolverOutput(plan: Plan, served: frozenset[str], optimality: Literal["proven","best_found","none"], solver: Literal["exact","ortools"], status: str, info: dict)`.
- `exact.py`: `TableEntry(km_tenths: int, ops: list[Op])`; `truck_table(scenario: Scenario, truck: Truck, order_ids: list[str]) -> tuple[dict[frozenset[str], TableEntry], int]` (drugi element = broj stanja); `ExactContext(tables: dict[str, dict[frozenset[str], TableEntry]], states: int)`; `build_context(scenario: Scenario, order_ids: list[str]) -> ExactContext`. `truck_table` prima i `max_states: int = 1_000_000` i `deadline_s: float = 8.0` te baca `StateLimitExceeded` kad ih pređe. `pinned_orders` se primjenjuje u kombiniranju (Zadatak 6), a ne u tablici.

Algoritam (DP nad stanjima, jer ga signatura ne određuje):

```python
# stanje = (preuzeti: frozenset|bitmaska, isporučeni, lokacija); vrijednost = (km, prethodno_stanje, radnja, teret_kg, broj_strojeva)
# sloj po sloj (svaki sloj = jedna radnja više); utovar samo ako teret+w <= nosivost i broj+1 <= mjesta; istovar samo ukrcanog
# zadrži manji km za isto stanje; završno stanje: preuzeti == isporučeni -> km + dionica(lokacija, baza)
```

- [x] **Korak 1: Testovi:** `test_table_sizes` (A 32 podskupa, B 1024); `test_state_count` (A 281 + B 65.281 = 65.562, uključujući početno stanje u bazi; stanje = (preuzeti, isporučeni, lokacija zadnje radnje)); `test_b_all_km` (B, svih 10 → 1822); `test_a_n03_km` (A, {N03} → 372); `test_b_without_n03_km` (1629); `test_empty_subset_zero` (∅ → 0 km); `test_shared_table_same_type` (dva kamiona istog tipa → isti objekt tablice); `test_state_cap_raises` (kamion s 12 mjesta i 12 naloga od 800 kg, `max_states=10_000` → `StateLimitExceeded`).
- [x] **Korak 2–5:** FAIL → implementacija (kamioni istog `(capacity_kg, slots)` dijele tablicu) → PASS → commit `feat: exact per-truck tables`.

### Zadatak 6: Egzaktni solver – kombiniranje i postavke

**Datoteke:** izmijeni `src/uprent/solvers/exact.py`; kreiraj `tests/test_exact_solve.py`

**Sučelja:** `solve_exact(scenario: Scenario, order_ids: list[str] | None = None, ctx: ExactContext | None = None) -> SolverOutput`; `feasible_entry(scenario, truck, subset, entry) -> bool`; `full_plan_assignments(scenario, ctx) -> list[Assignment]` (za krivulju i `makespan`), `Assignment(by_truck: dict[str, frozenset[str]], km_tenths: int, end_seconds: Fraction)`.

- [x] **Korak 1: Testovi** (svi na zadanom scenariju, `apply_overrides` za postavke):
  - `test_default_literal`: 182,2 km, 10/10, A prazan, `optimality == "proven"`.
  - `test_handling_counts`: `limit_includes_handling=True` → 200,1, A = {N03}.
  - `test_require_all_trucks`: → 200,1.
  - `test_handling_time_drive_mode` (`load/unload` 0 i 30) → 182,2.
  - `test_handling_time_strict` (uz `limit_includes_handling=True`): 17 → 182,2; 20 → 200,1; 21 → 217,0; 25 → 235,1; 30 → 254,9; 10+10 → 182,2.
  - `test_drive_limit`: 180 → 200,1; 150 → 239,2; 140 → 9 izvršenih; 100 → 7.
  - `test_strict_day_limit`: 480 → 235,1; 330 → 9; 300 → 8 i 203,8 km; 345 → 10 i 284,2.
  - `test_no_partial`: `allow_partial=False`, strogo, 300 → `status == "NO_FULL_PLAN"`.
  - `test_makespan`: `objective="makespan"` → 284,2 km, kraj posljednjeg kamiona 344,8 min.
  - `test_pinned_single`: `pinned_orders={"N04": "A"}` → 217,0 km, A vozi N01 i N04.
  - `test_pinned_all`: N04 na A, ostalih 9 na B → 218,8 km.
  - `test_pinned_too_heavy`: `{"N06": "A"}` → `ScenarioError`.
  - `test_pinned_not_forced`: isti ulaz kao `test_too_long_alone_pinned` → plan postoji, N04 neizvršen, status `OPTIMAL_PARTIAL`, nema pada.
  - `test_makespan_require_all_trucks`: dodan kamion C (10.000 kg, 3 mjesta, 10 km/h), `objective="makespan"`, `require_all_trucks=True` → C ima barem jedan nalog.
  - `test_makespan_three_trucks_fast`: 12 slučajnih naloga, 3 kamiona, `objective="makespan"` → gotovo za manje od 10 s.
  - `test_single_slot`: oba kamiona `slots=1` → 209,0; uz `limit_includes_handling=True` → 226,0.
  - `test_zero_orders`: prazan popis naloga → 0 km, `status == "OPTIMAL"`.
  - `test_slots_only_truck_a` (Geminijev slučaj): flota samo A, četiri stroja od 800 kg, nalozi L1→L3 → 4/4 izvršeno; validator: A nikad više od 2 stroja.
- [x] **Korak 2:** → FAIL. **Korak 3:** implementiraj DP po podskupovima (spec §9.1), provjeru vremena po kamionu, leksikografski ključ i `makespan` u tri DP koraka iz spec §9.1 (bez nabrajanja raspodjela); `pinned_orders` se primjenjuje u kombiniranju (kamion ne smije uzeti nalog prikvačen na drugi kamion; prikvačeni nalog nije obvezan ako ne stane); kod `makespan` uz `require_all_trucks` ključevi su (−korišteni kamioni, M) i (−korišteni kamioni, km). **Korak 4:** → PASS. **Korak 5:** commit `feat: exact solver combination`.

### Zadatak 7: OR-Tools solver

**Datoteke:** kreiraj `src/uprent/solvers/ortools_solver.py`, `tests/test_ortools.py`

**Sučelja:** `solve_ortools(scenario: Scenario, order_ids: list[str], time_limit_s: float) -> SolverOutput` (`optimality="best_found"`; status `FEASIBLE`, `FEASIBLE_PARTIAL` ili `NOT_FOUND`).

- [ ] **Korak 1: Testovi** (svaki plan mora proći `validate`):
  - `test_default_close_to_optimum`: zadano → 10 izvršenih, km između 182,2 i 185,8 (≤ 2 % iznad).
  - `test_strict_close_to_optimum`: `limit_includes_handling=True` → 10 izvršenih, km između 200,1 i 204,1.
  - `test_too_heavy_does_not_crash`: N11 12.000 kg → proces ne pada, N11 izostavljen, validator prolazi.
  - `test_require_all_trucks_soft`: oba kamiona korištena.
  - `test_partial_strict_300`: ≤ 8 izvršenih, validator prolazi.
  - `test_makespan_counts_handling`: `objective="makespan"`, zadano (radnje ne ulaze u limit) → najveći `total_min` po validatoru ≤ 351,7 (a ne oko 384,8).
  - `test_pinned_ortools`: `{"N04": "A"}` → N04 u ruti A; validator prolazi.
  - `test_slow_truck_capacity`: A brzine 30 km/h, `objective="makespan"` → plan postoji i prolazi validator (W_max računat po najnižoj brzini).
  - `test_limit_capacity_floor`: `limit_capacity_seconds(60.01) == 3600` i `limit_capacity_seconds(540) == 32400`.
  - `test_no_forbidden_patterns`: izvor datoteke ne sadrži regex `AddDisjunction\(\[[^\]]*,[^\]]*\]` ni `NextVar\(.*Start.*\)\s*!=`.
- [ ] **Korak 2–5:** FAIL → implementacija prema spec §9.2 (kazne, dimenzije `kg`, `slots`, `limit_time` i `work_time`, `ceil` sekundi, `SetAllowedVehiclesForIndex` za prikvačene naloge) → PASS → commit `feat: ortools solver`.

### Zadatak 8: Servis, auto izbor i SolveResult

**Datoteke:** kreiraj `src/uprent/solvers/auto.py`, `src/uprent/result.py`, `src/uprent/service.py`, `tests/test_service.py`

**Sučelja:** `choose_solver(scenario: Scenario, n_orders: int) -> Literal["exact","ortools"]`; `SolveResult` (spec §8; `comparison` uvijek `null` – usporedbu radi sučelje drugim pozivom); `solve(scenario: Scenario, solver_override: str | None = None) -> SolveResult`.

Tok `solve`: provjera ulaza → `precheck` → izvedivi nalozi → izbor solvera → solver → `validate` → status (`INVALID_PLAN` ako validator padne) → razlozi neizvršenih (`DOES_NOT_FIT_TOGETHER` uz egzaktni, `NOT_FOUND` uz OR-Tools) → analiza (Zadatak 9) → `SolveResult`.

- [ ] **Korak 1: Testovi:** `test_default_result` (status `OPTIMAL`, `solver == "exact"`, `totals.km == 182.2`, A `used is False`); `test_n11_partial` (`OPTIMAL_PARTIAL`, 10/11, 182,2 km, N11 `TOO_HEAVY`); `test_thirteen_orders_uses_ortools` (13 naloga → `solver == "ortools"`, `optimality == "best_found"`, nijedna poruka ne sadrži „optimal"); `test_all_too_heavy` (0/N, svaki `TOO_HEAVY`, bez pada); `test_rounding_shortcut_full_plan` (scenarij iz spec §15, test 27, uz `allow_partial=False` → `OPTIMAL`, 2/2, 11,3 km, a ne `NO_FULL_PLAN`); `test_invalid_plan_detected` (monkeypatch solvera da vrati plan s dvostrukim utovarom → `INVALID_PLAN`, `validation.passed is False`); `test_state_cap_fallback` (monkeypatch `max_states=10` → `solver == "ortools"`, poruka sadrži „prekinut"); `test_analysis_after_fallback` (nakon prelaska na OR-Tools `analysis.why`, `curve` i `alternatives` su prazni, a `binding` sadrži napomenu da trebaju egzaktni solver); `test_zero_served_status` (svi nalozi preteški, `allow_partial=True` → `OPTIMAL_PARTIAL` i poruka „Nijedan nalog nije moguće izvršiti."); `test_unused_truck_not_invalid` (`require_all_trucks=True`, monkeypatch solvera da vrati „B sam" → status nije `INVALID_PLAN`, a postoji poruka o nekorištenom kamionu); `test_does_not_fit_message` (strogo, 300 min → poruka sadrži „Dokazano" i „8 od 10").
- [ ] **Korak 2–5:** FAIL → implementacija → PASS → commit `feat: solve service`.

### Zadatak 9: Analiza

**Datoteke:** kreiraj `src/uprent/analysis.py`, `tests/test_analysis.py`

**Sučelja:** `analyze(scenario: Scenario, ctx: ExactContext | None, report: ValidationReport) -> Analysis`; `Analysis(why: list[WhyRow], unused_trucks: list[UnusedTruck], alternatives: list[Alternative], binding: list[str], sensitivity: Sensitivity, curve: list[CurvePoint])`; `WhyRow(order, truck, other_truck, other_km: float | None, delta_km: float | None, delta_objective: float | None, other_truck_orders: list[str], impossible: str | None, lazy: bool)` (`lazy=True` kad se redak računa tek na klik: 3 kamiona ili egzaktni solver duži od 2 s); `Alternative(setting: str, value: bool, km: float, served: int, trucks_used: int, summary: str)`; `CurvePoint(km: float, end_min: float, by_truck: dict[str, list[str]])`; `Sensitivity(limit_basis: Literal["drive","drive+handling"], limit_lower_min: float, better_plan_at_min: float | None, better_plan_km: float | None, handling_max_min: float | None, next_plan_km: float | None, note: str)`. Granice limita računaju se iz tablica prema `limit_basis`, nikad s krivulje (spec §12). Uz OR-Tools (`ctx is None`) `why`, `alternatives` i `curve` su prazni i `binding` sadrži napomenu da su dostupni samo uz egzaktni solver.

- [ ] **Korak 1: Testovi:**
  - `test_why_default`: N03 → A 200,1 (+17,9); N01 → 217,0 (+34,8); N04 → 217,0 (+34,8; `other_truck_orders == ["N01", "N04"]`); N05 → 220,1 (+37,9); N02 → 231,5 (+49,3); N06–N10 `impossible` sadrži „3.500 kg".
  - `test_unused_truck_sentence`: A → „Kamion A nije korišten: B stigne sve sam, a svaki nalog prebačen na A dodao bi najmanje 17,9 km."
  - `test_alternatives_default`: dva retka (`limit_includes_handling=True` → 200,1; `require_all_trucks=True` → 200,1).
  - `test_binding_default`: sadrži „Limit vožnje nije aktivan" i „3 h 02 min".
  - `test_sensitivity_default`: tekst sadrži „182,2 min" i „ne mijenja plan".
  - `test_sensitivity_strict`: `handling_max_min == 20.95`, `next_plan_km == 217.0`, `limit_lower_min == 522.9`; uz `require_all_trucks=False` `better_plan_at_min == 582.2` i `better_plan_km == 182.2`.
  - `test_sensitivity_limit_basis_drive`: zadano → `limit_basis == "drive"`, `limit_lower_min == 182.2`, `better_plan_at_min is None`, `handling_max_min is None`.
  - `test_sensitivity_hidden_for_mixed_handling`: utovar 20, istovar 15 → `handling_max_min is None`, `note` objašnjava zašto.
  - `test_better_plan_full_key`: `objective="makespan"` → `better_plan_at_min is None`; `require_all_trucks=True` → `better_plan_at_min is None`.
  - `test_handling_max_skips_unused`: `limit_includes_handling=True`, `day_limit_min=600` → plan „B sam", `handling_max_min == pytest.approx(20.89)`, bez iznimke.
  - `test_analysis_requires_exact_result`: `analyze` s `ctx=None` → `why`, `alternatives` i `curve` su prazni.
  - `test_handling_max_no_used_trucks`: `limit_includes_handling=True`, bez naloga → `handling_max_min is None`, a `note` sadrži „nije primjenjivo".
  - `test_curve_default`: 14 točaka; prva (182,2; 582,2), zadnja (284,2; 344,8); uz `require_all_trucks=True` 13 točaka, prva (200,1; 522,9).
- [ ] **Korak 2–5:** FAIL → implementacija (ponovno kombiniranje iz `ctx`, bez nove DP pretrage) → PASS → commit `feat: analysis`.

### Zadatak 10: Usporedba scenarija i CLI

**Datoteke:** kreiraj `src/uprent/compare.py`, `src/uprent/cli.py`, `tests/test_compare.py`, `tests/test_cli.py`

**Sučelja:** `Preset(label: str, overrides: dict, truck_overrides: dict | None = None)`; `PRESETS` (redom): „Zadano (doslovno tumačenje)" `{}`; „U 9 h ulazi utovar/istovar" `{limit_includes_handling: true}`; „Svaki kamion mora voziti" `{require_all_trucks: true}`; „9 h s utovarom, 20 min po nalogu" `{limit_includes_handling: true, load_min: 10, unload_min: 10}`; „Najraniji završetak" `{objective: "makespan"}`; „Jedan stroj odjednom" `truck_overrides={"slots": 1}`. `compare(scenario, presets=PRESETS) -> list[ComparisonRow(label, km, served, orders, trucks_used, valid_under: list[str])]`; oznake tumačenja: „samo vožnja", „vožnja + radnje (20 min)", „vožnja + radnje (10 + 10)", „svaki kamion vozi". `main(argv: list[str] | None = None) -> int`.

- [ ] **Korak 1: Testovi:** `test_presets_values` (182,2; 200,1; 200,1; 182,2; 284,2; 209,0); `test_valid_under` (redak 1: točno „samo vožnja" i „vožnja + radnje (10 + 10)"; redak 2: sve četiri); `test_cli_json_default` (`main(["solve","data/default_scenario.json","--json"])` → JSON `totals.km == 182.2`, izlazni kod 0); `test_cli_set_override` (`--set limit_includes_handling=true` → 200,1); `test_cli_solver_flag` (`--solver ortools` → `solver == "ortools"`); `test_cli_invalid_file` (→ izlazni kod 2, poruka na stderr); `test_cli_compare_table` (ispis sadrži svih šest naziva).
- [ ] **Korak 2–5:** FAIL → implementacija → PASS → commit `feat: compare presets and CLI`.

### Zadatak 11: API

**Datoteke:** kreiraj `src/uprent/api.py`, `tests/test_api.py`; izmijeni `cli.py` (`serve`)

**Sučelja:** `create_app(static_dir: Path | None = Path("web/dist")) -> FastAPI`; rute iz spec §8. Ako `static_dir` ne postoji, `/` vraća jednostavnu stranicu „Sučelje nije izgrađeno – pokreni `npm run build` u mapi web". Rute za računanje su sinkrone (`def`), pa ih FastAPI izvršava u threadpoolu.

- [ ] **Korak 1: Testovi** (`TestClient`): `test_health`; `test_default_scenario` (10 naloga); `test_solve_default` (182,2); `test_solve_invalid_422` (nepoznata lokacija → 422, `detail` sadrži „nepoznata lokacija"); `test_validate_bad_plan` (dvostruki utovar → `passed is False`); `test_compare` (6 redaka); `test_solve_runs_in_threadpool` (ruta je `def`, ne `async def` – provjeri `inspect.iscoroutinefunction` nad endpointom); `test_static_fallback` (bez `web/dist` → 200 i tekst „nije izgrađeno").
- [ ] **Korak 2–5:** FAIL → implementacija → PASS → commit `feat: FastAPI app`.

### Zadatak 12: Sučelje – kostur, API klijent, formatiranje i sustav uputa

**Datoteke:** kreiraj `web/` (Vite React TS), `web/vite.config.ts` (proxy `/api` → `http://127.0.0.1:8000`; Vitest `jsdom`), `web/tailwind.config.ts`, `web/src/types.ts`, `web/src/api.ts`, `web/src/lib/format.ts`, `web/src/lib/parseNumber.ts`, `web/src/content/hints.ts`, `web/src/components/{Hint,InfoLine,Callout,StatusBadge}.tsx`, testovi u `web/src/**/*.test.ts(x)`.

**Sučelja:** `formatKm(km: number): string`, `formatKg(kg: number): string`, `formatDuration(min: number): string`, `parseHrNumber(s: string): number | null`; `hints.settings[key] = {title, body}` za svaki ključ postavki, `hints.tabs[tab]`, `hints.status[status]`, `hints.firstSteps: string[3]`, `hints.empty[...]`; `<Hint id>` = ikona ⓘ s oblačićem (otvara klik ili fokus, zatvara Esc ili klik izvan; nikad modal).

- [x] **Korak 1:** `npm create vite@latest web -- --template react-ts`; dodaj `tailwindcss`, `lucide-react`, `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, `@playwright/test`.
- [x] **Korak 2: Testovi:** `formatKm(182.2) === "182,2 km"`; `formatKg(9400) === "9.400 kg"`; `formatDuration(582.2) === "9 h 42 min"`, `formatDuration(522.9) === "8 h 43 min"`, `formatDuration(37.2) === "37 min"`, `formatDuration(540) === "9 h"`; `parseHrNumber("20,5") === 20.5`, `("20.5") === 20.5`, `("abc") === null`, `("") === null`; `hints covers every setting` (za svaki ključ iz `SETTINGS_KEYS` postoji naslov i tijelo; tekst za `limit_includes_handling` sadrži „voziti", „182,2 km" i „200,1 km"); `Hint opens and closes` (skriven → klik → vidljiv → Esc → skriven).
- [x] **Korak 3:** `npm test` → FAIL. **Korak 4:** implementiraj; tekstove uputa prepiši iz spec §6 i §13. **Korak 5:** `npm test` → PASS. **Korak 6:** commit `feat(web): scaffold, formatting and hint system`.

### Zadatak 13: Sučelje – Postavke i Ulazni podaci

**Datoteke:** kreiraj `web/src/features/settings/SettingsPanel.tsx`, `web/src/features/input/InputTables.tsx`, `web/src/state/useScenario.ts`, testove uz njih.

**Sučelja:** `useScenario()` → `{scenario, setScenario, applySettings(patch), resetToTask(), error}`; `SettingsPanel({settings, onChange})`; `InputTables({scenario, onChange})`. Neispravna izmjena se ne šalje na računanje: prikazuje grešku uz polje, a zadnji valjani scenarij i rezultat ostaju.

- [x] **Korak 1: Testovi:** `shows literal defaults` (limit „9 h", prekidač „U 9 h ulazi utovar/istovar" isključen, utovar 20, istovar 20, „Svaki kamion mora voziti" isključen); `toggle emits patch` (klik → `onChange({limit_includes_handling: true})`); `every setting has a hint icon`; `invalid edit keeps last result` (nalog s nepoznatom lokacijom → poruka uz polje, `onChange` nije pozvan); `decimal comma accepted` (utovar „20,5" → 20.5); `reset restores task data`; `add order with heavy machine` (dodaj M11 12000 i N11 L1→L3 → scenarij ima 11 naloga).
- [x] **Korak 2–5:** FAIL → implementacija → PASS → commit `feat(web): settings and input data`.

### Zadatak 14: Sučelje – Plan, Provjera i računanje

**Datoteke:** kreiraj `web/src/state/useSolve.ts`, `web/src/features/plan/{PlanView,TruckCard,StepTable,AlternativeStrip,Warnings}.tsx`, `web/src/features/validation/ValidationView.tsx`, `web/src/test/fixtures/{default,strict,n11}-result.json`, testove.

**Sučelja:** `useSolve(scenario)` → `{result, comparison, computing, error}`; automatski računa 300 ms nakon zadnje promjene; svaki zahtjev ima redni broj i stariji odgovor se odbacuje; nakon rezultata egzaktnog solvera (ako `compare_with_ortools`) šalje drugi zahtjev s `solver="ortools"` i sprema `comparison`.

- [ ] **Korak 1:** generiraj fixture: `uv run uprent solve data/default_scenario.json --json > web/src/test/fixtures/default-result.json`; isto sa `--set limit_includes_handling=true` (strict) i s N11 (n11).
- [ ] **Korak 2: Testovi:** `plan shows totals` („182,2 km", „10/10"); `unused truck explained` („Kamion A" + „nije korišten" + gumb „zašto?" otkriva rečenicu iz analize); `step table rows` (B ima 21 redak; prvi redak prikazuje lokaciju i teret prvog koraka iz fixturea u hrvatskom formatu – redoslijed se ne zakucava jer više ruta može imati jednako km); `alternative strip` (prikazuje „200,1 km" i „Primijeni"; klik → `applySettings({limit_includes_handling: true})`); `warnings for n11` (kartica s „N11" i porukom `TOO_HEAVY`); `validation list` (10 provjera, sve s ✓); `ignores stale responses` (lažni `fetch`: odgovor na 1. zahtjev stiže nakon 2. → prikazan je 2.); `shows computing state` (dok traje zahtjev, vidljivo „Računam…" i postojeći rezultat ostaje).
- [ ] **Korak 3–5:** FAIL → implementacija → PASS → commit `feat(web): plan and validation views`.

### Zadatak 15: Sučelje – Karta, Vremenska crta, Analiza i raspored

**Datoteke:** kreiraj `web/src/features/map/MapView.tsx`, `web/src/features/timeline/TimelineView.tsx`, `web/src/features/analysis/{AnalysisView,CurveChart,ComparisonTable}.tsx`, `web/src/App.tsx` (raspored iz spec §13, traka „Prvi koraci", izbornik „?"), testove.

- [ ] **Korak 1: Testovi:** `map renders locations` (10 elemenata `data-testid^="loc-"`); `map routes` (zadano 1 ruta, strict 2); `timeline segments` (B: 20 traka radnji; zbroj duljina traka vožnje = 182,2 min; dionice od 0 km se ne crtaju; crta limita s oznakom „samo vožnja"); `analysis why table` (N03 redak „+17,9 km"); `why row pins order` (klik „prikaži plan" u retku N04 → `applySettings({pinned_orders: {N04: "A"}})`); `curve points` (14 točaka; klik → `applySettings({pinned_orders: …})` za sve naloge); `first steps strip` (vidljiv pri prvom otvaranju, nakon zatvaranja se ne prikazuje; vraća se iz izbornika „?"); `narrow layout` (širina 390 → postavke iza gumba „Postavke").
- [ ] **Korak 2–5:** FAIL → implementacija → PASS → commit `feat(web): map, timeline, analysis and layout`.

### Zadatak 16: E2E testovi i build

**Datoteke:** kreiraj `web/playwright.config.ts` (webServer: `uv run uprent serve --port 8765`), `web/e2e/smoke.spec.ts`; izgradi `web/dist`.

- [ ] **Korak 1:** `cd web && npm run build` → nastaje `web/dist`.
- [ ] **Korak 2: Testovi** (`smoke.spec.ts`): `loads default plan` (vidljivo „182,2 km" i „Dokazano optimalno"); `apply alternative reading` (klik „Primijeni" → „200,1 km"); `heavy order warning` (Podaci → dodaj M11 12000 i N11 → upozorenje s „N11"; „10/11"); `hint explains limit` (ⓘ uz „U 9 h ulazi utovar/istovar" → tekst sadrži „voziti"); `reset` (izbornik „?" → „Vrati podatke i postavke iz zadatka" → „182,2 km"); `mobile` (390×844: nema vodoravnog pomicanja, gumb „Postavke" vidljiv).
- [ ] **Korak 3:** `npx playwright install chromium`; `npm run e2e` → PASS.
- [ ] **Korak 4:** u `.github/workflows/ci.yml` dodaj posao za sučelje (`npm ci`, `npm test` u `web`); commit `test(web): e2e smoke tests and production build` (uključi `web/dist`); `git push`; CI zelen.

### Zadatak 17: Dokumentacija predaje

**Datoteke:** kreiraj `docs/LOGIKA.md`, `docs/PRETPOSTAVKE.md`, `docs/AI_ALATI.md`, `docs/VRIJEME.md`; provjeri `README.md` i `docs/upute.md` (već napisani).

- [ ] **Korak 1:** `LOGIKA.md` (do 2 stranice): problem (VRPPD), model, egzaktni solver i zašto je dokaz, OR-Tools i kada, validator i zašto je neovisan, cilj i leksikografski redoslijed.
- [ ] **Korak 2:** `PRETPOSTAVKE.md`: tablica iz spec §6 (tumačenja, zadano i zašto, učinak u brojkama).
- [ ] **Korak 3:** `AI_ALATI.md`: alati i uloge (ChatGPT, Gemini, Claude, Codex); kako je provjereno (egzaktni solver, neovisni referentni solver u `qa/oracle/`, validator, testovi); konkretne greške: tvrdo pravilo „oba kamiona" u OR-Toolsu → nije našao rješenje; `AddDisjunction([p, d], …)` → pad procesa; pogrešno zadano „9 h samo vožnja" u prvoj ChatGPT specifikaciji označeno kao dogovoreno prije nego što je kandidat odlučio. Geminijev neovisni pregled specifikacije našao je šest stvarnih problema (npr. `makespan` u OR-Toolsu mjerio je samo vožnju); svi su ispravljeni prije implementacije (spec §19).
- [ ] **Korak 4:** `VRIJEME.md`: tablica faza s praznim stupcem sati koji popunjava kandidat (ne izmišljati brojke).
- [ ] **Korak 5:** pokreni doslovno svaku naredbu iz `README.md` i `docs/upute.md`; svaka mora raditi kako piše. Razlike ispravi u dokumentu ili kodu.
- [ ] **Korak 6:** commit `docs: submission documents`.

### Zadatak 18: Docker i Cloudflare

**Datoteke:** kreiraj `Dockerfile`, `.dockerignore`, `cloudflare/package.json`, `cloudflare/wrangler.jsonc`, `cloudflare/src/index.ts`, `docs/deploy.md`.

- [ ] **Korak 1:** `Dockerfile`: `python:3.11-slim`, instaliraj `uv`, `uv sync --frozen --no-dev`, kopiraj `src/`, `data/`, `web/dist/`; `CMD ["uv","run","uprent","serve","--host","0.0.0.0","--port","8000"]`. `.dockerignore` isključuje `.git`, `.venv`, `web/node_modules`, `priprema/`, `originalni-zadatak.md` i `qa/`.
- [ ] **Korak 2:** `docker build -t uprent-planner .` → uspjeh; `docker run --rm -p 8000:8000 uprent-planner`; `curl http://localhost:8000/api/health` → `{"status":"ok"}`; u pregledniku zadani plan 182,2 km.
- [ ] **Korak 3:** Cloudflare Containers: `wrangler.jsonc` s `containers` (`class_name: "PlannerContainer"`, `image: "../Dockerfile"`, `max_instances: 2`) i Durable Object vezom; `src/index.ts` s klasom `PlannerContainer extends Container` (`defaultPort = 8000`, `sleepAfter = "15m"`) koja sve zahtjeve prosljeđuje kontejneru (paket `@cloudflare/containers`). Prije pisanja provjeri trenutnu dokumentaciju Cloudflare Containers (beta).
- [ ] **Korak 4:** kandidat je prije pokretanja Codexa uzeo Workers Paid i prijavio se (`npx wrangler login`). Codex:
  - pokreće `npx wrangler whoami` (ako ne prolazi, stani i javi);
  - provjerava da Docker radi;
  - iz mape `cloudflare/` pokreće `npx wrangler deploy` (`max_instances: 1`), s varijablom okoline `CLOUDFLARE_ACCOUNT_ID` postavljenom iz lokalne datoteke `cloudflare/.env`. Datoteka je u `.gitignore`, a ID se ne upisuje u `wrangler.jsonc`;
  - tokene nikad ne ispisuje ni ne commita;
  - javni URL provjerava u ugrađenom pregledniku i upisuje ga u README.

  Provjera: `https://…/api/health` → ok; zadani plan 182,2 km.
- [ ] **Korak 5:** `docs/deploy.md`: oba puta iz spec §14 (Containers i rezerva Pages + Render) s naredbama, uključujući postavljanje `CLOUDFLARE_ACCOUNT_ID` za korisnika koji ima više računa.
- [ ] **Korak 6:** commit `chore: docker and cloudflare deploy`.

---

## Samoprovjera plana (napravljena)

- **Pokrivenost specifikacije:** §5 pravila → Z3; §6 postavke → Z1, Z6, Z13; §8 format/CLI/API → Z1, Z10, Z11; §9 solveri → Z5–Z8; §10 validator → Z3; §11 razlozi → Z4, Z8; §12 analiza → Z9, Z10; §13 sučelje i upute → Z12–Z16; §14 hosting → Z18; §15 testovi → Z1–Z16; §16 predaja → Z17.
- **Dosljednost imena:** `validate`, `Plan`, `Op`, `SolverOutput`, `ExactContext`, `solve`, `analyze`, `compare`, `apply_overrides` – isti u svim zadacima.
- **Fokus pregleda:** svih pet rizika ima test u zadatku koji posjeduje kod.

## Izvođenje

Preporuka: **Codex implementira zadatke 1–18 i zatim izvršava `docs/razvoj/qa-plan.md`; Claude nakon toga radi neovisni pregled** (logika solvera, neovisnost validatora, usporedba s referentnim solverom na više scenarija, upute u sučelju, točnost dokumentacije). Početni prompt za Codex je u `prompts/1-codex-implementacija.md`.
