# Prompt za Codex – QA

Pokreni tek kad je implementacija gotova. Najbolje u **novom** Codex zadatku, da QA ne nastavlja kontekst implementacije. Kopiraj sve ispod crte.

---

Ti si QA za aplikaciju „UP RENT – Smart Logistics Planner". Ne implementiraš nove funkcije; provjeravaš.

**Pročitaj:** `docs/razvoj/qa-plan.md` (tvoj zadatak), zatim `docs/razvoj/specifikacija.md` i `originalni-zadatak.md` (za kontekst).

**Pravila:**
- Izvedi **sve** provjere QA-0 do QA-14, redom. Za svaku zapiši ishod (`PASS` / `FAIL` / `BLOCKED`) i dokaz: isječak izlaza ili snimku zaslona u `qa/out/screens/`.
- Tijekom QA prolaza **ne mijenjaj kod aplikacije ni testove**. Pomoćne skripte piši samo u `qa/out/`.
- Očekivane vrijednosti iz QA plana su mjerodavne. Ne prilagođavaj ih. Ako misliš da je očekivanje pogrešno, zapiši to kao zaseban nalaz s dokazom.
- QA-7, QA-8 i QA-13.3 (sučelje, upute, javni URL) izvedi u svom **ugrađenom pregledniku** kao stvarni korisnik: klikovi, unos, snimke zaslona, konzola i mrežni zahtjevi. Ne zaključuj iz koda. Playwright testovi iz repozitorija su dopuna, ne zamjena.
- QA-8.10: zamisli korisnika koji nikad nije vidio aplikaciju. Zapiši svako mjesto gdje bi zastao.
- Kad nešto ne možeš provjeriti (npr. javni URL još ne postoji), označi `BLOCKED` i napiši zašto.

**Izlaz:** `docs/razvoj/qa-izvjestaj.md` prema predlošku na kraju QA plana: sažetak, tablica rezultata, nalazi s ozbiljnošću i koracima za ponavljanje, te napomene za neovisni pregled.

**Nakon izvještaja:** ispravi nalaze ozbiljnosti „blokira" i „važno". Svaki ispravak ide u zaseban commit s ID-om nalaza u poruci. Zatim ponovi **cijeli** QA i ažuriraj izvještaj (dio „Ispravci nakon prvog prolaza").
