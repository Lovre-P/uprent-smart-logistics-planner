# Prompt za Codex – implementacija

Kopiraj sve ispod crte u novi Codex zadatak (radna mapa: korijen projekta `UpRent-zadatak`).

---

**Cilj:** implementiraj zadatke 1–18 iz `docs/razvoj/plan-implementacije.md` tako da aplikacija „UP RENT – Smart Logistics Planner" radi točno prema dokumentima u ovom repozitoriju.

**Gotovo je kad:**
1. svih 18 zadataka ima označene korake;
2. `uv run pytest -q`, `npm test` i `npm run e2e` (u `web`) prolaze;
3. `uv run python qa/oracle/compare_with_app.py --seeds 30` javlja 0 grešaka;
4. postoji `docs/razvoj/implementacija-sazetak.md`;
5. aplikacija je objavljena na Cloudflare Containers, javni URL radi i upisan je u README (ili je u `docs/razvoj/napredak.md` zapisano zašto nije);
6. sve je pushano na GitHub, a zadnji CI je zelen.

**Granice, da cilj ne ide u širinu:** radi samo ono što plan traži. Nema novih funkcija, dodatnih biblioteka ni refaktoriranja izvan plana. Deploy je dio cilja (Zadatak 18), ali tek kad je sve ostalo zeleno.

**Zaustavi se i javi kad:**
- test ne prolazi ni nakon 3 stvarna pokušaja ispravka;
- specifikacija proturječi sama sebi ili zadatku;
- instalacija ovisnosti ne uspijeva;
- trebala bi važna odluka koju ne pokrivaju ni specifikacija ni plan.

Prije zaustavljanja zapiši stanje i razlog u `docs/razvoj/napredak.md`. Sitne odluke donesi sam, uz kratku bilješku u `docs/razvoj/odstupanja.md`.

**Praćenje:** nakon svakog zadatka dodaj jedan redak u `docs/razvoj/napredak.md`: broj zadatka, broj testova koji prolaze, commit.

**Brzina i subagenti:** vremenski cilj je oko 2 sata, ali točnost ima prednost. Testovi, provjere i pregledi se ne preskaču radi brzine. Koristi subagente gdje ubrzavaju rad ili podižu kvalitetu i ne štedi tokene na štetu točnosti: greška koju treba kasnije ispravljati skuplja je od dodatnog agenta.
- **Paralelni tokovi**, nakon zadataka 1 i 2:
  - **A, jezgra:** zadaci 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11, redom, jer ovise jedan o drugom.
  - **B, sučelje:** zadaci 12 i 13 odmah, jer ne ovise o backendu (format scenarija i `SolveResult` su u spec §8). Zadaci 14–16 tek kad CLI daje JSON (nakon zadatka 10).
  - **C, priprema:** Dockerfile i Cloudflare datoteke (zadatak 18, bez deploya) te nacrti dokumenata (zadatak 17), čim postoji struktura projekta.
- **Pregled jezgre:** nakon zadataka 3, 5, 6, 7, 8 i 9 pokreni zasebnog subagenta-recenzenta. On kod uspoređuje sa specifikacijom i javlja nalaze, ali ne piše kod. Implementator ispravlja nalaze prije prelaska dalje.
- **Pravila za subagente:**
  - dva subagenta nikad ne mijenjaju iste datoteke;
  - svi poštuju iste zabrane (očekivane brojke, `qa/oracle/`, OR-Tools zamke, tekst zadatka);
  - glavni agent spaja rad, pokreće sve testove prije svakog commita i jedini commita i pusha.

**Pročitaj prije početka, ovim redom:**
1. `originalni-zadatak.md` – mjerodavni zadatak; ne mijenjaj ga i **nikad ga ne commitaj** (u `.gitignore` je jer nije potvrđeno smije li se objaviti).
2. `docs/razvoj/specifikacija.md` – što i zašto.
3. `docs/razvoj/plan-implementacije.md` – zadaci 1–18, svaki s datotekama, sučeljima, testovima i naredbama za provjeru.
4. `README.md` i `docs/upute.md` – već su napisani i opisuju kako aplikacija mora raditi; aplikacija se prilagođava njima, a ne obrnuto (osim ako nađeš grešku – tada je zapiši).

