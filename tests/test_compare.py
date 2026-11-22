import pytest

from uprent.compare import PRESETS, Preset, compare
from uprent.domain import Scenario, ScenarioError, apply_overrides, load_scenario

from conftest import DEFAULT_PATH


@pytest.fixture(scope="module")
def default_rows():
    return compare(load_scenario(DEFAULT_PATH))


def test_presets_values(default_rows):
    assert [row.label for row in default_rows] == [p.label for p in PRESETS]
    assert [row.km for row in default_rows] == [182.2, 200.1, 200.1, 182.2, 284.2, 209.0]
    assert all((row.served, row.orders) == (10, 10) for row in default_rows)
    assert [row.trucks_used for row in default_rows][:3] == [1, 2, 2]


def test_valid_under(default_rows):
    assert default_rows[0].valid_under == ["samo vožnja", "vožnja + radnje (10 + 10)"]
    assert default_rows[1].valid_under == [
        "samo vožnja", "vožnja + radnje (20 min)", "vožnja + radnje (10 + 10)", "svaki kamion vozi",
    ]


def test_custom_comparison_preserves_input(scenario):
    before = scenario.model_dump()
    custom = Preset(label="Jedan stroj", overrides={}, truck_overrides={"slots": 1})
    assert compare(scenario, [custom])[0].km == 209.0
    assert scenario.model_dump() == before
    assert compare(scenario, []) == []


def test_builtin_readings_have_a_literal_baseline(scenario):
    current = apply_overrides(scenario, {"limit_includes_handling": True})
    assert compare(current)[0].km == 182.2
    assert compare(current, [Preset(label="Trenutačne postavke", overrides={})])[0].km == 200.1


def test_no_full_plan_has_no_validity_labels(scenario_data):
    scenario_data["settings"].update(limit_includes_handling=True, day_limit_min=60, allow_partial=False)
    rows = compare(Scenario.model_validate(scenario_data), [Preset(label="Kratka smjena", overrides={})])
    assert rows[0].served == 0 and rows[0].valid_under == []


def test_custom_variant_revalidated(scenario):
    with pytest.raises(ScenarioError, match="slots"):
        compare(scenario, [Preset(label="Mjesta", overrides={}, truck_overrides={"slots": 0})])
