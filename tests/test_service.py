import pytest

from fixtures.routes import B_ALONE, ops
from uprent import service
from uprent.domain import Scenario, ScenarioError, apply_overrides
from uprent.plan import Plan
from uprent.solvers.base import SolverOutput


def extend(data, weights):
    for index, kg in enumerate(weights, len(data["orders"]) + 1):
        mid, oid = f"M{index:02d}", f"N{index:02d}"
        data["machines"].append({"id": mid, "weight_kg": kg})
        data["orders"].append({"id": oid, "machine": mid, "pickup": "L1", "delivery": "L3"})
    return Scenario.model_validate(data)


def heavy(data):
    for machine in data["machines"]:
        machine["weight_kg"] = 12000
    return Scenario.model_validate(data)


def test_default_result(scenario):
    r = service.solve(scenario)
    assert (r.status, r.optimality, r.solver) == ("OPTIMAL", "proven", "exact")
    assert r.totals.model_dump() == {"km": 182.2, "served": 10, "orders": 10, "trucks_used": 1}
    assert not r.trucks[0].used and r.validation.passed and r.comparison is None
    assert set(r.validation.model_dump()) == {"passed", "checks"}
    assert len(r.validation.checks) == 10 and r.unserved == []


def test_n11_partial(scenario_data):
    r = service.solve(extend(scenario_data, [12000]))
    assert (r.status, r.totals.served, r.totals.orders, r.totals.km) == ("OPTIMAL_PARTIAL", 10, 11, 182.2)
    assert [(u.order, u.reason) for u in r.unserved] == [("N11", "TOO_HEAVY")]
    assert "12.000 kg" in r.unserved[0].message


def test_thirteen_orders_uses_ortools(scenario_data):
    s = apply_overrides(extend(scenario_data, [800] * 3), {"ortools_time_limit_s": 1})
    r = service.solve(s)
    assert (r.solver, r.optimality, r.validation.passed) == ("ortools", "best_found", True)
    assert all("optimal" not in msg.lower() for msg in r.messages)


def test_all_too_heavy(scenario_data):
    r = service.solve(heavy(scenario_data))
    assert r.totals.served == 0 and r.totals.orders == 10 and len(r.unserved) == 10
    assert all(u.reason == "TOO_HEAVY" for u in r.unserved)


def test_rounding_shortcut_full_plan(rounding_scenario):
    r = service.solve(rounding_scenario)
    assert (r.status, r.totals.served, r.totals.orders, r.totals.km) == ("OPTIMAL", 2, 2, 11.3)
    assert r.validation.passed


def fake_exact(monkeypatch, routes):
    plan = Plan(routes=routes)
    claimed = frozenset(order for route in routes.values() for action, order in route if action == "PICKUP")
    monkeypatch.setattr(service, "solve_exact", lambda *args, **kwargs: SolverOutput(
        plan=plan, served=claimed, optimality="proven", solver="exact", status="OPTIMAL",
    ))


def test_invalid_plan_detected(scenario, monkeypatch):
    fake_exact(monkeypatch, {"A": ops("P:N03 P:N03 D:N03")})
    r = service.solve(scenario)
    assert (r.status, r.optimality, r.validation.passed) == ("INVALID_PLAN", "none", False)
    assert r.messages and not r.analysis.why


def test_state_cap_fallback(scenario, monkeypatch):
    monkeypatch.setattr(service, "MAX_STATES", 10)
    r = service.solve(apply_overrides(scenario, {"ortools_time_limit_s": 1}), "exact")
    assert r.solver == "ortools" and r.optimality == "best_found" and r.validation.passed
    assert any("prekinut" in text for text in r.messages)


def test_analysis_after_fallback(scenario, monkeypatch):
    monkeypatch.setattr(service, "MAX_STATES", 10)
    r = service.solve(apply_overrides(scenario, {"ortools_time_limit_s": 1}))
    assert r.analysis.why == r.analysis.curve == r.analysis.alternatives == []
    assert any("egzaktni solver" in text for text in r.analysis.binding)


def test_zero_served_status(scenario_data):
    r = service.solve(heavy(scenario_data))
    assert r.status == "OPTIMAL_PARTIAL" and "Nijedan nalog nije moguće izvršiti." in r.messages


def test_heuristic_zero_does_not_claim_impossibility(rounding_scenario, monkeypatch):
    s = apply_overrides(rounding_scenario, {"allow_partial": True})
    assert service.solve(s).totals.served == 2
    monkeypatch.setattr(service, "solve_ortools", lambda *args: SolverOutput(
        Plan(routes={}), frozenset(), "best_found", "ortools", "FEASIBLE_PARTIAL",
    ))
    r = service.solve(s, "ortools")
    assert r.totals.served == 0 and r.status == "FEASIBLE_PARTIAL"
    assert "Nijedan nalog nije moguće izvršiti." not in r.messages
    assert any("nije našao rutu" in msg and "nije dokazana" in msg for msg in r.messages)


def test_unused_truck_not_invalid(scenario, monkeypatch):
    fake_exact(monkeypatch, {"B": B_ALONE})
    r = service.solve(apply_overrides(scenario, {"require_all_trucks": True}))
    assert r.validation.passed and r.status == "OPTIMAL"
    assert any("A" in msg and "nekorišten" in msg.lower() for msg in r.messages)


