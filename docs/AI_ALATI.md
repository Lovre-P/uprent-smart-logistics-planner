# AI alati i provjera rezultata

Kandidat je odabrao da se devet sati po zadanom odnosi na vožnju. Učinak te odluke može se provjeriti na istim nalozima. Kad se u limit uključe i utovar i istovar, A preuzima nalog N03, a ukupna kilometraža raste za 17,9 km.

## Tijek rada

1. Kratko informiranje o problemu u ChatGPT-u.
2. Kandidat je napisao pretpostavke i pravila koja smatra obveznima. S Claude Codeom (Opus 5.5) ih je provjerio i kritički pregledao, a zatim izradio specifikaciju, plan implementacije, QA plan i promptove za provjeru.
3. Gemini 4 Hydrogen u Google AI Studiju pregledao je specifikaciju i pretpostavke izvan izvornog konteksta, u najviše četiri kruga.
4. Codex (GPT 6.2 Astra, xhigh, sa subagentima) implementirao je plan kao ograničeno autonoman zadatak. Smjernice su određivale što mora pročitati prije početka i kada mora stati i tražiti odobrenje.
5. Nakon kandidatove ručne provjere QA je izveden u novom Codexovu razgovoru, uz automatizirane testove i provjeru u ugrađenom pregledniku.
6. Završnu provjeru napravili su Claude Code i Gemini. Kandidat je nalaze objedinio u Claude Codeu i dao ih Codexu na ispravak.

## Uloga svakog alata

| Alat | Uloga u radu |
|---|---|
| ChatGPT | Predložio je početni pristup s OR-Toolsom i Streamlitom te prvo tumačenje poslovnih pravila. |
| Gemini 4 Hydrogen | Predložio je FastAPI i React, zatim neovisno pregledao specifikaciju i izdvojio pogreške u modelu i načinu provjere. |
| Codex (GPT 6.2 Astra) | Provjerio je zahtjeve, sastavio primjer s pogrešnim izostavljanjem naloga i implementirao planer uz testove. Zasebni agenti pregledali su implementaciju jezgre. |
| Claude Code (Opus 5.5) | Usporedio je tri predložena pristupa i egzaktnim izračunom potvrdio 182,2 km i 200,1 km. Napisao je specifikaciju, plan implementacije, QA plan i referentni solver. Nakon QA-a neovisno je pregledao kod i sučelje te aplikaciju usporedio s iscrpnom pretragom na 400 slučajnih scenarija. [Neovisni pregled](razvoj/neovisni-pregled.md) |

## Što su provjere otkrile

- U prvoj ChatGPT-ovoj specifikaciji devet sati vožnje bilo je predstavljeno kao već dogovorena pretpostavka. Kandidat je naknadno odabrao doslovno čitanje kao zadano, uz mogućnost da korisnik uključi utovar i istovar u limit.
- U ranom pokusu s OR-Toolsom tvrdi uvjet da oba kamiona moraju krenuti spriječio je početnu heuristiku da pronađe rješenje. Zahtjev za korištenje više kamiona zato je postao prednost pri izboru između planova koji izvrše jednako mnogo naloga.
- Geminijev prijedlog da se obje radnje istog naloga zajedno predaju u `AddDisjunction([p, d], …)` prouzročio je pad procesa s OR-Toolsom 9.15. Model predviđa po jedan zaseban poziv za svaki čvor. Veza utovara i istovara određuje da ih obavi isti kamion.
- U prvom krugu neovisnog pregleda Gemini je našao šest problema. Primjerice, predloženi model za najraniji završetak mjerio je samo vožnju kada su radnje bile isključene iz dnevnog limita. Ispravak uvodi `work_time` koji uvijek obuhvaća i radnje. Svih šest nalaza ispravljeno je u specifikaciji prije implementacije. [Nalazi po krugovima pregleda](razvoj/specifikacija.md#19-povijest-izmjena).
- Gemini je u pregledu koda prijavio da druga tumačenja mogu izostaviti naloge koji ne stanu u limit. Neovisni pregled pokazao je da servis gradi tablice od svih naloga osim preteških, pa se to ne događa.
- Codex je prije implementacije provjerio može li se nalog izostaviti čim njegova samostalna ruta premaši limit. Referentni solver vratio je izvediv plan od **11,3 km za oba naloga**, iako je samo prvi izravnom rutom tražio 11,4 km. Kandidat je odobrio računanje donje granice preko zaokruženih dionica. U tom primjeru ona za prvi nalog iznosi 11,2 km. [Izračun i odluka](razvoj/odstupanja.md).

Tijekom implementacije završeno je šest zasebnih pregleda jezgre. Obuhvatili su validator, tablice ruta, kombiniranje ruta, OR-Tools, servis za izračun i analizu rezultata. Primjerice, pregled OR-Toolsa otkrio je da naloge izostavljene prije pretrage treba uzeti u obzir i pri određivanju statusa. Regresijski test sada provjerava da se plan s izostavljenim nalogom prikazuje kao djelomičan kad je to dopušteno. [Rezultati po zadacima](razvoj/napredak.md).

## Kako provjeriti brojke

Egzaktni solver daje optimum pregledom dopuštenih stanja i raspodjela. Validator neovisno ponavlja svaku radnju konkretnog plana, uključujući opterećenje na svakom utovaru i povratak u bazu. Testiranje tih dvaju dijelova pokriva različite pogreške. Jedan test može uhvatiti preveliku kilometražu valjane rute, drugi privremeno prekoračenje nosivosti i kada je ukupan broj kilometara točan.

Referentni solver napisan je odvojeno od aplikacije. Za zadani je ulaz reproducirao **182,2 km**, sa svih deset naloga na B. Uz uključen utovar i istovar u devetosatni limit reproducirao je **200,1 km** i dodjelu N03 kamionu A. [Referentni solver](../qa/oracle/oracle_exact.py).

Usporedba je pokrenuta kroz naredbeni redak na **30 slučajnih scenarija i završila je bez grešaka**. Egzaktni solver u svakom je scenariju izračunao isti broj izvršenih naloga i istu kilometražu kao referentni solver. Provjera za OR-Tools tražila je slučaj u kojem bi izvršio više naloga od reference ili isti broj s manje kilometara. Svi planovi obaju solvera prošli su validator. Provjera se ponavlja naredbom `uv run python qa/oracle/compare_with_app.py --seeds 30`. [Program za usporedbu](../qa/oracle/compare_with_app.py).

Neovisni pregled ponovio je usporedbu na 100 novih scenarija bez greške i dodao 300 rubnih scenarija. OR-Tools je u 3 s pogodio optimum u 91 od 100 scenarija, pa njegov plan nosi oznaku „Najbolje pronađeno”.

Automatski testovi obuhvaćaju pravila prijevoza i rad sučelja. Za završnu provjeru kroz preglednik i usporedbu prikazanih podataka s izračunom pripremljen je [zaseban QA plan](razvoj/qa-plan.md).
