# Prompt za Claude – neovisni pregled nakon Codexa

Pošalji u Claude Code kad Codex završi implementaciju i QA (postoje `docs/razvoj/implementacija-sazetak.md` i `docs/razvoj/qa-izvjestaj.md`).

---

Codex je završio implementaciju i QA. Napravi neovisni pregled:

1. Pročitaj `docs/razvoj/qa-izvjestaj.md`, `docs/razvoj/implementacija-sazetak.md` i `docs/razvoj/odstupanja.md` (ako postoji).
2. Pregledaj logiku:
   - `src/uprent/solvers/exact.py`, `ortools_solver.py`, `validator.py`, `analysis.py`, prema specifikaciji;
   - neovisnost validatora;
   - kazne i dimenzije u OR-Toolsu;
   - leksikografski cilj.
3. Pokreni `qa/oracle/compare_with_app.py` s više scenarija (npr. `--seeds 100 --start 5000`) i rubne slučajeve koje QA nije pokrio.
4. Otvori aplikaciju u pregledniku i provjeri upute u sučelju i UX prema spec §13.
5. Provjeri da su dokumenti točni (README, upute, LOGIKA, PRETPOSTAVKE, AI_ALATI).

Nalaze zapiši u `docs/razvoj/neovisni-pregled.md`. Zatim mi reci što predlažeš ispraviti prije predaje.
