"""Ulazni podaci planera i provjera veza među njima."""

import json
from fractions import Fraction
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


class ScenarioError(ValueError):
    """Pogreška ulaznih podataka koja se može prikazati korisniku."""


def input_error(errors: list) -> ScenarioError:
    messages = {
        "missing": "nedostaje obavezno polje",
        "extra_forbidden": "nepoznato polje",
        "greater_than": "vrijednost mora biti veća od nule",
        "greater_than_equal": "vrijednost je manja od dopuštenog minimuma",
        "less_than_equal": "vrijednost prelazi dopušteni maksimum",
        "too_short": "popis mora imati barem jednu stavku",
        "finite_number": "vrijednost mora biti konačan broj",
        "string_too_short": "tekst mora sadržavati barem jedan znak",
        "string_pattern_mismatch": "unesite vrijeme u obliku HH:MM (00:00–23:59)",
        "literal_error": "nepoznata vrijednost postavke",
    }
    descriptions = []
    for error in errors:
        field = ".".join(str(part) for part in error["loc"])
        underlying = error.get("ctx", {}).get("error")
        message = str(underlying) if underlying is not None else messages.get(
            error["type"], "neispravna vrijednost"
        )
        descriptions.append(f"{field}: {message}" if field else message)
    return ScenarioError("\n".join(descriptions))


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Location(InputModel):
    id: str = Field(min_length=1)
    x: float
    y: float
    name: str | None = None


class Machine(InputModel):
    id: str = Field(min_length=1)
    weight_kg: int = Field(gt=0)


class Truck(InputModel):
    id: str = Field(min_length=1)
    name: str | None = None
    capacity_kg: int = Field(gt=0)
    slots: int = Field(ge=1)
    speed_kmh: float = Field(default=60, gt=0)


class Order(InputModel):
    id: str = Field(min_length=1)
    machine: str
    pickup: str
    delivery: str
    load_min: float | None = Field(default=None, ge=0)
    unload_min: float | None = Field(default=None, ge=0)


class Settings(InputModel):
    day_limit_min: float = Field(default=540, gt=0)
    limit_includes_handling: bool = False
    load_min: float = Field(default=20, ge=0)
    unload_min: float = Field(default=20, ge=0)
    require_all_trucks: bool = False
    allow_partial: bool = True
    objective: Literal["km", "makespan"] = "km"
    solver: Literal["auto", "exact", "ortools"] = "auto"
    ortools_time_limit_s: float = Field(default=3, ge=1, le=30)
    compare_with_ortools: bool = True
    day_start: str = Field(default="07:00", pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
    exact_max_orders: int = Field(default=12, ge=1)
    exact_max_trucks: int = Field(default=3, ge=1)
    pinned_orders: dict[str, str] | None = None

    @field_validator("*", mode="before")
    @classmethod
    def parse_structured_value(cls, value):
        if isinstance(value, str) and value.lstrip().startswith(("{", "[")):
            try:
                return json.loads(value)
            except json.JSONDecodeError as exc:
                raise ScenarioError("neispravan JSON") from exc
        return value


class Scenario(InputModel):
    name: str
    depot: str
    locations: list[Location] = Field(min_length=1)
    machines: list[Machine]
    trucks: list[Truck] = Field(min_length=1)
    orders: list[Order]
    settings: Settings = Field(default_factory=Settings)

    @classmethod
    def model_validate(cls, obj, **kwargs) -> Self:
        try:
            return super().model_validate(obj, **kwargs)
        except ValidationError as exc:
            raise input_error(exc.errors(include_url=False, include_input=False)) from exc

    @model_validator(mode="after")
    def check_references(self) -> Self:
        for field in ("locations", "machines", "trucks", "orders"):
            ids = set()
            for item in getattr(self, field):
                if item.id in ids:
                    raise ScenarioError(f"{field}.id: ponovljen ID {item.id}.")
                ids.add(item.id)

        locations = {location.id for location in self.locations}
        if self.depot not in locations:
            raise ScenarioError(f"depot: nepoznata lokacija baze {self.depot}.")
        machines = {machine.id: machine for machine in self.machines}
        trucks = {truck.id: truck for truck in self.trucks}
        orders = {order.id: order for order in self.orders}
        assigned = set()
        for order in self.orders:
            for field in ("pickup", "delivery"):
                location = getattr(order, field)
                if location not in locations:
                    raise ScenarioError(f"orders.{order.id}.{field}: nepoznata lokacija {location}.")
            if order.pickup == order.delivery:
                raise ScenarioError(f"orders.{order.id}.delivery: isto mjesto utovara i istovara.")
            if order.machine not in machines:
                raise ScenarioError(f"orders.{order.id}.machine: nepoznat stroj {order.machine}.")
            if order.machine in assigned:
                raise ScenarioError(f"orders.{order.id}.machine: stroj {order.machine} pojavljuje se u dva naloga.")
            assigned.add(order.machine)

        for order_id, truck_id in (self.settings.pinned_orders or {}).items():
            field = f"settings.pinned_orders.{order_id}"
            if order_id not in orders:
                raise ScenarioError(f"{field}: nepoznat nalog {order_id}.")
            if truck_id not in trucks:
                raise ScenarioError(f"{field}: nepoznat kamion {truck_id}.")
            capacity = trucks[truck_id].capacity_kg
            if machines[orders[order_id].machine].weight_kg > capacity:
                formatted = f"{capacity:,}".replace(",", ".")
                raise ScenarioError(f"{field}: stroj je teži od nosivosti kamiona {truck_id} ({formatted} kg).")
        return self

    def handling_seconds(self, order_id: str) -> tuple[int | Fraction, int | Fraction]:
        order = next((item for item in self.orders if item.id == order_id), None)
        if order is None:
            raise ScenarioError(f"orders.id: nepoznat nalog {order_id}.")
        load = self.settings.load_min if order.load_min is None else order.load_min
        unload = self.settings.unload_min if order.unload_min is None else order.unload_min
        return _seconds(load), _seconds(unload)


def _seconds(minutes: float) -> int | Fraction:
    seconds = Fraction(str(minutes)) * 60
    return seconds.numerator if seconds.denominator == 1 else seconds


def load_scenario(path: str | Path) -> Scenario:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScenarioError(f"Datoteka {path}: scenarij se ne može pročitati kao JSON.") from exc
    return Scenario.model_validate(data)


def apply_overrides(scenario: Scenario, overrides: dict[str, object]) -> Scenario:
    data = scenario.model_dump()
    data["settings"].update(overrides)
    return Scenario.model_validate(data)
