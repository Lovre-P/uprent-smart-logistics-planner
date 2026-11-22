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
