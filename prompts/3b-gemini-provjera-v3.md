# Prompt za Gemini – kratka provjera specifikacije v3

Pošalji u isti Gemini razgovor u kojem je bio prvi pregled, uz novu verziju `docs/razvoj/specifikacija.md`. Odgovor proslijedi Claudeu.

---

Prilažem specifikaciju v3. Ispravljena je prema tvojih šest nalaza; popis izmjena je u §19. Provjeri kratko i strogo:

1. Za svaki od tvojih šest nalaza: je li ispravak u v3 stvarno rješava? Odgovori po nalazu s „riješeno" ili „nije riješeno" i jednom rečenicom zašto.
2. Jesu li izmjene u v3 uvele novo proturječje ili grešku? Gledaj posebno §6 (`pinned_orders`), §8 (statusi i provjera ulaza), §9.1 (`makespan` u tri koraka i zaštita stanja), §9.2 (`limit_time` i `work_time`, kazne), §10 (tvrde i informativne provjere), §12 (osjetljivost) i §15 (testovi 17–21).
3. Postoji li još nešto što bi dalo pogrešnu brojku ili srušilo aplikaciju?

Navedi samo stvarne probleme, s odjeljkom i prijedlogom ispravka. Ako ih nema, napiši „nema novih problema".
