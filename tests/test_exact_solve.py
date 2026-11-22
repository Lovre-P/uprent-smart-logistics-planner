import random
from time import perf_counter

import pytest

from uprent.domain import Scenario, ScenarioError, apply_overrides
from uprent.solvers.exact import build_context, full_plan_assignments, solve_exact
from uprent.validator import validate


def result(s, **settings):
    s = apply_overrides(s, settings)
    output = solve_exact(s)
    report = validate(s, output.plan)
    assert report.passed
    assert set(report.served) == output.served
    return output, report


def test_default_literal(scenario):
    output, report = result(scenario)
    assert (report.total_km, len(output.served), report.trucks[0].used) == (182.2, 10, False)
    assert output.optimality == "proven" and output.status == "OPTIMAL"


def test_handling_counts(scenario):
    _, r = result(scenario, limit_includes_handling=True)
    assert r.total_km == 200.1 and r.trucks[0].orders == ["N03"]


def test_require_all_trucks(scenario):
    _, r = result(scenario, require_all_trucks=True)
    assert r.total_km == 200.1 and all(t.used for t in r.trucks)


@pytest.mark.parametrize("minutes", [0, 30])
def test_handling_time_drive_mode(scenario, minutes):
    assert result(scenario, load_min=minutes, unload_min=minutes)[1].total_km == 182.2


@pytest.mark.parametrize("minutes,km", [(17, 182.2), (20, 200.1), (21, 217), (25, 235.1), (30, 254.9), (10, 182.2)])
def test_handling_time_strict(scenario, minutes, km):
    _, r = result(scenario, limit_includes_handling=True, load_min=minutes, unload_min=minutes)
    assert r.total_km == km and len(r.served) == 10


@pytest.mark.parametrize("limit,served,km", [(180, 10, 200.1), (150, 10, 239.2), (140, 9, None), (100, 7, None)])
def test_drive_limit(scenario, limit, served, km):
    _, r = result(scenario, day_limit_min=limit)
    assert len(r.served) == served
    if km is not None:
        assert r.total_km == km


@pytest.mark.parametrize("limit,served,km", [(480, 10, 235.1), (330, 9, None), (300, 8, 203.8), (345, 10, 284.2)])
def test_strict_day_limit(scenario, limit, served, km):
    _, r = result(scenario, limit_includes_handling=True, day_limit_min=limit)
    assert len(r.served) == served
    if km is not None:
        assert r.total_km == km


def test_no_partial(scenario):
    output, r = result(scenario, allow_partial=False, limit_includes_handling=True, day_limit_min=300)
    assert output.status == "NO_FULL_PLAN" and not r.served


def test_makespan(scenario):
    _, r = result(scenario, objective="makespan")
    assert (r.total_km, max(t.total_min for t in r.trucks)) == (284.2, 344.8)


def test_pinned_single(scenario):
    _, r = result(scenario, pinned_orders={"N04": "A"})
    assert r.total_km == 217.0 and set(r.trucks[0].orders) == {"N01", "N04"}


def test_pinned_all(scenario):
    pins = {o.id: ("A" if o.id == "N04" else "B") for o in scenario.orders}
    _, r = result(scenario, pinned_orders=pins)
    assert r.total_km == 218.8 and r.trucks[0].orders == ["N04"]


def test_pinned_too_heavy(scenario):
    with pytest.raises(ScenarioError):
        result(scenario, pinned_orders={"N06": "A"})


def test_pinned_not_forced(scenario_data):
    scenario_data["trucks"][0]["speed_kmh"] = 30
    output, r = result(Scenario.model_validate(scenario_data), day_limit_min=60, pinned_orders={"N04": "A"})
    assert output.status == "OPTIMAL_PARTIAL" and "N04" not in r.served and r.served


def test_makespan_require_all_trucks(scenario_data):
    scenario_data["trucks"].append({**scenario_data["trucks"][1], "id": "C", "speed_kmh": 10})
    _, r = result(Scenario.model_validate(scenario_data), objective="makespan", require_all_trucks=True)
    assert len(r.served) == 10 and all(t.used for t in r.trucks)


def test_makespan_three_trucks_fast(scenario_data):
    rng = random.Random(31)
    weights = [m["weight_kg"] for m in scenario_data["machines"]] + [6100, 7500]
    rng.shuffle(weights)
    s = scenario_data
    s["machines"] = [{"id": f"M{i}", "weight_kg": w} for i, w in enumerate(weights)]
    locations = [p["id"] for p in s["locations"]]
    s["orders"] = []
    for i in range(12):
        start, end = rng.sample(locations, 2)
        s["orders"].append({"id": f"N{i}", "machine": f"M{i}", "pickup": start, "delivery": end})
    s["trucks"].append({**s["trucks"][1], "id": "C", "speed_kmh": 55})
    start = perf_counter()
    output, r = result(Scenario.model_validate(s), objective="makespan")
    assert perf_counter() - start < 10
    assert output.status == "OPTIMAL" and len(r.served) == 12


@pytest.mark.parametrize("strict,km", [(False, 209), (True, 226)])
def test_single_slot(scenario_data, strict, km):
    for truck in scenario_data["trucks"]:
        truck["slots"] = 1
    assert result(Scenario.model_validate(scenario_data), limit_includes_handling=strict)[1].total_km == km


def test_zero_orders(scenario_data):
    scenario_data["orders"] = []
    output, r = result(Scenario.model_validate(scenario_data))
    assert (output.status, r.total_km, r.served) == ("OPTIMAL", 0, [])


def test_slots_only_truck_a(scenario_data):
    s = scenario_data
    s["trucks"] = s["trucks"][:1]
    s["machines"] = [{"id": f"M{i}", "weight_kg": 800} for i in range(4)]
    s["orders"] = [{"id": f"N{i}", "machine": f"M{i}", "pickup": "L1", "delivery": "L3"} for i in range(4)]
    _, r = result(Scenario.model_validate(s))
    assert len(r.served) == 4 and r.trucks[0].peak_slots <= 2


def test_explicit_empty_order_ids(scenario):
    assert solve_exact(scenario, order_ids=[]).served == frozenset()


def test_complete_assignments_respect_pins_and_limits(scenario):
    s = apply_overrides(scenario, {"pinned_orders": {"N03": "A"}, "limit_includes_handling": True})
    ctx = build_context(s, [o.id for o in s.orders])
    assignments = full_plan_assignments(s, ctx)
    assert assignments and min(a.km_tenths for a in assignments) == 2001
    assert all("N03" in a.by_truck["A"] and a.end_seconds <= 540 * 60 for a in assignments)
