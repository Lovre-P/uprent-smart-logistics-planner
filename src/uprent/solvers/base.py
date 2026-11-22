from dataclasses import dataclass, field
from typing import Literal

from uprent.plan import Plan


@dataclass
class SolverOutput:
    plan: Plan
    served: frozenset[str]
    optimality: Literal["proven", "best_found", "none"]
    solver: Literal["exact", "ortools"]
    status: str
    info: dict = field(default_factory=dict)
