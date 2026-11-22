# Kako planer raspoređuje prijevoz

Na zadanim podacima kamion B može prevesti svih deset strojeva za **182,2 km**. Vožnja traje 3 h 02 min, a dvadeset utovara i istovara još 400 min. Kad u devet sati mora stati cijeli radni dan, najkraći plan ima **200,1 km**. Kamion A tada preuzima N03, a B ostalih devet naloga.

## Što čini plan

Riječ je o problemu usmjeravanja vozila s preuzimanjem i isporukom (VRPPD). Odluke su koji kamion prevozi svaki stroj i kojim redom obavlja radnje. Svaka ruta počinje i završava u bazi. Isti kamion mora preuzeti i isporučiti stroj, a nakon svake radnje mora imati dovoljno nosivosti i mjesta. Čak i redoslijed na istom stajalištu može odlučiti o izvedivosti. Ako B na L7 utovari M10 prije nego što istovari M06, teret naraste na 13.300 kg.

Pri usporedbi dvaju planova odlučuje prvi kriterij po kojem se razlikuju.

1. Izvršiti što više naloga.
2. Ako se traži korištenje svih kamiona, upotrijebiti što više kamiona.
3. Ostvariti odabrani cilj, najmanju ukupnu kilometražu ili najraniji završetak posljednjeg kamiona.
4. Uz jednako vrijeme završetka prednost ima manja ukupna kilometraža.

## Kako se dokazuje optimum

Egzaktni solver gradi tablicu najkraćih povratnih ruta. Kamioni iste nosivosti i istog broja mjesta dijele tablicu. Stanje određuju skup preuzetih naloga, skup isporučenih naloga i trenutačna lokacija. Iz njih se može utvrditi što je u kamionu i koje su sljedeće radnje dopuštene. Kad dva puta dovedu do istog stanja, oba imaju jednake mogućnosti nastavka i već su obavila iste radnje. Dovoljno je sačuvati kraći put. Svaki put kad je kamion prazan može se dodati povratak u bazu i zabilježiti rezultat za upravo izvršeni skup naloga.

Drugi korak raspodjeljuje skupove iz tablica tako da svaki nalog pripadne najviše jednom kamionu. Provjerava brzinu, dnevni limit i prikvačene naloge. Za isti skup naloga trajanje svih radnji je stalno, pa najkraća ruta ujedno troši najmanje vremena. Za cilj najranijeg završetka solver prvo određuje najveći izvediv broj naloga, zatim najraniji zajednički završetak i naposljetku najmanje kilometara uz taj završetak. Ako se traži korištenje svih kamiona, ta prednost vrijedi u svakom koraku. Dokaz optimalnosti slijedi iz obuhvata svih dopuštenih redoslijeda i raspodjela.

## Kada se nalog smije unaprijed izostaviti

Svaka se dionica zaokružuje zasebno na desetinku kilometra, s polovicom prema gore. U primjeru iz specifikacije v4.2 put od baze do cilja izravno ima 5,7 km, a preko drugog utovara 2,8 + 2,8 = 5,6 km. Nalog N01 sam traži 11,4 km, dok kamion u zajedničkoj vožnji oba naloga izvršava za 11,3 km.

Za procjenu vremena predprovjera računa najkraće putove između baze i svih mjesta utovara i istovara. Zbroji tri donje granice za put do utovara, od utovara do isporuke i natrag u bazu. Za N01 dobiva **11,2 km**. Pri brzini od 60 km/h i limitu od 11,3 min nalog stoga ostaje u pretrazi. Izostavljanje zbog vremena opravdano je tek ako donja granica, uz obvezne radnje kad su uključene u limit, prelazi limit svakog dopuštenog kamiona.

## Veći ulazi i provjera rezultata

U automatskom načinu zadani su pragovi za egzaktni izračun 12 naloga i tri kamiona. Za veći ulaz, ili kad egzaktna pretraga dosegne granicu od milijun stanja ili osam sekundi, raspored traži OR-Tools. U početne rute umeće parove utovar–istovar, a zatim lokalno poboljšava raspored. Zasebno prati vrijeme koje ulazi u limit i ukupno radno vrijeme. Pronađeni potpuni plan nosi oznaku **Najbolje pronađeno**. Ako vrijeme pretrage istekne, izvedivost potpunog plana može ostati otvorena.

Oba solvera predaju slijed radnji neovisnom validatoru. On iz naloga očitava mjesta i mase, vlastitom formulom računa dionice te pri svakom utovaru i istovaru provjerava redoslijed, masu tereta i broj strojeva. Nakon povratka u bazu uspoređuje dnevni limit s vremenom vožnje ili s ukupnim radnim vremenom, ovisno o postavci. Iz te simulacije dolaze kilometri, satnica i opterećenja za prikaz. Kršenje tvrdog pravila daje status `INVALID_PLAN`. Nekorišten kamion uz uključenu postavku „Svaki kamion mora voziti” daje informativno upozorenje.
