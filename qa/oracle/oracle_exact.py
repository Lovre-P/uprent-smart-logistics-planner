"""Neovisni referentni (egzaktni) solver za QA.

Napisan odvojeno od aplikacije (drugi autor, drugi kod). Aplikacija ga NE smije uvoziti.
Koristi se samo za usporedbu: aplikacija mora dati isti broj izvršenih naloga i istu
kilometražu kao ovaj solver (redoslijed radnji smije biti drugačiji ako je jednako dobar).

Uporaba:
    python qa/oracle/oracle_exact.py data/default_scenario.json
    python qa/oracle/oracle_exact.py data/default_scenario.json --set limit_includes_handling=true

Podržava cilj "km" (najviše naloga -> [svi kamioni korišteni] -> najmanje km).
"""
from __future__ import annotations

import json
import sys
from decimal import ROUND_HALF_UP, Decimal, getcontext
from fractions import Fraction

getcontext().prec = 40


def leg_tenths(a: dict, b: dict) -> int:
    dx = Decimal(str(a["x"])) - Decimal(str(b["x"]))
    dy = Decimal(str(a["y"])) - Decimal(str(b["y"]))
    km = (dx * dx + dy * dy).sqrt()
    return int((km * 10).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def parse_value(raw: str):
    low = raw.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return raw


def truck_tables(orders, loc, depot, cap, slots):
    """Za jedan kamion: {maska_isporučenih: najmanje desetinki km}, preko DP-a nad stanjima."""
    elig = [i for i, o in enumerate(orders) if o["w"] <= cap]
    best = {(0, 0, depot): (0, 0, 0)}  # (preuzeti, isporučeni, lokacija) -> (km, teret, broj)
    frontier = [(0, 0, depot)]
    for _ in range(2 * len(elig)):
        nxt = {}
        for key in frontier:
            pm, dm, here = key
            km, load, cnt = best[key]
            for i in elig:
                bit = 1 << i
                if not pm & bit:
                    if cnt + 1 > slots or load + orders[i]["w"] > cap:
                        continue
                    nk = (pm | bit, dm, orders[i]["p"])
                    val = (km + leg(loc, here, orders[i]["p"]), load + orders[i]["w"], cnt + 1)
                elif not dm & bit:
                    nk = (pm, dm | bit, orders[i]["d"])
                    val = (km + leg(loc, here, orders[i]["d"]), load - orders[i]["w"], cnt - 1)
                else:
                    continue
                if nk not in nxt or val[0] < nxt[nk][0]:
                    nxt[nk] = val
        for k, v in nxt.items():
            if k not in best or v[0] < best[k][0]:
                best[k] = v
        frontier = list(nxt)
    table = {}
    for (pm, dm, here), (km, _, _) in best.items():
        if pm != dm:
            continue
        total = km + leg(loc, here, depot)
        if pm not in table or total < table[pm]:
            table[pm] = total
    return table


_LEG_CACHE: dict = {}


def leg(loc, a, b):
    key = (a, b)
    if key not in _LEG_CACHE:
        _LEG_CACHE[key] = leg_tenths(loc[a], loc[b])
    return _LEG_CACHE[key]


def solve(scenario: dict, overrides: dict | None = None) -> dict:
    s = dict(scenario["settings"])
    s.update(overrides or {})
    _LEG_CACHE.clear()
    loc = {l["id"]: l for l in scenario["locations"]}
    depot = scenario.get("depot", "L0")
    weight = {m["id"]: m["weight_kg"] for m in scenario["machines"]}
    orders = []
    for o in scenario["orders"]:
        load = o.get("load_min")
        unload = o.get("unload_min")
        orders.append({
            "id": o["id"], "w": weight[o["machine"]], "p": o["pickup"], "d": o["delivery"],
            "hand_s": int(round(60 * ((s["load_min"] if load is None else load) + (s["unload_min"] if unload is None else unload)))),
        })
    n = len(orders)
    limit_s = Fraction(str(s["day_limit_min"])) * 60
    trucks = scenario["trucks"]

    def feasible(mask, tenths, speed):
        if mask == 0:
            return True
        drive = Fraction(tenths * 360) / Fraction(str(speed))  # sekunde
        hand = sum(orders[i]["hand_s"] for i in range(n) if mask >> i & 1)
        used = drive + hand if s["limit_includes_handling"] else drive
        return used <= limit_s

    tables = []
    for t in trucks:
        raw = truck_tables(orders, loc, depot, t["capacity_kg"], t["slots"])
        tables.append({m: km for m, km in raw.items() if feasible(m, km, t.get("speed_kmh", 60))})

    require_all = bool(s.get("require_all_trucks"))
    # f[U] = (-korišteni_kamioni ako se traže, km), izbori za rekonstrukciju
    f = {0: ((0, 0), [])}
    for j, table in enumerate(tables):
        g = {}
        for done, (key, picks) in f.items():
            for mask, km in table.items():
                if mask & done:
                    continue
                used = 1 if (mask and require_all) else 0
                nk = (key[0] - used, key[1] + km)
                U = done | mask
                if U not in g or nk < g[U][0]:
                    g[U] = (nk, picks + [mask])
        f = g
    best_U = min(f, key=lambda U: (-bin(U).count("1"), f[U][0]))
    key, picks = f[best_U]
    out_trucks = {}
    for t, mask, table in zip(trucks, picks, tables):
        out_trucks[t["id"]] = {
            "orders": [orders[i]["id"] for i in range(n) if mask >> i & 1],
            "km": round(table[mask] / 10, 1) if mask else 0.0,
        }
    return {
        "served": bin(best_U).count("1"),
        "orders": n,
        "km": round(key[1] / 10, 1),
        "trucks": out_trucks,
        "unserved": [orders[i]["id"] for i in range(n) if not best_U >> i & 1],
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    path = argv[0]
    overrides = {}
    rest = argv[1:]
    while rest:
        if rest[0] == "--set" and len(rest) > 1:
            k, v = rest[1].split("=", 1)
            overrides[k] = parse_value(v)
            rest = rest[2:]
        else:
            print(f"Nepoznat argument: {rest[0]}")
            return 2
    with open(path, encoding="utf-8") as fh:
        scenario = json.load(fh)
    print(json.dumps(solve(scenario, overrides), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
