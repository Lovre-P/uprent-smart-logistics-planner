# Prompt za Gemini – neovisni pregled specifikacije (po želji, prije implementacije)

Svrha: treći, neovisni par očiju prije nego što Codex krene pisati kod. Jeftino je, a greška u specifikaciji kasnije je skupa.

Uz prompt priloži dvije datoteke: `originalni-zadatak.md` i `docs/razvoj/specifikacija.md`. Zatim kopiraj sve ispod crte.

---

Priložena su dva dokumenta: izvorni programerski zadatak i specifikacija aplikacije napisana za njega. Budi strog recenzent. Zanimaju me samo stvarni problemi, ne stil.

Pronađi i navedi, poredano od najozbiljnijeg:
1. Zahtjeve iz zadatka koje specifikacija ne pokriva ili pokriva pogrešno.
2. Logičke greške ili proturječja unutar specifikacije: pravila, zadane postavke, statusi, redoslijed ciljeva.
3. Brojke koje ne mogu biti točne. Provjeri barem: udaljenosti L0→L9 = 9,4 km, L9→L4 = 17,0 km, L4→L0 = 10,8 km; ruta „B sam" 182,2 km uz 20 radnji po 20 min = 582,2 min; strože tumačenje 200,1 km (A: N03 37,2 km; B 162,9 km, 522,9 min).
4. Rubne slučajeve koji bi srušili aplikaciju ili dali pogrešan rezultat, a specifikacija ih ne spominje.
5. Mjesta gdje bi programer morao nagađati, a pogrešan izbor bi bio skup.

Za svaki nalaz napiši: gdje je (odjeljak), u čemu je problem, zašto je problem (s brojkom ili citatom) i prijedlog ispravka. Ako nešto nije problem nego svjesna odluka obrazložena u specifikaciji, ne navodi to. Ako ne nađeš ništa ozbiljno, napiši to.
