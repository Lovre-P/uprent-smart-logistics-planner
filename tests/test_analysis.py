import pytest

from uprent.analysis import analyze
from uprent.domain import Scenario, apply_overrides
from uprent.service import solve
from uprent.solvers.exact import solve_exact
from uprent.validator import validate


@pytest.fixture
def default(scenario):
    return solve(scenario).analysis


def test_why_default(default):
    rows = {row.order: row for row in default.why}
    for oid, (km, delta) in {
        "N03": (200.1, 17.9), "N01": (217, 34.8), "N04": (217, 34.8),
        "N05": (220.1, 37.9), "N02": (231.5, 49.3),
    }.items():
        assert (rows[oid].other_km, rows[oid].delta_km, rows[oid].delta_objective) == (km, delta, delta)
        assert rows[oid].other_truck == "A"
    assert rows["N04"].other_truck_orders == ["N01", "N04"]
    assert all("3.500 kg" in rows[f"N{i:02}"].impossible for i in range(6, 11))


def test_unused_truck_sentence(default):
    assert default.unused_trucks[0].truck == "A"
    assert default.unused_trucks[0].message == (
        "Kamion A nije korišten: B stigne sve sam, a svaki nalog prebačen na A dodao bi najmanje 17,9 km."
    )


def test_alternatives_default(default):
    assert [(a.setting, a.value, a.km) for a in default.alternatives] == [
        ("limit_includes_handling", True, 200.1), ("require_all_trucks", True, 200.1),
    ]
    assert all(a.served == 10 and a.trucks_used == 2 and "A vozi N03" in a.summary for a in default.alternatives)


def test_binding_default(default):
    assert any("Limit vožnje nije aktivan" in text and "3 h 02 min" in text for text in default.binding)


def test_binding_distinguishes_route_slack_from_better_plan(scenario):
    a = solve(apply_overrides(scenario, {"day_limit_min": 180})).analysis
    assert a.sensitivity.better_plan_at_min == 182.2
    assert all("nije aktivan" not in text for text in a.binding)
    assert any("182,2 min" in text and "bolji plan" in text for text in a.binding)


def test_sensitivity_default(default):
    assert "182,2 min" in default.sensitivity.note and "ne mijenja plan" in default.sensitivity.note


def test_sensitivity_strict(scenario):
    analysis = solve(apply_overrides(scenario, {"limit_includes_handling": True})).analysis
    s = analysis.sensitivity
    assert (s.handling_max_min, s.next_plan_km, s.limit_lower_min) == (20.95, 217, 522.9)
    assert "uz 217,0 km" in s.note
    assert (s.better_plan_at_min, s.better_plan_km) == (582.2, 182.2)
    assert any("17,1" in text for text in analysis.binding)


def test_sensitivity_limit_basis_drive(default):
    s = default.sensitivity
    assert (s.limit_basis, s.limit_lower_min, s.better_plan_at_min, s.handling_max_min) == ("drive", 182.2, None, None)


@pytest.mark.parametrize("order_override", [False, True])
def test_sensitivity_hidden_for_mixed_handling(scenario_data, order_override):
    if order_override:
        scenario_data["orders"][0]["load_min"] = 20
    else:
        scenario_data["settings"]["unload_min"] = 15
    s = solve(Scenario.model_validate(scenario_data)).analysis.sensitivity
    assert s.handling_max_min is None and ("različit" in s.note or "vlastit" in s.note)


@pytest.mark.parametrize("patch", [{"objective": "makespan"}, {"require_all_trucks": True}])
def test_better_plan_full_key(scenario, patch):
    assert solve(apply_overrides(scenario, patch)).analysis.sensitivity.better_plan_at_min is None


def test_handling_max_skips_unused(scenario):
    s = apply_overrides(scenario, {"limit_includes_handling": True, "day_limit_min": 600})
    assert solve(s).analysis.sensitivity.handling_max_min == pytest.approx(20.89)


