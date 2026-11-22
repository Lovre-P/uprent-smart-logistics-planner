from fractions import Fraction
from pathlib import Path

import pytest

from uprent.domain import Scenario, ScenarioError, Settings, apply_overrides, load_scenario


def test_default_scenario_loads():
    path = Path(__file__).resolve().parents[1] / "data" / "default_scenario.json"
    s = load_scenario(path)
    assert (len(s.locations), len(s.machines), len(s.trucks), len(s.orders)) == (10, 10, 2, 10)
    assert s.settings.limit_includes_handling is False
    assert s.settings.require_all_trucks is False
    assert s.settings.load_min == 20


def test_missing_settings_use_defaults(scenario_data):
    del scenario_data["settings"]
    assert Scenario.model_validate(scenario_data).settings == Settings()


def test_rejects_unknown_location(scenario_data):
    scenario_data["orders"][0]["pickup"] = "L99"
    with pytest.raises(ScenarioError) as exc:
        Scenario.model_validate(scenario_data)
    assert "nepoznata lokacija" in str(exc.value) and "N01" in str(exc.value)


def test_rejects_same_pickup_and_delivery(scenario_data):
    scenario_data["orders"][0]["delivery"] = "L1"
    with pytest.raises(ScenarioError, match="isto mjesto"):
        Scenario.model_validate(scenario_data)


def test_rejects_machine_in_two_orders(scenario_data):
    scenario_data["orders"][1]["machine"] = "M01"
    with pytest.raises(ScenarioError) as exc:
        Scenario.model_validate(scenario_data)
    assert "M01" in str(exc.value) and "dva naloga" in str(exc.value)


@pytest.mark.parametrize("entity", ["locations", "machines", "trucks", "orders"])
def test_rejects_duplicate_ids(scenario_data, entity):
    scenario_data[entity][1]["id"] = scenario_data[entity][0]["id"]
    with pytest.raises(ScenarioError, match=entity):
        Scenario.model_validate(scenario_data)


def test_rejects_nonpositive_speed(scenario_data):
    scenario_data["trucks"][0]["speed_kmh"] = 0
    with pytest.raises(ScenarioError, match="speed_kmh"):
        Scenario.model_validate(scenario_data)


def test_rejects_zero_slots(scenario_data):
    scenario_data["trucks"][0]["slots"] = 0
    with pytest.raises(ScenarioError, match="slots"):
        Scenario.model_validate(scenario_data)


def test_rejects_negative_handling(scenario_data):
    scenario_data["orders"][0]["load_min"] = -1
    with pytest.raises(ScenarioError, match="load_min"):
        Scenario.model_validate(scenario_data)


def test_apply_overrides_parses_types(scenario):
    revised = apply_overrides(scenario, {"limit_includes_handling": "true", "load_min": "10"})
    assert revised.settings.limit_includes_handling is True
    assert revised.settings.load_min == 10.0
    assert scenario.settings.load_min == 20


def test_apply_overrides_json(scenario):
    revised = apply_overrides(scenario, {"pinned_orders": '{"N04":"A"}'})
    assert revised.settings.pinned_orders == {"N04": "A"}
    assert Scenario.model_validate({**scenario.model_dump(), "settings": {"pinned_orders": '{"N04":"A"}'}}).settings.pinned_orders == {"N04": "A"}


def test_rejects_empty_trucks(scenario_data):
    scenario_data["trucks"] = []
    with pytest.raises(ScenarioError, match="trucks"):
        Scenario.model_validate(scenario_data)


def test_rejects_unknown_depot(scenario_data):
    scenario_data["depot"] = "L99"
    with pytest.raises(ScenarioError, match="depot"):
        Scenario.model_validate(scenario_data)


@pytest.mark.parametrize("value", ["7h", "24:00", "07:60"])
def test_rejects_bad_day_start(scenario, value):
    with pytest.raises(ScenarioError, match="day_start"):
        apply_overrides(scenario, {"day_start": value})


@pytest.mark.parametrize("value", [0, 31])
def test_rejects_bad_ortools_limit(scenario, value):
    with pytest.raises(ScenarioError, match="ortools_time_limit_s"):
        apply_overrides(scenario, {"ortools_time_limit_s": value})


@pytest.mark.parametrize("pins,message", [
    ({"N12": "A"}, "N12"), ({"N01": "Q"}, "Q"), ({"N06": "A"}, "3.500 kg"),
])
def test_pinned_validation(scenario, pins, message):
    with pytest.raises(ScenarioError) as exc:
        apply_overrides(scenario, {"pinned_orders": pins})
    assert message in str(exc.value)
    assert next(iter(pins)) in str(exc.value)


def test_order_handling_precedence_and_fractional_seconds(scenario_data):
    scenario_data["orders"][0].update(load_min=0, unload_min=0.01)
    s = apply_overrides(Scenario.model_validate(scenario_data), {"load_min": 5, "unload_min": 12})
    assert s.handling_seconds("N01") == (0, Fraction(3, 5))
    assert s.handling_seconds("N02") == (300, 720)


@pytest.mark.parametrize("settings, field", [
    ({"bad_setting": True}, "bad_setting"), ({"solver": "xyz"}, "solver"),
    ({"pinned_orders": "{bad"}, "pinned_orders"), ({"pinned_orders": "[]"}, "pinned_orders"),
    ({"day_limit_min": 0}, "day_limit_min"), ({"load_min": "nan"}, "load_min"),
])
def test_rejects_invalid_settings(scenario, settings, field):
    with pytest.raises(ScenarioError, match=field):
        apply_overrides(scenario, settings)


@pytest.mark.parametrize("entity,field,value", [
    ("locations", "x", float("inf")), ("machines", "weight_kg", 0),
    ("trucks", "capacity_kg", 0), ("orders", "machine", "M99"),
])
def test_rejects_invalid_entity(scenario_data, entity, field, value):
    scenario_data[entity][0][field] = value
    with pytest.raises(ScenarioError, match=field):
        Scenario.model_validate(scenario_data)


def test_rejects_empty_locations(scenario_data):
    scenario_data["locations"] = []
    with pytest.raises(ScenarioError, match="locations"):
        Scenario.model_validate(scenario_data)
