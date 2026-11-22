import type { PlanStatus, Settings } from '../types'

export interface HintText { title: string; body: string }
export const hints = {
  settings: {
    day_limit_min: { title: 'Dnevni limit vozača', body: 'Zadatak predviđa 9 h vožnje po vozaču. B za sve naloge treba 3 h 02 min vožnje. Kraći limit može promijeniti raspodjelu naloga.' },
    limit_includes_handling: { title: 'U 9 h ulazi i utovar/istovar', body: 'Zadatak kaže da vozač može voziti 9 h. Zadano u limit ulazi samo vožnja. B sam prijeđe 182,2 km, a s radnjama radi 9 h 42 min. Uključite ovu postavku i ukupna ruta iznosi 200,1 km. A tada preuzima N03.' },
    load_min: { title: 'Trajanje utovara', body: 'Zadano je 20 min za svaki utovar. Vrijeme upisano na nalogu ima prednost. Za 20 min po cijelom nalogu postavite utovar i istovar na po 10 min.' },
    unload_min: { title: 'Trajanje istovara', body: 'Zadano je 20 min za svaki istovar. Vrijeme upisano na nalogu ima prednost. Uz limit samo za vožnju promjena utječe na kraj radnog dana.' },
    require_all_trucks: { title: 'Svaki kamion mora voziti', body: 'Zadano je isključeno. Kamion može ostati u bazi. Uključivanjem A preuzima N03, a ukupna ruta raste na 200,1 km. Ako nema dovoljno izvedivih naloga, dobit ćete upozorenje.' },
    allow_partial: { title: 'Djelomičan plan', body: 'Zadano je uključen. Plan izvršava najveći mogući broj naloga i navodi razlog za svaki izostavljeni. Isključite ako tražite isključivo potpuni plan.' },
    objective: { title: 'Cilj optimizacije', body: 'Zadani cilj su najmanji ukupni kilometri. Za najraniji kraj radnog dana kamioni prijeđu 284,2 km i završe za 5 h 45 min.' },
    solver: { title: 'Solver', body: 'Automatski odabir koristi egzaktni izračun do 12 naloga i 3 kamiona. Za veće scenarije OR-Tools traži najbolji plan u zadanom vremenu.' },
    ortools_time_limit_s: { title: 'Vrijeme pretrage OR-Toolsa', body: 'Zadano su 3 s, a raspon je od 1 do 30 s. Dulja pretraga može pronaći kraću rutu.' },
    compare_with_ortools: { title: 'Usporedi s OR-Toolsom', body: 'Nakon egzaktnog rezultata pokreće se i OR-Tools. U kartici Provjera vidite rezultate obaju izračuna. Usporedba je zadano uključena.' },
    day_start: { title: 'Početak smjene', body: 'Zadano je 07:00. Ovdje odaberite od koliko sati želite čitati dolaske i odlaske na ruti.' },
    exact_max_orders: { title: 'Prag broja naloga', body: 'Automatski odabir zadano koristi egzaktni solver do 12 naloga. Iznad praga koristi OR-Tools.' },
    exact_max_trucks: { title: 'Prag broja kamiona', body: 'Automatski odabir zadano koristi egzaktni solver za najviše 3 kamiona. Za veću flotu koristi OR-Tools.' },
    pinned_orders: { title: 'Prikvačeni nalozi', body: 'Na početku su svi nalozi slobodni. U Analizi nalog možete dodijeliti određenom kamionu i izračunati kako se mijenja plan.' },
    speed_kmh: { title: 'Brzina kamiona', body: 'Zadana brzina je 60 km/h, pa svaki kilometar traje jednu minutu. Brzina pojedinog kamiona podešava se u ulaznim podacima.' },
  } satisfies Record<keyof Settings | 'speed_kmh', HintText>,
  tabs: {
    plan: 'Pregledajte rutu svakog kamiona, vrijeme vožnje i teret nakon svake radnje.',
    map: 'Koordinate su u kilometrima. Prijeđite mišem preko koraka za pojedinosti o ruti.',
    timeline: 'Pratite kada kamion vozi, utovaruje i istovaruje strojeve.',
    analysis: 'Provjerite zašto kamion preuzima pojedini nalog i usporedite druge rasporede.',
    validation: 'Svaki se plan ponovno provjerava radnju po radnju.',
    input: 'Uredite lokacije, strojeve, kamione i transportne naloge. Plan se računa nakon valjane izmjene.',
  },
  status: {
    OPTIMAL: { title: 'Dokazano optimalno', body: 'Egzaktni solver pregledao je sve dopuštene rasporede.' },
    OPTIMAL_PARTIAL: { title: 'Optimalan djelomičan plan', body: 'Dokazano je koliko se najviše naloga može izvršiti. Razlozi za ostale naloge navedeni su u upozorenjima.' },
    FEASIBLE: { title: 'Najbolje pronađeno', body: 'OR-Tools pronašao je potpuni plan unutar vremena pretrage.' },
    FEASIBLE_PARTIAL: { title: 'Pronađen djelomičan plan', body: 'OR-Tools pronašao je plan za dio naloga unutar vremena pretrage.' },
    NO_FULL_PLAN: { title: 'Potpuni plan nije moguć', body: 'Potpuni plan dokazano nije moguć uz ove postavke. Za prikaz izvedivih naloga uključite djelomičan plan.' },
    NOT_FOUND: { title: 'Plan nije pronađen', body: 'Pretraga je završila bez rješenja. Pokušajte povećati vrijeme pretrage.' },
    INVALID_PLAN: { title: 'Plan nije valjan', body: 'Neovisna provjera otkrila je prekršeno pravilo. Pojedinosti su u kartici Provjera.' },
  } satisfies Record<PlanStatus, HintText>,
  firstSteps: [
    'Pregledajte podatke iz zadatka.',
    'Prilagodite postavke. Ikona ⓘ objašnjava svako tumačenje.',
    'Plan se računa sam. Pregledajte Kartu i Analizu.',
  ] as const,
  empty: {
    orders: 'Nema naloga. Dodajte nalog ili vratite podatke iz zadatka.',
    curve: 'Krivulja prikazuje potpune planove. Nema dostupnog potpunog plana.',
  },
} as const
