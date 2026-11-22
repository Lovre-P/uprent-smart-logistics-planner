"""Usporedba aplikacije s neovisnim referentnim solverom na slučajnim scenarijima.

Pokretanje (iz korijena repozitorija, nakon što aplikacija postoji):
    uv run python qa/oracle/compare_with_app.py --seeds 30

Za svaki scenarij:
  * referentni solver (oracle_exact.py) daje broj izvršenih naloga i km;
  * aplikacija se pokreće kroz CLI: `uv run uprent solve FILE --json --solver exact|ortools`;
  * egzaktni način aplikacije mora dati ISTI broj naloga i ISTE km (tolerancija 0,05 km);
  * OR-Tools ne smije biti bolji od referentnog (izvršava najviše jednako naloga,
    a uz jednako naloga ima barem jednako km);
  * oba plana moraju imati validation.passed == true.
Izlazni kod je 1 ako ijedna provjera padne.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oracle_exact import solve as oracle_solve  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "qa" / "out"
WEIGHTS = [800, 1300, 1800, 2400, 3100, 3900, 4800, 6100, 7500, 9400]


def random_scenario(seed: int) -> dict:
    rnd = random.Random(seed)
    base = json.loads((ROOT / "data" / "default_scenario.json").read_text(encoding="utf-8"))
    n = rnd.randint(5, 10)
    machines, orders = [], []
    for k in range(n):
        mid, oid = f"M{k + 1:02d}", f"N{k + 1:02d}"
        machines.append({"id": mid, "weight_kg": rnd.choice(WEIGHTS)})
        p, d = rnd.sample([l["id"] for l in base["locations"]], 2)
        orders.append({"id": oid, "machine": mid, "pickup": p, "delivery": d})
    base["name"] = f"QA slučajni scenarij {seed}"
    base["machines"], base["orders"] = machines, orders
    base["settings"].update({
        "limit_includes_handling": rnd.random() < 0.5,
        "require_all_trucks": rnd.random() < 0.3,
        "day_limit_min": rnd.choice([540, 540, 360, 240]),
        "compare_with_ortools": False,
    })
    return base


def run_app(path: Path, solver: str) -> dict:
    cmd = ["uv", "run", "uprent", "solve", str(path), "--json", "--solver", solver]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> izlaz {proc.returncode}: {proc.stderr.strip()[:400]}")
    return json.loads(proc.stdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--start", type=int, default=1000)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    failures = 0
    for seed in range(args.start, args.start + args.seeds):
        sc = random_scenario(seed)
        path = OUT / f"scenarij_{seed}.json"
        path.write_text(json.dumps(sc, ensure_ascii=False, indent=2), encoding="utf-8")
        ref = oracle_solve(sc)
        problems = []
        try:
            ex = run_app(path, "exact")
            ot = run_app(path, "ortools")
        except Exception as exc:  # noqa: BLE001
            print(f"seed {seed}: GREŠKA pokretanja: {exc}")
            failures += 1
            continue
        if ex["totals"]["served"] != ref["served"] or abs(ex["totals"]["km"] - ref["km"]) > 0.05:
            problems.append(f"egzaktni {ex['totals']['served']}/{ex['totals']['km']} ≠ referentni {ref['served']}/{ref['km']}")
        if not ex["validation"]["passed"]:
            problems.append("egzaktni plan ne prolazi validator")
        if ot["totals"]["served"] > ref["served"] or (
            ot["totals"]["served"] == ref["served"] and ot["totals"]["km"] < ref["km"] - 0.05
        ):
            problems.append(f"OR-Tools bolji od referentnog ({ot['totals']['served']}/{ot['totals']['km']}) – nemoguće, greška u modelu ili referenci")
        if not ot["validation"]["passed"]:
            problems.append("OR-Tools plan ne prolazi validator")
        gap = ""
        if ot["totals"]["served"] == ref["served"] and ref["km"]:
            gap = f" | OR-Tools razlika {100 * (ot['totals']['km'] - ref['km']) / ref['km']:.2f} %"
        status = "OK " if not problems else "PAD"
        print(f"{status} seed {seed}: n={ref['orders']} referentni {ref['served']}/{ref['orders']} {ref['km']} km{gap}")
        for p in problems:
            print(f"     - {p}")
        failures += bool(problems)
    print(f"\nUkupno: {args.seeds} scenarija, {failures} s greškom.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
