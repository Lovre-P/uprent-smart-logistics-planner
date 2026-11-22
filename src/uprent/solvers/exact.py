"""Najkraća dopuštena ruta za svaki podskup naloga pojedinog kamiona."""

from dataclasses import dataclass
from functools import cache
from time import perf_counter

from uprent.distance import leg_tenths
from uprent.domain import Scenario, Truck
from uprent.plan import Op


class StateLimitExceeded(Exception):
    """Egzaktna pretraga dosegla je dopušteni broj stanja ili trajanje."""


@dataclass
class TableEntry:
    km_tenths: int
    ops: list[Op]


Table = dict[frozenset[str], TableEntry]
State = tuple[int, int, int]  # preuzeti, isporučeni, lokacija


@dataclass
class ExactContext:
    tables: dict[str, Table]
    states: int
    build_seconds: float = 0.0


def _check_time(deadline: float) -> None:
    if perf_counter() >= deadline:
        raise StateLimitExceeded("Egzaktni solver prekinut: isteklo je vrijeme pretrage.")


def _ops(state: State, parents: dict[State, State | None], ids: list[str]) -> list[Op]:
    reversed_ops: list[Op] = []
    while (previous := parents[state]) is not None:
        picked, delivered, _ = state
        if picked != previous[0]:
            order = (picked ^ previous[0]).bit_length() - 1
            reversed_ops.append(("PICKUP", ids[order]))
        else:
            order = (delivered ^ previous[1]).bit_length() - 1
            reversed_ops.append(("DELIVERY", ids[order]))
        state = previous
    reversed_ops.reverse()
    return reversed_ops


def truck_table(
    scenario: Scenario, truck: Truck, order_ids: list[str],
    max_states: int = 1_000_000, deadline_s: float = 8.0,
) -> tuple[Table, int]:
    deadline = perf_counter() + deadline_s
    _check_time(deadline)
    if max_states < 1:
        raise StateLimitExceeded("Egzaktni solver prekinut: dosegnuta je granica broja stanja.")

    requested = set(order_ids)
    machine_weights = {m.id: m.weight_kg for m in scenario.machines}
    orders = [o for o in scenario.orders if o.id in requested and machine_weights[o.machine] <= truck.capacity_kg]
    ids = [o.id for o in orders]
    weights = [machine_weights[o.machine] for o in orders]
    locations = {p.id: p for p in scenario.locations}
    stops = list(dict.fromkeys([scenario.depot, *(o.pickup for o in orders), *(o.delivery for o in orders)]))
    stop_index = {stop: i for i, stop in enumerate(stops)}
    pickup = [stop_index[o.pickup] for o in orders]
    delivery = [stop_index[o.delivery] for o in orders]
    distances = []
    for stop in stops:
        _check_time(deadline)
        distances.append([leg_tenths(locations[stop], locations[other]) for other in stops])

    @cache
    def possible_pickups(onboard: int) -> int:
        if onboard.bit_count() >= truck.slots:
            return 0
        load = sum(w for i, w in enumerate(weights) if onboard & (1 << i))
        return sum(1 << i for i, w in enumerate(weights) if load + w <= truck.capacity_kg)

    # Jedan sloj ima fiksan broj radnji. Do obrade idućeg sloja svi njegovi
    # prethodnici već su obrađeni, pa su trošak i prethodnik konačni.
    start: State = (0, 0, 0)
    frontier = {start: 0}
    parents: dict[State, State | None] = {start: None}
    endings: dict[int, tuple[int, State]] = {}
    while frontier:
        next_layer: dict[State, int] = {}

        def relax(target: State, cost: int, parent: State) -> None:
            old = next_layer.get(target)
            if old is None:
                if len(parents) >= max_states:
                    raise StateLimitExceeded("Egzaktni solver prekinut: dosegnuta je granica broja stanja.")
            elif old <= cost:
                return
            next_layer[target] = cost
            parents[target] = parent

        for i, (state, cost) in enumerate(frontier.items()):
            if i % 256 == 0:
                _check_time(deadline)
            picked, delivered, position = state
            onboard = picked ^ delivered
            distances_from_here = distances[position]
            if not onboard:
                with_return = cost + distances_from_here[0]
                if delivered not in endings or with_return < endings[delivered][0]:
                    endings[delivered] = (with_return, state)

            pending = possible_pickups(onboard) & ~picked
            while pending:
                bit = pending & -pending
                stop = pickup[bit.bit_length() - 1]
                relax((picked | bit, delivered, stop), cost + distances_from_here[stop], state)
                pending ^= bit
            while onboard:
                bit = onboard & -onboard
                stop = delivery[bit.bit_length() - 1]
                relax((picked, delivered | bit, stop), cost + distances_from_here[stop], state)
                onboard ^= bit
        frontier = next_layer

    table: Table = {}
    for mask, (cost, state) in endings.items():
        _check_time(deadline)
        subset = frozenset(oid for i, oid in enumerate(ids) if mask & (1 << i))
        table[subset] = TableEntry(cost, _ops(state, parents, ids))
    _check_time(deadline)
    return table, len(parents)


def build_context(
    scenario: Scenario, order_ids: list[str], max_states: int = 1_000_000, deadline_s: float = 8.0,
) -> ExactContext:
    start = perf_counter()
    deadline = start + deadline_s
    by_type: dict[tuple[int, int], Table] = {}
    tables = {}
    states = 0
    for truck in scenario.trucks:
        key = (truck.capacity_kg, truck.slots)
        if key not in by_type:
            table, count = truck_table(scenario, truck, order_ids, max_states - states, deadline - perf_counter())
            by_type[key] = table
            states += count
        tables[truck.id] = by_type[key]
    _check_time(deadline)
    return ExactContext(tables, states, perf_counter() - start)
