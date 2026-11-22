"""Neovisno odigrava predane radnje i iz njih izvodi izvještaj o planu."""

from collections import defaultdict
from decimal import Decimal
from fractions import Fraction
from functools import cache
from math import isqrt
from typing import Literal

from pydantic import BaseModel

from uprent.domain import Location, Scenario, Truck
from uprent.plan import Op, Plan


class StepView(BaseModel):
    seq: int
    location: str
    action: Literal["PICKUP", "DELIVERY", "RETURN"]
    order: str | None
    machine: str | None
    leg_km: float
    cum_km: float
    arrive: str
    depart: str
    load_kg: int
    load_slots: int
    onboard: list[str]


class TruckView(BaseModel):
    id: str
    name: str
    used: bool
    km: float
    drive_min: float
    handling_min: float
    total_min: float
    limit_min: float
    limit_basis: Literal["drive", "drive+handling"]
    slack_min: float
    peak_kg: int
    capacity_kg: int
    peak_slots: int
    slots: int
    orders: list[str]
    steps: list[StepView]


class Check(BaseModel):
    rule: str
    passed: bool
    detail: str
    severity: Literal["hard", "info"] = "hard"


class ValidationReport(BaseModel):
    passed: bool
    checks: list[Check]
    trucks: list[TruckView]
    total_km: float
    served: list[str]
    unserved: list[str]


