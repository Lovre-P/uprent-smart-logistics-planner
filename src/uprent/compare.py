"""Usporedba postavki i provjera istog rasporeda prema četirima tumačenjima."""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from uprent.domain import Scenario, Settings, apply_overrides
from uprent.plan import Plan
from uprent.result import SolveResult
from uprent.service import solve
from uprent.validator import validate


class Preset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    overrides: dict[str, object]
    truck_overrides: dict[str, object] | None = None


class ComparisonRow(BaseModel):
    label: str
    km: float
    served: int
    orders: int
    trucks_used: int
    valid_under: list[str]


PRESETS = (
    Preset(label="Zadano (doslovno tumačenje)", overrides={}),
    Preset(label="U 9 h ulazi utovar/istovar", overrides={"limit_includes_handling": True}),
    Preset(label="Svaki kamion mora voziti", overrides={"require_all_trucks": True}),
    Preset(label="9 h s utovarom, 20 min po nalogu",
           overrides={"limit_includes_handling": True, "load_min": 10, "unload_min": 10}),
    Preset(label="Najraniji završetak", overrides={"objective": "makespan"}),
    Preset(label="Jedan stroj odjednom", overrides={}, truck_overrides={"slots": 1}),
)


def _valid_under(scenario: Scenario, result: SolveResult) -> list[str]:
    if not result.validation.passed or result.status in {"NO_FULL_PLAN", "NOT_FOUND", "INVALID_PLAN"}:
        return []
    routes = {truck.id: [(step.action, step.order) for step in truck.steps if step.action != "RETURN"]
              for truck in result.trucks}
    plan = Plan(routes=routes)
    readings = [
        ("samo vožnja", False, 20, False),
        ("vožnja + radnje (20 min)", True, 20, False),
        ("vožnja + radnje (10 + 10)", True, 10, False),
        ("svaki kamion vozi", False, 20, True),
    ]
    labels = []
    for label, strict, handling, all_trucks in readings:
        changed = apply_overrides(scenario, {"limit_includes_handling": strict, "load_min": handling,
                                             "unload_min": handling, "require_all_trucks": all_trucks})
        report = validate(changed, plan)
        if report.passed and (not all_trucks or all(truck.used for truck in report.trucks)):
            labels.append(label)
    return labels


def compare(scenario: Scenario, presets: Sequence[Preset] = PRESETS) -> list[ComparisonRow]:
    # Ugrađeni primjeri počinju od doslovnog tumačenja. Vlastite varijante
    # nadograđuju trenutačne postavke. Flota, lokacije i nalozi su isti.
    base = scenario
    if presets is PRESETS:
        interpretation = {"limit_includes_handling", "require_all_trucks", "load_min", "unload_min", "objective"}
        base = apply_overrides(scenario, Settings().model_dump(include=interpretation))
    rows = []
    for preset in presets:
        changed = apply_overrides(base, preset.overrides)
        if preset.truck_overrides:
            data = changed.model_dump()
            for truck in data["trucks"]:
                truck.update(preset.truck_overrides)
            changed = Scenario.model_validate(data)
        result = solve(changed, include_analysis=False)
        rows.append(ComparisonRow(label=preset.label, **result.totals.model_dump(),
                                  valid_under=_valid_under(changed, result)))
    return rows
