from fractions import Fraction

from uprent.distance import distance_matrix, drive_seconds, leg_tenths
from uprent.domain import Location


def test_task_legs(scenario):
    matrix = distance_matrix(scenario)
    assert [matrix[a, b] for a, b in [("L0", "L9"), ("L9", "L4"), ("L4", "L0")]] == [94, 170, 108]
    assert len(matrix) == len(scenario.locations) ** 2
    assert all(value == matrix[b, a] for (a, b), value in matrix.items())


def test_half_up():
    assert leg_tenths(Location(id="a", x=0, y=0), Location(id="b", x=0.05, y=0)) == 1


def test_identical_coordinates_zero():
    assert leg_tenths(Location(id="a", x=-3, y=2), Location(id="b", x=-3, y=2)) == 0


def test_drive_seconds():
    assert drive_seconds(94, 60) == 564
    assert drive_seconds(1822, 60) == 10932
    assert drive_seconds(1, 62.5) == Fraction(144, 25)
