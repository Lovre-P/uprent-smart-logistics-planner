import inspect
import random
import re

import pytest
from hypothesis import given, settings, strategies as st

from uprent.domain import Scenario, apply_overrides
from uprent.solvers import ortools_solver
from uprent.solvers.exact import solve_exact
from uprent.solvers.ortools_solver import limit_capacity_seconds, solve_ortools
from uprent.validator import validate


def checked(s, seconds=None):
    budget = s.settings.ortools_time_limit_s if seconds is None else seconds
    output = solve_ortools(s, [o.id for o in s.orders], budget)
    report = validate(s, output.plan)
    assert report.passed, [c for c in report.checks if not c.passed]
    assert output.served == frozenset(report.served)
    return output, report


def test_default_close_to_optimum(scenario):
    out, report = checked(scenario)
    assert len(out.served) == 10 and 182.2 <= report.total_km <= 185.8
    assert out.status == "FEASIBLE" and out.optimality == "best_found"


def test_strict_close_to_optimum(scenario):
    out, report = checked(apply_overrides(scenario, {"limit_includes_handling": True}))
    assert len(out.served) == 10 and 200.1 <= report.total_km <= 204.1


def test_too_heavy_does_not_crash(scenario_data):
    scenario_data["machines"].append({"id": "M11", "weight_kg": 12000})
    scenario_data["orders"].append({"id": "N11", "machine": "M11", "pickup": "L1", "delivery": "L3"})
    out, _ = checked(Scenario.model_validate(scenario_data))
    assert len(out.served) == 10 and "N11" not in out.served
    assert out.status == "FEASIBLE_PARTIAL"


def test_require_all_trucks_soft(scenario):
    out, report = checked(apply_overrides(scenario, {"require_all_trucks": True}))
    assert len(out.served) == 10 and all(t.used for t in report.trucks)


def test_partial_strict_300(scenario):
    out, _ = checked(apply_overrides(scenario, {"limit_includes_handling": True, "day_limit_min": 300}))
    assert out.status == "FEASIBLE_PARTIAL" and 0 < len(out.served) <= 8


def test_makespan_counts_handling(scenario):
    out, report = checked(apply_overrides(scenario, {"objective": "makespan"}))
    assert len(out.served) == 10 and max(t.total_min for t in report.trucks) <= 351.7


def test_pinned_ortools(scenario):
    _, report = checked(apply_overrides(scenario, {"pinned_orders": {"N04": "A"}}))
    assert "N04" in report.trucks[0].orders and len(report.served) == 10


def test_slow_truck_capacity(scenario_data):
    scenario_data["trucks"][0]["speed_kmh"] = 30
    scenario_data["settings"]["objective"] = "makespan"
    out, _ = checked(Scenario.model_validate(scenario_data))
    assert len(out.served) == 10


def test_limit_capacity_floor():
    assert limit_capacity_seconds(60.01) == 3600
    assert limit_capacity_seconds(540) == 32400


def test_no_forbidden_patterns():
    source = inspect.getsource(ortools_solver)
    assert not re.search(r"AddDisjunction\(\[[^\]]*,[^\]]*\]", source)
    assert not re.search(r"NextVar\(.*Start.*\)\s*!=", source)


def small_scenario(seed, count):
    generator = random.Random(seed)
    locations = [{"id": f"L{i}", "x": generator.randint(-12, 12), "y": generator.randint(-12, 12)}
                 for i in range(6)]
    orders = []
    for i in range(count):
        pickup, delivery = generator.sample(locations, 2)
        orders.append({"id": f"N{i}", "machine": f"M{i}", "pickup": pickup["id"], "delivery": delivery["id"]})
    return Scenario.model_validate({
        "name": "Usporedba solvera", "depot": "L0", "locations": locations,
        "machines": [{"id": f"M{i}", "weight_kg": generator.choice((900, 2400, 3900, 6100, 9400))}
                     for i in range(count)],
        "trucks": [{"id": "A", "capacity_kg": 3500, "slots": 2, "speed_kmh": 55},
                   {"id": "B", "capacity_kg": 10000, "slots": 3, "speed_kmh": 64}],
        "orders": orders,
    })


@pytest.mark.parametrize("seed", range(10))
def test_random_ortools_never_beats_exact(seed):
    s = small_scenario(seed, 8 + seed % 3)
    exact = solve_exact(s)
    reference = validate(s, exact.plan)
    assert reference.passed
    _, report = checked(s, 0.16)
    assert (-len(reference.served), reference.total_km) <= (-len(report.served), report.total_km)


@settings(max_examples=14, deadline=None, derandomize=True)
@given(seed=st.integers(0, 65535), count=st.integers(0, 5),
       limit=st.integers(10, 540), strict=st.booleans(), require_all=st.booleans())
def test_small_plans_pass_validator(seed, count, limit, strict, require_all):
    s = apply_overrides(small_scenario(seed, count), {
        "day_limit_min": limit, "limit_includes_handling": strict, "require_all_trucks": require_all,
    })
    assert validate(s, solve_exact(s).plan).passed
    checked(s, 0.08)


def test_full_only_failure_has_no_proof(scenario):
    s = apply_overrides(scenario, {"allow_partial": False, "day_limit_min": 1})
    out, report = checked(s, 0.12)
    assert out.status == "NOT_FOUND" and out.optimality == "none" and not report.served


def test_empty_orders(scenario_data):
    scenario_data["orders"] = []
    out, report = checked(Scenario.model_validate(scenario_data), 0.1)
    assert out.status == "FEASIBLE" and not out.served and report.total_km == 0


def test_zero_time_pickups_precede_delivery(scenario_data):
    for location in scenario_data["locations"]:
        location.update(x=0, y=0)
    scenario_data["settings"].update(load_min=0, unload_min=0, pinned_orders={"N04": "A"})
    out, report = checked(Scenario.model_validate(scenario_data), 0.2)
    assert len(out.served) == 10 and report.total_km == 0
    assert "N04" in report.trucks[0].orders


def test_conservative_fractional_service_time(scenario_data):
    scenario_data["orders"] = [scenario_data["orders"][0]]
    scenario_data["orders"][0].update(load_min=0.01, unload_min=0.01)
    for location in scenario_data["locations"]:
        location.update(x=0, y=0)
    scenario_data["settings"].update(limit_includes_handling=True, day_limit_min=0.019)
    out, _ = checked(Scenario.model_validate(scenario_data), 0.1)
    assert not out.served


def test_pinned_on_slow_truck_can_be_omitted(scenario_data):
    scenario_data["trucks"][0]["speed_kmh"] = 30
    scenario_data["settings"].update(pinned_orders={"N04": "A"}, day_limit_min=60)
    out, _ = checked(Scenario.model_validate(scenario_data), 0.3)
    assert "N04" not in out.served and out.served
