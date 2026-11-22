"""Radnje koje je odabrao solver, bez izvedenih podataka o ruti."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


Op = tuple[Literal["PICKUP", "DELIVERY"], str]


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    routes: dict[str, list[Op]]
    reported_km: dict[str, float] | None = None
    reported_unserved: list[str] | None = None
