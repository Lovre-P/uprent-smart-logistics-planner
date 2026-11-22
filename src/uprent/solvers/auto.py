from typing import Literal

from uprent.domain import Scenario


def choose_solver(scenario: Scenario, n_orders: int) -> Literal["exact", "ortools"]:
    settings = scenario.settings
    if settings.solver != "auto":
        return settings.solver
    if n_orders <= settings.exact_max_orders and len(scenario.trucks) <= settings.exact_max_trucks:
        return "exact"
    return "ortools"
