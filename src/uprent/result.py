"""Javni oblik rezultata koji dijele naredbeni redak i web-sučelje."""

from typing import Literal

from pydantic import BaseModel, Field

from uprent.domain import Settings
from uprent.validator import Check, TruckView


class Totals(BaseModel):
    km: float
    served: int
    orders: int
    trucks_used: int


class Unserved(BaseModel):
    order: str
    reason: Literal["TOO_HEAVY", "TOO_LONG_ALONE", "DOES_NOT_FIT_TOGETHER", "NOT_FOUND"]
    message: str


class Validation(BaseModel):
    passed: bool
    checks: list[Check]


class WhyRow(BaseModel):
    order: str
    truck: str
    other_truck: str
    other_km: float | None = None
    delta_km: float | None = None
    delta_objective: float | None = None
    other_truck_orders: list[str] = Field(default_factory=list)
    impossible: str | None = None
    lazy: bool = False


class UnusedTruck(BaseModel):
    truck: str
    message: str


class Alternative(BaseModel):
    setting: Literal["limit_includes_handling", "require_all_trucks"]
    value: bool
    km: float
    served: int
    trucks_used: int
    summary: str


class Sensitivity(BaseModel):
    limit_basis: Literal["drive", "drive+handling"]
    limit_lower_min: float | None = None
    better_plan_at_min: float | None = None
    better_plan_km: float | None = None
    handling_max_min: float | None = None
    next_plan_km: float | None = None
    note: str = ""


class CurvePoint(BaseModel):
    km: float
    end_min: float
    by_truck: dict[str, list[str]]


class Analysis(BaseModel):
    why: list[WhyRow] = Field(default_factory=list)
    unused_trucks: list[UnusedTruck] = Field(default_factory=list)
    alternatives: list[Alternative] = Field(default_factory=list)
    binding: list[str] = Field(default_factory=list)
    sensitivity: Sensitivity
    curve: list[CurvePoint] = Field(default_factory=list)


class SolveResult(BaseModel):
    status: Literal["OPTIMAL", "OPTIMAL_PARTIAL", "FEASIBLE", "FEASIBLE_PARTIAL", "NO_FULL_PLAN", "NOT_FOUND", "INVALID_PLAN"]
    optimality: Literal["proven", "best_found", "none"]
    solver: Literal["exact", "ortools"]
    settings: Settings
    totals: Totals
    trucks: list[TruckView]
    unserved: list[Unserved]
    validation: Validation
    analysis: Analysis
    comparison: None = None
    messages: list[str]
    timings_ms: dict[str, float]
