from uprent.domain import Scenario, apply_overrides
from uprent.precheck import eligible_trucks, min_route_tenths, precheck


def test_too_heavy(scenario_data):
    scenario_data["machines"].append({"id": "M11", "weight_kg": 12000})
    scenario_data["orders"].append({"id": "N11", "machine": "M11", "pickup": "L1", "delivery": "L3"})
    reason = precheck(Scenario.model_validate(scenario_data))["N11"]
    assert reason.order == "N11" and reason.code == "TOO_HEAVY"
    assert reason.message == "N11 nije moguće izvršiti: stroj M11 teži 12.000 kg, a najveća nosivost kamiona je 10.000 kg."


def test_too_long_alone_drive(scenario):
    reasons = precheck(apply_overrides(scenario, {"day_limit_min": 60}))
    assert reasons["N06"].code == "TOO_LONG_ALONE" and "60,2" in reasons["N06"].message
    assert "N09" not in reasons


def test_too_long_alone_with_handling(scenario):
    reasons = precheck(apply_overrides(scenario, {"day_limit_min": 90, "limit_includes_handling": True}))
    assert reasons["N06"].code == "TOO_LONG_ALONE" and "100,2" in reasons["N06"].message


def test_eligible_trucks(scenario):
    assert eligible_trucks(scenario, "N10") == ["B"]
    assert eligible_trucks(scenario, "N01") == ["A", "B"]


def test_too_long_alone_pinned(scenario_data):
    scenario_data["trucks"][0]["speed_kmh"] = 30
    scenario_data["settings"].update(day_limit_min=60, pinned_orders={"N04": "A"})
    s = Scenario.model_validate(scenario_data)
    assert eligible_trucks(s, "N04") == ["A"]
    reason = precheck(s)["N04"]
    assert reason.code == "TOO_LONG_ALONE" and "76,8" in reason.message


def test_min_route_task_data(scenario):
    assert [min_route_tenths(scenario, oid) for oid in ["N06", "N09", "N04"]] == [602, 345, 384]


def test_rounding_shortcut_not_excluded(rounding_scenario):
    assert min_route_tenths(rounding_scenario, "N01") == 112
    assert "N01" not in precheck(rounding_scenario)
