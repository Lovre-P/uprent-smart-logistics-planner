# Prompt za Gemini – neovisni pregled koda (po želji, nakon Codexova QA-a)

Specifikacija više ne treba nove krugove: treći krug nije našao kritične ni važne nalaze. Ovaj prompt je za drugu stvar: pregled **stvarnog koda** kad ga Codex napiše. Pošalji ga usporedno s Claudeovim pregledom (prompt 4). Odgovor proslijedi Claudeu.

Priloži:
- `docs/razvoj/specifikacija.md`
- `src/uprent/solvers/exact.py`
- `src/uprent/solvers/ortools_solver.py`
- `src/uprent/validator.py`
- `src/uprent/analysis.py`
- `docs/razvoj/qa-izvjestaj.md`

Zatim kopiraj sve ispod crte.

---

Prilažem specifikaciju i četiri ključne datoteke implementacije (egzaktni solver, OR-Tools solver, validator, analiza), te QA izvještaj. Pregledaj **kod** prema specifikaciji. Zanimaju me samo stvarne greške, ne stil.

Traži posebno:
1. mjesta gdje kod odstupa od specifikacije (§9.1, §9.2, §10, §12);
2. greške koje testovi ne bi uhvatili: granični slučajevi, prazni skupovi, dijeljenje nulom, `float` umjesto `Fraction`, pogrešan leksikografski ključ, `pinned_orders`, `require_all_trucks`, `makespan`;
3. ovisi li validator o kodu solvera (smije ovisiti samo o domenskim modelima);
4. OR-Tools: dimenzije `limit_time` i `work_time`, kazne, disjunkcije, `fix_start_cumul_to_zero`, zaokruživanje.

Svaki nalaz označi kao **kritično** (pogrešan rezultat ili pad), **važno** (odstupanje od specifikacije) ili **sitno**. Uz svaki navedi datoteku, funkciju ili redak, scenarij koji grešku pokazuje i prijedlog ispravka. Ako nema kritičnih ni važnih nalaza, napiši to izričito.