def _distance(a: Location, b: Location) -> int:
    """Usporedi kvadrat duljine s točnom granicom polovice desetinke."""
    dx = Fraction(str(a.x)) - Fraction(str(b.x))
    dy = Fraction(str(a.y)) - Fraction(str(b.y))
    squared = 100 * (dx * dx + dy * dy)
    lower = isqrt(squared.numerator // squared.denominator)
    return lower + int(4 * squared >= (2 * lower + 1) ** 2)


def _clock(start_min: int, seconds: Fraction) -> str:
    minute = (start_min + seconds // 60) % (24 * 60)
    return f"{minute // 60:02}:{minute % 60:02}"


def _minutes(seconds: Fraction) -> float:
    return float(round(seconds / 60, 1))


def _number(value: int | float) -> str:
    return format(value, ",.1f").removesuffix(".0").translate(str.maketrans(".,", ",."))


def _comparison_values(left: Fraction, right: Fraction) -> tuple[str, str]:
    rounded = (_number(float(left)), _number(float(right)))
    if rounded[0] != rounded[1]:
        return rounded

    def precise(value: Fraction) -> str:
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
        if Fraction(decimal) == value:
            return format(decimal, ",f").translate(str.maketrans(".,", ",."))
        return f"{value.numerator}/{value.denominator}"

    return precise(left), precise(right)


class _Simulation:
    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.orders = {order.id: order for order in scenario.orders}
        self.weights = {m.id: m.weight_kg for m in scenario.machines}
        places = {p.id: p for p in scenario.locations}

        @cache
        def distance(a: str, b: str) -> int:
            return _distance(places[a], places[b])

        self.distance = distance
        hour, minute = map(int, scenario.settings.day_start.split(":"))
        self.start_min = 60 * hour + minute
        self.limit_seconds = Fraction(str(scenario.settings.day_limit_min)) * 60
        self.events: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.violations: dict[str, list[str]] = defaultdict(list)

    def drive(self, truck: Truck, route: list[Op]) -> TruckView:
        scenario = self.scenario
        depot = position = scenario.depot
        speed = Fraction(str(truck.speed_kmh))
        drive_s = handling_s = Fraction(0)
        distance = load = peak_kg = peak_slots = 0
        onboard: set[str] = set()
        delivered: list[str] = []
        steps: list[StepView] = []

        def visit(place, action, order_id=None, machine=None, service_s=0):
            nonlocal position, distance, drive_s, handling_s
            leg = self.distance(position, place)
            position = place
            distance += leg
            drive_s += Fraction(leg * 360) / speed
            arrival = drive_s + handling_s
            handling_s += service_s
            steps.append(StepView(
                seq=len(steps) + 1, location=place, action=action, order=order_id, machine=machine,
                leg_km=leg / 10, cum_km=distance / 10, arrive=_clock(self.start_min, arrival),
                depart=_clock(self.start_min, arrival + service_s), load_kg=load,
                load_slots=len(onboard), onboard=sorted(onboard),
            ))

        for action, order_id in route:
            order = self.orders.get(order_id)
            if order is None:
                self.violations["jednom"].append(f"{truck.id}: nepoznat nalog {order_id}.")
                continue
            self.events[order_id].append((action, truck.id))
            machine = order.machine
            load_s, unload_s = scenario.handling_seconds(order_id)
            if action == "PICKUP":
                if machine not in onboard:
                    onboard.add(machine)
                    load += self.weights[machine]
                peak_kg = max(peak_kg, load)
                peak_slots = max(peak_slots, len(onboard))
                visit(order.pickup, action, order_id, machine, load_s)
            else:
                if machine in onboard:
                    onboard.remove(machine)
                    load -= self.weights[machine]
                    delivered.append(order_id)
                else:
                    self.violations["redoslijed"].append(f"{truck.id}: istovar {machine} za {order_id} prije utovara u taj kamion.")
                visit(order.delivery, action, order_id, machine, unload_s)

        if steps:
            visit(depot, "RETURN")
        if onboard:
            self.violations["baza"].append(f"{truck.id}: pri povratku u bazu ostaju {', '.join(sorted(onboard))}.")
        if peak_kg > truck.capacity_kg:
            self.violations["kapacitet_kg"].append(f"{truck.id}: {_number(peak_kg)} / {_number(truck.capacity_kg)} kg.")
        if peak_slots > truck.slots:
            self.violations["mjesta"].append(f"{truck.id}: {peak_slots} / {truck.slots} mjesta.")
        total_s = drive_s + handling_s
        strict = scenario.settings.limit_includes_handling
        measured = total_s if strict else drive_s
        if measured > self.limit_seconds:
            actual, limit = _comparison_values(measured / 60, self.limit_seconds / 60)
            self.violations["vrijeme"].append(
                f"{truck.id}: {actual} min prelazi limit od {limit} min."
            )
        return TruckView(
            id=truck.id, name=truck.name or f"Kamion {truck.id}", used=bool(steps), km=distance / 10,
            drive_min=_minutes(drive_s), handling_min=_minutes(handling_s), total_min=_minutes(total_s),
            limit_min=scenario.settings.day_limit_min, limit_basis="drive+handling" if strict else "drive",
            slack_min=_minutes(self.limit_seconds - measured), peak_kg=peak_kg, capacity_kg=truck.capacity_kg,
            peak_slots=peak_slots, slots=truck.slots, orders=delivered, steps=steps,
        )


def validate(scenario: Scenario, plan: Plan) -> ValidationReport:
    sim = _Simulation(scenario)
    errors = sim.violations
    trucks = [sim.drive(truck, plan.routes.get(truck.id, [])) for truck in scenario.trucks]
    actual_km = {truck.id: truck.km for truck in trucks}
    for unknown in sorted(plan.routes.keys() - actual_km.keys()):
        errors["baza"].append(f"Nepoznat kamion {unknown}.")

    served = []
    pins = scenario.settings.pinned_orders or {}
    for order in scenario.orders:
        events = sim.events.get(order.id, [])
        if not events:
            continue
        carriers = {truck_id for action, truck_id in events}
        if len(carriers) > 1:
            errors["isti_kamion"].append(f"{order.id}: radnje su raspoređene na {', '.join(sorted(carriers))}.")
        if order.id in pins and carriers != {pins[order.id]}:
            errors["isti_kamion"].append(f"{order.id}: prikvačen je na kamion {pins[order.id]}.")
        actions = [action for action, truck_id in events]
        pickups, deliveries = actions.count("PICKUP"), actions.count("DELIVERY")
        if pickups != 1 or deliveries != 1:
            errors["jednom"].append(f"{order.id}: utovara {pickups}, istovara {deliveries}.")
        elif len(carriers) == 1 and actions == ["PICKUP", "DELIVERY"]:
            served.append(order.id)

    served_ids = set(served)
    unserved = [order.id for order in scenario.orders if order.id not in served_ids]
    if plan.reported_km is not None:
        required = {truck.id for truck in trucks if truck.used}
        for missing in sorted(required - plan.reported_km.keys()):
            errors["km_dosljedno"].append(f"{missing}: nedostaju prijavljeni kilometri.")
        for truck_id, km in plan.reported_km.items():
            if truck_id not in actual_km:
                errors["km_dosljedno"].append(f"Nepoznat kamion {truck_id}.")
            elif km != actual_km[truck_id]:
                reported, actual = _comparison_values(Fraction(str(km)), Fraction(str(actual_km[truck_id])))
                errors["km_dosljedno"].append(
                    f"{truck_id}: prijavljeno {reported} km, prijeđeno {actual} km."
                )
    if plan.reported_unserved is not None and sorted(plan.reported_unserved) != sorted(unserved):
        errors["neizvrseni_dosljedno"].append("Prijavljeni popis odstupa od simulacije. "
                                              f"Neizvršeni: {', '.join(unserved) or 'nema'}.")

    unused = [truck.id for truck in trucks if not truck.used]
    if scenario.settings.require_all_trucks and unused:
        errors["svi_kamioni"].append(f"Nekorišteni kamioni: {', '.join(unused)}.")
    checks = []

    def check(name: str, success: str, severity: Literal["hard", "info"] = "hard"):
        failures = errors.get(name, [])
        checks.append(Check(rule=name, passed=not failures, detail=" ".join(failures) or success, severity=severity))

    check("baza", f"Svi kamioni završavaju prazni u bazi {scenario.depot}.")
    check("kapacitet_kg", "; ".join(f"{t.id}: {_number(t.peak_kg)} / {_number(t.capacity_kg)} kg" for t in trucks))
    check("mjesta", "; ".join(f"{t.id}: {t.peak_slots} / {t.slots}" for t in trucks))
    check("redoslijed", "Svaki istovar slijedi odgovarajući utovar.")
    check("isti_kamion", "Isti kamion izvršava obje radnje i poštuje prikvačene naloge.")
    check("jednom", f"Izvršenih naloga s jednim utovarom i jednim istovarom: {len(served)}.")
    check("vrijeme", "; ".join(f"{t.id}: {_number(t.total_min if t.limit_basis == 'drive+handling' else t.drive_min)}"
                               f" / {_number(t.limit_min)} min" for t in trucks))
    check("km_dosljedno", "Prijavljene udaljenosti odgovaraju prijeđenima." if plan.reported_km is not None else "nije primjenjivo")
    check("neizvrseni_dosljedno", f"Popis se podudara ({len(unserved)} neizvršenih)." if plan.reported_unserved is not None else "nije primjenjivo")
    check("svi_kamioni", "Svi kamioni voze." if scenario.settings.require_all_trucks else "nije primjenjivo", "info")
    total = sum(Fraction(str(truck.km)) for truck in trucks)
    return ValidationReport(
        passed=all(c.passed for c in checks if c.severity == "hard"), checks=checks,
        trucks=trucks, total_km=float(total), served=served, unserved=unserved,
    )