def test_analysis_requires_exact_result(scenario):
    output = solve_exact(scenario)
    a = analyze(scenario, None, validate(scenario, output.plan))
    assert a.curve == a.why == a.alternatives == []
    assert any("egzaktni solver" in text for text in a.binding)
    assert all("nije aktivan" not in text for text in a.binding)


def test_handling_max_no_used_trucks(scenario_data):
    scenario_data["orders"] = []
    scenario_data["settings"]["limit_includes_handling"] = True
    s = solve(Scenario.model_validate(scenario_data)).analysis.sensitivity
    assert s.handling_max_min is None and "nije primjenjivo" in s.note


@pytest.mark.parametrize("required,count,start", [(False, 14, (182.2, 582.2)), (True, 13, (200.1, 522.9))])
def test_curve_default(scenario, required, count, start):
    points = solve(apply_overrides(scenario, {"require_all_trucks": required})).analysis.curve
    assert len(points) == count
    assert (points[0].km, points[0].end_min) == start
    assert (points[-1].km, points[-1].end_min) == (284.2, 344.8)
    assert all(a.km < b.km and a.end_min > b.end_min for a, b in zip(points, points[1:]))
    assert all(sum(map(len, p.by_truck.values())) == 10 for p in points)


def test_partial_has_no_full_curve_or_upper_limit(scenario):
    s = apply_overrides(scenario, {"limit_includes_handling": True, "day_limit_min": 300})
    a = solve(s).analysis
    assert not a.curve and a.sensitivity.better_plan_at_min is None
    assert a.sensitivity.limit_lower_min is not None and any("potpuni plan" in text for text in a.binding)
    assert not {"N08", "N09"}.intersection(row.order for row in a.why)


def test_slow_solve_defers_work_until_requested(scenario):
    output = solve_exact(scenario)
    report = validate(scenario, output.plan)
    ctx = output.info["context"]
    a = analyze(scenario, ctx, report, elapsed_s=2.1)
    assert not a.alternatives and a.sensitivity.limit_lower_min is None
    assert next(row for row in a.why if row.order == "N03").lazy
    detailed = analyze(scenario, ctx, report, elapsed_s=2.1, detailed=True)
    assert len(detailed.alternatives) == 2 and detailed.sensitivity.limit_lower_min == 182.2


def test_three_trucks_why_is_lazy(scenario_data):
    scenario_data["trucks"].append({**scenario_data["trucks"][0], "id": "C"})
    a = solve(Scenario.model_validate(scenario_data)).analysis
    assert all(row.lazy for row in a.why if not row.impossible)


def test_why_keeps_other_existing_pins(scenario):
    s = apply_overrides(scenario, {"pinned_orders": {"N03": "A"}})
    row = next(r for r in solve(s).analysis.why if r.order == "N04" and r.other_truck == "A")
    assert {"N03", "N04"}.issubset(row.other_truck_orders)


def test_analysis_guard_keeps_plan_and_discards_incomplete_frontier(scenario, monkeypatch):
    from uprent import analysis
    monkeypatch.setattr(analysis, "MAX_ASSIGNMENTS", 1, raising=False)
    r = solve(scenario)
    assert r.status == "OPTIMAL" and r.totals.km == 182.2
    assert not r.analysis.curve and r.analysis.sensitivity.better_plan_at_min is None
    assert "gornja granica" in r.analysis.sensitivity.note
    assert any("prekinut" in note.lower() for note in r.analysis.binding)
    assert all("nije aktivan" not in text for text in r.analysis.binding)


def test_many_trucks_one_order_exact_analysis(scenario_data):
    s = scenario_data
    s["orders"] = s["orders"][:1]
    s["trucks"] = [{**s["trucks"][0], "id": f"T{i}"} for i in range(1050)]
    r = solve(Scenario.model_validate(s), "exact")
    assert r.status == "OPTIMAL" and r.totals.served == 1
    assert len(r.analysis.curve) == 1