**Pravila rada:**
- Radi zadatke redom. U svakom zadatku: napiši testove → pokreni ih i potvrdi da padaju → implementiraj → pokreni i potvrdi da prolaze → commit. Ne prelazi na sljedeći zadatak dok trenutni nije zelen.
- Referentne brojke iz plana i specifikacije (182,2 km; 200,1 km; 217,0 km; 284,2 km; 65.562 stanja…) su ugovor. **Nikad ne mijenjaj očekivanu vrijednost u testu da bi test prošao.** Ako misliš da je brojka pogrešna, stani i zapiši dokaz u `docs/razvoj/odstupanja.md`.
- Ne mijenjaj `data/default_scenario.json`, `qa/oracle/*`, `originalni-zadatak.md` ni ništa u `priprema/`. Aplikacija ne smije uvoziti ništa iz `qa/`.
- OR-Tools: nikad `AddDisjunction([pickup, delivery], …)` (ruši proces u 9.15) i nikad tvrdo `NextVar(Start(v)) != End(v)` (heuristika tada ne nađe rješenje). Ispravni oblici su u spec §9.2.
- `validator.py` ne smije uvoziti `uprent.solvers` ni `uprent.distance`.
- Sav tekst za korisnika na hrvatskom. Tekstove uputa u sučelju drži u `web/src/content/hints.ts`, prema spec §6 i §13. Upute moraju biti dio dizajna (ⓘ oblačići, jednoredni opisi, trake), nikad modal koji iskače sam.
- Python 3.11 preko `uv`. Izgrađeni `web/dist` commitaj (ocjenjivaču ne treba Node).
- Zadatak 18 – **Cloudflare Containers**. Vlasnik je već uzeo Workers Paid i prijavio se.
  - Prije pisanja datoteka provjeri trenutnu dokumentaciju Cloudflare Containers (usluga je u beta fazi).
  - Ne pokreći `wrangler login`. Ako `npx wrangler whoami` ne prolazi, stani i javi.
  - **Račun:** prijava ima pristup dvama Cloudflare računima. Deploy ide **samo** na račun čiji je ID u lokalnoj datoteci `cloudflare/.env`: to je račun s poddomenom `lovre-petrina2.workers.dev`, na kojem je Workers Paid.
    - Pri deployu postavi varijablu okoline `CLOUDFLARE_ACCOUNT_ID` na tu vrijednost.
    - ID ne upisuj u `wrangler.jsonc` ni u drugu datoteku koja se commita; `cloudflare/.env` je u `.gitignore`.
    - Upozorenje o nedostajućim `k2` ovlastima nije bitno za Containers. Ako deploy ipak javi grešku ovlasti, stani i javi.
  - Deploy pokreni tek kad su svi testovi zeleni; Docker mora raditi; `max_instances: 1`.
  - Tokene nikad ne ispisuj ni ne commitaj.
  - Nakon deploya provjeri javni URL u ugrađenom pregledniku (`/api/health` i zadani plan 182,2 km) i upiši ga u README.
- Specifikacija je v4.1: uključuje ispravke nakon tri kruga neovisnog pregleda (spec §19). Posebno pazi na `work_time` u OR-Toolsu, `pinned_orders`, informativnu provjeru `svi_kamioni` i zaštitu od eksplozije stanja.
- **Git i GitHub:** povijest commitova je dio predaje jer pokazuje proces razvoja.
  - Zadatak 1, korak 0 pravi **privatan** repozitorij `uprent-smart-logistics-planner` (`gh` je već prijavljen). Prvi commit sadrži samo dokumente.
  - Commitaj često i smisleno, poruke kratke i na engleskom. Gdje je prirodno, prvo commitaj testove koji padaju (`test: …`), pa implementaciju (`feat: …`).
  - `git push` nakon svakog zadatka.
  - Nikad `--force` i nikad prepisivanje povijesti.
  - Vidljivost repozitorija ne mijenjaj: javnim ga čini vlasnik pri predaji.

**Kad završiš svih 18 zadataka:**
1. `uv run pytest -q` i (u `web`) `npm test` i `npm run e2e` – sve zeleno.
2. `uv run python qa/oracle/compare_with_app.py --seeds 30` → 0 grešaka.
3. Napiši kratak sažetak u `docs/razvoj/implementacija-sazetak.md`:
   - što je napravljeno;
   - odstupanja od plana i zašto;
   - poznata ograničenja;
   - broj testova.

QA radiš zasebno, prema `prompts/2-codex-qa.md`.
