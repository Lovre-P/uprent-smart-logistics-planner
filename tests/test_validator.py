from pathlib import Path

import pytest
from pydantic import ValidationError

from fixtures.routes import B_ALONE, BOUNDARY_A, BOUNDARY_B, STRICT_A, STRICT_B, ops
from uprent.domain import Scenario, apply_overrides
from uprent.plan import Plan
from uprent.validator import validate


def rule(report, name):
    return next(check for check in report.checks if check.rule == name)


def test_b_alone_valid_by_default(scenario):
    report = validate(scenario, Plan(routes={"B": B_ALONE}))
    a, b = report.trucks
    assert report.passed and len(report.served) == 10 and report.unserved == []
    assert len(report.checks) == 10
    assert (a.used, a.km, a.steps) == (False, 0, [])
    assert (b.km, b.drive_min, b.handling_min, b.total_min) == (182.2, 182.2, 400, 582.2)
    assert (b.peak_kg, b.peak_slots, len(b.steps)) == (9400, 3, 21)
    assert (b.limit_basis, b.slack_min) == ("drive", 357.8)
    first, last = b.steps[0], b.steps[-1]
    assert (first.seq, first.location, first.action, first.order, first.machine) == (1, "L4", "PICKUP", "N08", "M08")
    assert (first.leg_km, first.cum_km, first.load_kg, first.load_slots) == (10.8, 10.8, 6100, 1)
    assert (first.arrive, first.depart, first.onboard) == ("07:10", "07:30", ["M08"])
    assert (last.action, last.location, last.cum_km, last.onboard) == ("RETURN", "L0", 182.2, [])


def test_b_alone_invalid_when_handling_counts(scenario):
    s = apply_overrides(scenario, {"limit_includes_handling": True})
    r = validate(s, Plan(routes={"B": B_ALONE}))
    assert not r.passed and not rule(r, "vrijeme").passed
    assert "582,2" in rule(r, "vrijeme").detail


def test_strict_plan_valid(scenario):
    s = apply_overrides(scenario, {"limit_includes_handling": True})
    r = validate(s, Plan(routes={"A": STRICT_A, "B": STRICT_B}))
    a, b = r.trucks
    assert r.passed and r.total_km == 200.1
    assert (a.km, a.total_min, b.km, b.total_min, b.peak_kg) == (37.2, 77.2, 162.9, 522.9, 9900)
    assert (b.limit_basis, b.slack_min) == ("drive+handling", 17.1)


def test_boundary_plan(scenario):
    plan = Plan(routes={"A": BOUNDARY_A, "B": BOUNDARY_B})
    assert validate(scenario, plan).passed
    s = apply_overrides(scenario, {"limit_includes_handling": True})
    r = validate(s, plan)
    assert not rule(r, "vrijeme").passed and "540,4" in rule(r, "vrijeme").detail


def test_capacity_l7_swap(scenario):
    route = STRICT_B.copy()
    i = route.index(("DELIVERY", "N06"))
    route[i], route[i+1] = route[i+1], route[i]
    r = validate(scenario, Plan(routes={"B": route}))
    assert not rule(r, "kapacitet_kg").passed and "13.300" in rule(r, "kapacitet_kg").detail


def test_exact_capacity_allowed(scenario):
    r = validate(scenario, Plan(routes={"B": ops("P:N06 P:N08 D:N06 D:N08")}))
    assert rule(r, "kapacitet_kg").passed and r.trucks[1].peak_kg == 10000


def test_slots_exceeded(scenario):
    r = validate(scenario, Plan(routes={"B": ops("P:N01 P:N02 P:N03 P:N04 D:N01 D:N02 D:N03 D:N04")}))
    assert not rule(r, "mjesta").passed and "4 / 3" in rule(r, "mjesta").detail


def test_delivery_before_pickup(scenario):
    r = validate(scenario, Plan(routes={"A": ops("D:N03 P:N03")}))
    assert not rule(r, "redoslijed").passed


def test_other_truck_delivers(scenario):
    r = validate(scenario, Plan(routes={"A": ops("P:N03"), "B": ops("D:N03")}))
    assert not rule(r, "isti_kamion").passed and not rule(r, "baza").passed
    assert "N03" not in r.served


def test_double_pickup(scenario):
    r = validate(scenario, Plan(routes={"A": ops("P:N03 P:N03 D:N03")}))
    assert not rule(r, "jednom").passed


def test_machine_left_on_truck(scenario):
    r = validate(scenario, Plan(routes={"A": ops("P:N03")}))
    assert not rule(r, "baza").passed
    assert r.trucks[0].steps[-1].onboard == ["M03"]


def test_reported_km_without_return(scenario):
    r = validate(scenario, Plan(routes={"A": STRICT_A}, reported_km={"A": 26.4}))
    assert not rule(r, "km_dosljedno").passed


def test_zero_leg_handling_counted(scenario_data):
    # L9 i L4 ostaju dvije različite lokacije naloga N03.
    scenario_data["locations"][9].update(x=9, y=-6)
    s = Scenario.model_validate(scenario_data)
    r = validate(s, Plan(routes={"A": STRICT_A}))
    assert r.passed and r.trucks[0].steps[1].leg_km == 0 and r.trucks[0].handling_min == 40


def test_unused_truck_is_info(scenario):
    s = apply_overrides(scenario, {"require_all_trucks": True})
    r = validate(s, Plan(routes={"B": B_ALONE}))
    info = rule(r, "svi_kamioni")
    assert r.passed and info.severity == "info" and not info.passed and "A" in info.detail


def test_reported_unserved_mismatch(scenario):
    routes = {"A": STRICT_A, "B": STRICT_B}
    assert not rule(validate(scenario, Plan(routes=routes, reported_unserved=["N05"])), "neizvrseni_dosljedno").passed
    assert "nije primjenjivo" in rule(validate(scenario, Plan(routes=routes)), "neizvrseni_dosljedno").detail


def test_validator_does_not_import_solvers():
    source = (Path(__file__).resolve().parents[1] / "src/uprent/validator.py").read_text(encoding="utf-8")
    assert "uprent.solvers" not in source and "uprent.distance" not in source


def test_pinned_order_rejects_wrong_truck(scenario):
    s = apply_overrides(scenario, {"pinned_orders": {"N03": "A"}})
    r = validate(s, Plan(routes={"B": B_ALONE}))
    assert not r.passed and not rule(r, "isti_kamion").passed


@pytest.mark.parametrize("routes", [{"C": STRICT_A}, {"A": ops("P:N99 D:N99")}])
def test_unknown_truck_or_order(scenario, routes):
    assert not validate(scenario, Plan(routes=routes)).passed


def test_plan_rejects_malformed_action():
    with pytest.raises(ValidationError):
        Plan(routes={"A": [("RETURN", "N03")]})


def test_time_limit_compared_before_display_rounding(scenario):
    s = apply_overrides(scenario, {"day_limit_min": 37.1999})
    assert not rule(validate(s, Plan(routes={"A": STRICT_A})), "vrijeme").passed
    s = apply_overrides(scenario, {"day_limit_min": 37.2})
    assert validate(s, Plan(routes={"A": STRICT_A})).passed
