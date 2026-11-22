"""Udaljenosti u desetinkama kilometra i točno vrijeme vožnje."""

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

from uprent.domain import Location, Scenario


def leg_tenths(a: Location, b: Location) -> int:
    dx = Decimal(str(a.x)) - Decimal(str(b.x))
    dy = Decimal(str(a.y)) - Decimal(str(b.y))
    tenths = (dx * dx + dy * dy).sqrt() * 10
    return int(tenths.to_integral_value(rounding=ROUND_HALF_UP))


def drive_seconds(tenths: int, speed_kmh: float) -> Fraction:
    return Fraction(tenths * 360) / Fraction(str(speed_kmh))


def distance_matrix(scenario: Scenario) -> dict[tuple[str, str], int]:
    matrix = {}
    for index, a in enumerate(scenario.locations):
        matrix[a.id, a.id] = 0
        for b in scenario.locations[index + 1:]:
            matrix[a.id, b.id] = matrix[b.id, a.id] = leg_tenths(a, b)
    return matrix
