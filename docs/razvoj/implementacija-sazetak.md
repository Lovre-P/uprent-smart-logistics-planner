# Sažetak implementacije

Planer raspoređuje radne strojeve po kamionima i prikazuje svaku vožnju, utovar, istovar i povratak u bazu. Za zadani scenarij dokazan je optimum od **182,2 km za svih 10 naloga**. Kamion B vozi 3 h 02 min i s radnjama radi 9 h 42 min. Kad u devet sati mora stati cijeli radni dan, kamion A preuzima N03 i zajednička kilometraža raste na **200,1 km**.

Isti izračun dostupan je u web-aplikaciji, kroz naredbeni redak i HTTP API. Na šest kartica korisnik može urediti podatke, pratiti teret nakon svake radnje, pregledati kartu i vremensku crtu, ispitati dodjelu drugom kamionu i pročitati neovisnu provjeru plana. Izgrađeno sučelje nalazi se u repozitoriju, pa su za lokalno pokretanje dovoljni uv i naredba iz [README-a](../../README.md).

## Odluke i ograničenja

- Predprovjera prema v4.2 računa najkraće putove preko zaokruženih dionica. Regresijski primjer potvrđuje donju granicu od 11,2 km za N01 i izvediv potpuni plan od 11,3 km.
- Egzaktni solver automatski se bira za scenarije do 12 naloga i 3 kamiona. Pretraga ima zaštite od milijun stanja i osam sekundi. Za veće ulaze i nakon prekida radi OR-Tools. Njegov rezultat nosi oznaku „Najbolje pronađeno”. Analize koje trebaju iscrpnu pretragu imaju zasebnu zaštitu i navode što je bilo moguće izračunati.
- Pythonovo sučelje OR-Toolsa 9.15 odbija listu kamiona u metodi `SetAllowedVehiclesForIndex`. Dopušteni kamion i mogućnost izostavljanja naloga zadani su kroz `VehicleVar`. [Odluke i provjere](odstupanja.md)
- Lokacije su simulirane koordinate u kilometrima. Plan koristi euklidske dionice i vremena unesena u scenarij. Promijenjeni scenarij može se spremiti izvozom JSON-a.

## Provjera

Prolazi **296 automatskih testova** (223 Python testa, 67 testova sučelja i šest Playwright testova sa stvarnim API-jem). Jedan test kroz obrasce u Chromiumu dodaje stroj M11 od 12.000 kg i nalog N11. Sučelje je prikazalo 10/11 i razlog prekoračenja nosivosti. Ostali E2E testovi provjeravaju početni plan, primjenu drugog tumačenja, objašnjenje postavke, vraćanje početnih podataka i mobilni prikaz.

Egzaktni solver na podacima iz zadatka obradio je **65.562 stanja**. Tijekom šest zasebnih pregleda jezgre provjerene su tablice ruta, kombiniranje kamiona, vremenski limiti, prikvačeni nalozi, statusi i objašnjenja.

Referentni solver i aplikacija uspoređeni su na 30 slučajnih scenarija (sjemena 1000–1029). Egzaktni izračun dao je isti broj naloga i kilometražu u svih 30. Provjera obaju solvera završila je s **0 grešaka**.

Brojevi testova i commit za svaki zadatak navedeni su u [dnevniku napretka](napredak.md). Obrazac za procjenu vlastitih sati čeka unos kandidata. [Vrijeme razvoja](../VRIJEME.md)

## Objava

Docker slika provjerena je lokalno na portu 8000. Ista aplikacija radi na Cloudflare Containers s jednom dopuštenom instancom i uspavljivanjem nakon 15 minuta neaktivnosti. U ugrađenom pregledniku provjereni su javni odgovor `{"status":"ok"}` i automatski izračun od **182,2 km** s oznakom „Dokazano optimalno”. [Javni demo](https://uprent-smart-logistics-planner.lovre-petrina2.workers.dev/) · [Stanje aplikacije](https://uprent-smart-logistics-planner.lovre-petrina2.workers.dev/api/health)
