import pytest

from uprent.domain import Scenario, apply_overrides, load_scenario
from uprent.plan import Plan
from uprent.solvers.exact import StateLimitExceeded, build_context, truck_table
from uprent.validator import validate

from conftest import DEFAULT_PATH


@pytest.fixture(scope="module")
def tables():
    scenario = load_scenario(DEFAULT_PATH)
    ids = [o.id for o in scenario.orders]
    return [truck_table(scenario, truck, ids) for truck in scenario.trucks]


def test_table_sizes(tables):
    assert [len(table) for table, _ in tables] == [32, 1024]


def test_state_count(tables, scenario):
    assert [states for _, states in tables] == [281, 65281]
    assert build_context(scenario, [o.id for o in scenario.orders]).states == 65562


def test_b_all_km(tables, scenario):
    entry = tables[1][0][frozenset(o.id for o in scenario.orders)]
    assert entry.km_tenths == 1822
    report = validate(scenario, Plan(routes={"B": entry.ops}, reported_km={"B": 182.2}))
    assert report.passed and len(report.served) == 10


def test_a_n03_km(tables):
    assert tables[0][0][frozenset(["N03"])].km_tenths == 372


def test_b_without_n03_km(tables, scenario):
    ids = frozenset(o.id for o in scenario.orders if o.id != "N03")
    assert tables[1][0][ids].km_tenths == 1629


def test_empty_subset_zero(tables):
    for table, _ in tables:
        empty = table[frozenset()]
        assert empty.km_tenths == 0 and empty.ops == []


def test_shared_table_same_type(scenario_data):
    scenario_data["trucks"].append({**scenario_data["trucks"][0], "id": "C", "speed_kmh": 35})
    s = Scenario.model_validate(scenario_data)
    ctx = build_context(s, [o.id for o in s.orders])
    assert ctx.tables["A"] is ctx.tables["C"]
    assert ctx.states == 65562


def test_pins_not_applied_to_tables(scenario):
    s = apply_overrides(scenario, {"pinned_orders": {"N04": "A"}})
    ctx = build_context(s, ["N04"])
    assert frozenset(["N04"]) in ctx.tables["B"]
    assert ctx.tables["B"][frozenset(["N04"])].km_tenths == 384


def test_state_cap_raises(scenario_data):
    scenario_data["machines"] = [{"id": f"M{i}", "weight_kg": 800} for i in range(12)]
    scenario_data["orders"] = [
        {"id": f"N{i}", "machine": f"M{i}", "pickup": "L1", "delivery": "L3"} for i in range(12)
    ]
    scenario_data["trucks"][1]["slots"] = 12
    s = Scenario.model_validate(scenario_data)
    with pytest.raises(StateLimitExceeded):
        truck_table(s, s.trucks[1], [o.id for o in s.orders], max_states=10_000)


def test_context_shares_state_budget(scenario):
    # Tri stanja po tipu kamiona: oba zasebno prolaze granicu od pet.
    with pytest.raises(StateLimitExceeded):
        build_context(scenario, ["N01"], max_states=5)


def test_deadline_raises(scenario):
    with pytest.raises(StateLimitExceeded):
        truck_table(scenario, scenario.trucks[0], [], deadline_s=0)
