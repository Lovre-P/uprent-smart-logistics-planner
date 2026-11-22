"""Dokazive zapreke za pojedinačni nalog prije raspoređivanja."""

from fractions import Fraction
from typing import Literal

from pydantic import BaseModel

from uprent.distance import drive_seconds, leg_tenths
from uprent.domain import Order, Scenario, Truck


class Reason(BaseModel):
    order: str
    code: Literal["TOO_HEAVY", "TOO_LONG_ALONE", "DOES_NOT_FIT_TOGETHER", "NOT_FOUND"]
    message: str


def _eligible(scenario: Scenario, order: Order, weight: int) -> list[Truck]:
    pin = (scenario.settings.pinned_orders or {}).get(order.id)
    return [t for t in scenario.trucks if t.capacity_kg >= weight and (pin is None or pin == t.id)]


def eligible_trucks(scenario: Scenario, order_id: str) -> list[str]:
    order = next(o for o in scenario.orders if o.id == order_id)
    weight = next(m.weight_kg for m in scenario.machines if m.id == order.machine)
    return [truck.id for truck in _eligible(scenario, order, weight)]


def _shortest_paths(scenario: Scenario) -> dict[str, dict[str, int]]:
    stops = {scenario.depot}
    for order in scenario.orders:
        stops.update((order.pickup, order.delivery))
    places = [p for p in scenario.locations if p.id in stops]
    paths = {a.id: {b.id: leg_tenths(a, b) for b in places} for a in places}
    for via, onwards in paths.items():
        for row in paths.values():
            to_via = row[via]
            for destination, remaining in onwards.items():
                candidate = to_via + remaining
                if candidate < row[destination]:
                    row[destination] = candidate
    return paths


def _bound(paths: dict[str, dict[str, int]], depot: str, order: Order) -> int:
    return paths[depot][order.pickup] + paths[order.pickup][order.delivery] + paths[order.delivery][depot]


def min_route_tenths(scenario: Scenario, order_id: str) -> int:
    order = next(o for o in scenario.orders if o.id == order_id)
    return _bound(_shortest_paths(scenario), scenario.depot, order)


def _kg(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _minute_text(seconds: Fraction) -> str:
    value = seconds / 60
    if value.denominator == 1:
        return str(value.numerator)
    # Ne zaokružuj donju granicu naviše u obrazloženju dokaza.
    if (value * 10).denominator == 1:
        return f"{float(value):.1f}".replace(".", ",")
    return f"{value.numerator}/{value.denominator}"


def precheck(scenario: Scenario) -> dict[str, Reason]:
    paths = _shortest_paths(scenario)
    weights = {m.id: m.weight_kg for m in scenario.machines}
    max_capacity = max(truck.capacity_kg for truck in scenario.trucks)
    limit = Fraction(str(scenario.settings.day_limit_min)) * 60
    reasons = {}
    for order in scenario.orders:
        weight = weights[order.machine]
        allowed = _eligible(scenario, order, weight)
        if not allowed:
            reasons[order.id] = Reason(
                order=order.id, code="TOO_HEAVY",
                message=f"{order.id} nije moguće izvršiti: stroj {order.machine} teži {_kg(weight)} kg, "
                        f"a najveća nosivost kamiona je {_kg(max_capacity)} kg.",
            )
            continue
        bound = _bound(paths, scenario.depot, order)
        required = drive_seconds(bound, max(t.speed_kmh for t in allowed))
        basis = "vožnje"
        if scenario.settings.limit_includes_handling:
            required += sum(scenario.handling_seconds(order.id))
            basis = "vožnje i radnji"
        if required > limit:
            reasons[order.id] = Reason(
                order=order.id, code="TOO_LONG_ALONE",
                message=f"{order.id} ne stane u dnevni limit ni najkraćim mogućim putem "
                        f"(najmanje {_minute_text(required)} min {basis}, limit je {_minute_text(limit)} min).",
            )
    return reasons
