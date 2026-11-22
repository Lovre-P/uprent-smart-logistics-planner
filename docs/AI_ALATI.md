# AI alati i provjera rezultata

Kandidat je odabrao da se devet sati po zadanom odnosi na vožnju. Učinak te odluke može se provjeriti na istim nalozima. Kad se u limit uključe i utovar i istovar, A preuzima nalog N03, a ukupna kilometraža raste za 17,9 km.

| Alat | Uloga u radu |
|---|---|
| ChatGPT | Predložio je početni pristup s OR-Toolsom i Streamlitom te prvo tumačenje poslovnih pravila. |
| Gemini | Predložio je FastAPI i React, zatim neovisno pregledao specifikaciju i izdvojio pogreške u modelu i načinu provjere. |
| Codex | Provjerio je zahtjeve, sastavio primjer s pogrešnim izostavljanjem naloga i implementirao planer uz testove. Zasebni agenti pregledali su implementaciju jezgre. |
| Claude | Predviđen je za neovisni pregled nakon završene implementacije i zasebnog QA postupka. Opseg je zadan u [uputama za neovisni pregled](../prompts/4-claude-neovisni-pregled.md). |

## Što su provjere otkrile

- U prvoj ChatGPT-ovoj specifikaciji devet sati vožnje bilo je predstavljeno kao već dogovorena pretpostavka. Kandidat je naknadno odabrao doslovno čitanje kao zadano, uz mogućnost da korisnik uključi utovar i istovar u limit.
- U ranom pokusu s OR-Toolsom tvrdi uvjet da oba kamiona moraju krenuti spriječio je početnu heuristiku da pronađe rješenje. Zahtjev za korištenje više kamiona zato je postao prednost pri izboru između planova koji izvrše jednako mnogo naloga.
- Geminijev prijedlog da se obje radnje istog naloga zajedno predaju u `AddDisjunction([p, d], …)` prouzročio je pad procesa s OR-Toolsom 9.15. Model predviđa po jedan zaseban poziv za svaki čvor. Veza utovara i istovara određuje da ih obavi isti kamion.
- U prvom krugu neovisnog pregleda Gemini je našao šest problema. Primjerice, predloženi model za najraniji završetak mjerio je samo vožnju kada su radnje bile isključene iz dnevnog limita. Ispravak uvodi `work_time` koji uvijek obuhvaća i radnje. Svih šest nalaza ispravljeno je u specifikaciji prije implementacije. [Nalazi po krugovima pregleda](razvoj/specifikacija.md#19-povijest-izmjena).
- Codex je prije implementacije provjerio može li se nalog izostaviti čim njegova samostalna ruta premaši limit. Referentni solver vratio je izvediv plan od **11,3 km za oba naloga**, iako je samo prvi izravnom rutom tražio 11,4 km. Kandidat je odobrio računanje donje granice preko zaokruženih dionica. U tom primjeru ona za prvi nalog iznosi 11,2 km. [Izračun i odluka](razvoj/odstupanja.md).

Tijekom implementacije završeno je šest zasebnih pregleda jezgre. Obuhvatili su validator, tablice ruta, kombiniranje ruta, OR-Tools, servis za izračun i analizu rezultata. Primjerice, pregled OR-Toolsa otkrio je da naloge izostavljene prije pretrage treba uzeti u obzir i pri određivanju statusa. Regresijski test sada provjerava da se plan s izostavljenim nalogom prikazuje kao djelomičan kad je to dopušteno. [Rezultati po zadacima](razvoj/napredak.md).

## Kako provjeriti brojke

Egzaktni solver daje optimum pregledom dopuštenih stanja i raspodjela. Validator neovisno ponavlja svaku radnju konkretnog plana, uključujući opterećenje na svakom utovaru i povratak u bazu. Testiranje tih dvaju dijelova pokriva različite pogreške. Jedan test može uhvatiti preveliku kilometražu valjane rute, drugi privremeno prekoračenje nosivosti i kada je ukupan broj kilometara točan.

Referentni solver napisan je odvojeno od aplikacije. Za zadani je ulaz reproducirao **182,2 km**, sa svih deset naloga na B. Uz uključen utovar i istovar u devetosatni limit reproducirao je **200,1 km** i dodjelu N03 kamionu A. [Referentni solver](../qa/oracle/oracle_exact.py).

Usporedba je pokrenuta kroz naredbeni redak na **30 slučajnih scenarija i završila je bez grešaka**. Egzaktni solver u svakom je scenariju izračunao isti broj izvršenih naloga i istu kilometražu kao referentni solver. Provjera za OR-Tools tražila je slučaj u kojem bi izvršio više naloga od reference ili isti broj s manje kilometara. Svi planovi obaju solvera prošli su validator. Provjera se ponavlja naredbom `uv run python qa/oracle/compare_with_app.py --seeds 30`. [Program za usporedbu](../qa/oracle/compare_with_app.py).

Automatski testovi obuhvaćaju pravila prijevoza i rad sučelja. Za završnu provjeru kroz preglednik i usporedbu prikazanih podataka s izračunom pripremljen je [zaseban QA plan](razvoj/qa-plan.md).