def test_does_not_fit_message(scenario):
    r = service.solve(apply_overrides(scenario, {"limit_includes_handling": True, "day_limit_min": 300}))
    assert r.totals.served == 8 and {u.order for u in r.unserved} == {"N08", "N09"}
    assert all(u.reason == "DOES_NOT_FIT_TOGETHER" and "Dokazano" in u.message and "8 od 10" in u.message for u in r.unserved)


def test_precheck_proves_no_full_plan_even_with_ortools(scenario_data):
    s = apply_overrides(extend(scenario_data, [12000]), {"allow_partial": False})
    r = service.solve(s, "ortools")
    assert r.status == "NO_FULL_PLAN" and r.totals.served == 0 and r.totals.orders == 11
    assert next(u for u in r.unserved if u.order == "N11").reason == "TOO_HEAVY"
    assert any("predprovjer" in msg.lower() for msg in r.messages)


def test_no_full_plan_exact_does_not_claim_all_orders_impossible(scenario):
    r = service.solve(apply_overrides(scenario, {"allow_partial": False, "limit_includes_handling": True, "day_limit_min": 300}))
    assert r.status == "NO_FULL_PLAN" and r.totals.served == 0
    assert any("8 od 10" in msg for msg in r.messages)
    assert "Nijedan nalog nije moguće izvršiti." not in r.messages


def test_ortools_partial_and_not_found_distinguished(rounding_scenario):
    s = apply_overrides(rounding_scenario, {"day_limit_min": 11.25, "ortools_time_limit_s": 1})
    full = service.solve(s, "ortools")
    assert full.status == "NOT_FOUND" and full.optimality == "none"
    assert all(u.reason == "NOT_FOUND" for u in full.unserved)
    assert full.analysis.binding and full.analysis.curve == []
    partial = service.solve(apply_overrides(s, {"allow_partial": True}), "ortools")
    assert partial.status == "FEASIBLE_PARTIAL" and partial.totals.served == 1
    assert partial.unserved[0].reason == "NOT_FOUND"


def test_zero_orders(scenario_data):
    scenario_data["orders"] = []
    r = service.solve(Scenario.model_validate(scenario_data))
    assert r.status == "OPTIMAL" and r.totals.served == r.totals.orders == 0
    assert "Nijedan nalog nije moguće izvršiti." not in r.messages


def test_zero_orders_ortools_records_requested_solver(scenario_data):
    scenario_data["orders"] = []
    r = service.solve(Scenario.model_validate(scenario_data), "ortools")
    assert (r.status, r.solver, r.optimality) == ("FEASIBLE", "ortools", "best_found")
    assert r.validation.passed and r.totals.served == r.totals.orders == 0


def test_fractional_handling_heuristic_does_not_prove_impossibility(rounding_scenario):
    data = rounding_scenario.model_dump()
    for place in data["locations"]:
        place.update(x=0, y=0)
    data["settings"].update(load_min=0.001, unload_min=0.001, day_limit_min=0.01,
                            limit_includes_handling=True, allow_partial=True, ortools_time_limit_s=1)
    s = Scenario.model_validate(data)
    assert service.solve(s).totals.served == 2
    r = service.solve(s, "ortools")
    assert (r.status, r.optimality, r.totals.served) == ("FEASIBLE_PARTIAL", "best_found", 0)
    assert "Nijedan nalog nije moguće izvršiti." not in r.messages
    assert all(u.reason == "NOT_FOUND" for u in r.unserved)


def test_precheck_proof_without_full_tables_skips_exact_analysis(rounding_scenario):
    s = apply_overrides(rounding_scenario, {"day_limit_min": 1, "allow_partial": True})
    r = service.solve(s, "ortools")
    assert r.status == "OPTIMAL_PARTIAL" and r.totals.served == 0
    assert r.analysis.alternatives == [] and r.analysis.curve == [] and r.analysis.binding
    assert any("predprovjer" in msg.lower() for msg in r.messages)


def test_precheck_proof_survives_state_guard(scenario, monkeypatch):
    s = apply_overrides(scenario, {"day_limit_min": 1})
    monkeypatch.setattr(service, "MAX_STATES", 10)
    r = service.solve(s)
    assert (r.status, r.optimality, r.totals.served) == ("OPTIMAL_PARTIAL", "proven", 0)
    assert {u.reason for u in r.unserved} == {"TOO_LONG_ALONE"}
    assert any("predprovjer" in msg.lower() for msg in r.messages)
    assert r.analysis.curve == [] and r.analysis.binding


def test_revalidates_mutated_input(scenario):
    scenario.orders[0].pickup = "L99"
    with pytest.raises(ScenarioError, match="L99"):
        service.solve(scenario)


def test_analysis_context_includes_time_excluded_orders(rounding_scenario, monkeypatch):
    s = apply_overrides(rounding_scenario, {"day_limit_min": 10, "allow_partial": True})
    captured = {}
    original = service.analyze

    def inspect_context(scenario, ctx, report, **kwargs):
        captured["ctx"] = ctx
        return original(scenario, ctx, report, **kwargs)

    monkeypatch.setattr(service, "analyze", inspect_context)
    result = service.solve(s)
    assert result.totals.served == 1
    assert {u.order: u.reason for u in result.unserved} == {"N01": "TOO_LONG_ALONE"}
    assert frozenset(["N01"]) in captured["ctx"].tables["A"]
