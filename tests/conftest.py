import json
from pathlib import Path

import pytest


DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "default_scenario.json"


@pytest.fixture
def scenario_data():
    return json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def scenario(scenario_data):
    from uprent.domain import Scenario

    return Scenario.model_validate(scenario_data)


@pytest.fixture
def rounding_scenario(scenario_data):
    from uprent.domain import Scenario

    scenario_data.update(
        locations=[{"id": f"L{i}", "x": i * 2, "y": i * 2} for i in range(3)],
        trucks=scenario_data["trucks"][:1],
        machines=[{"id": mid, "weight_kg": 800} for mid in ["M01", "M02"]],
        orders=[
            {"id": "N01", "machine": "M01", "pickup": "L0", "delivery": "L2"},
            {"id": "N02", "machine": "M02", "pickup": "L1", "delivery": "L0"},
        ],
    )
    scenario_data["settings"].update(day_limit_min=11.3, allow_partial=False)
    return Scenario.model_validate(scenario_data)
