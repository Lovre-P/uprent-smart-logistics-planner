"""Najkraća dopuštena ruta za svaki podskup naloga pojedinog kamiona."""

from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction
from functools import cache
from time import perf_counter

from uprent.distance import drive_seconds, leg_tenths
from uprent.domain import Scenario, Truck
from uprent.plan import Op, Plan
from uprent.solvers.base import SolverOutput


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


@dataclass
class Assignment:
    by_truck: dict[str, frozenset[str]]
    km_tenths: int
    end_seconds: Fraction
    limit_seconds: Fraction = Fraction(0)


@dataclass(frozen=True, slots=True)
class _Choice:
    subset: frozenset[str]
    entry: TableEntry
    work: Fraction
    measured: Fraction


def feasible_entry(scenario: Scenario, truck: Truck, subset: frozenset[str], entry: TableEntry) -> bool:
    pins = scenario.settings.pinned_orders or {}
    if any(pins.get(oid, truck.id) != truck.id for oid in subset):
        return False
    required = drive_seconds(entry.km_tenths, truck.speed_kmh)
    if scenario.settings.limit_includes_handling:
        required += sum(sum(scenario.handling_seconds(oid)) for oid in subset)
    return required <= Fraction(str(scenario.settings.day_limit_min)) * 60


def _choices(
    scenario: Scenario, ctx: ExactContext, ids: list[str], *, enforce_limit: bool, deadline: float,
) -> list[dict[int, _Choice]]:
    bits = {oid: 1 << i for i, oid in enumerate(ids)}
    service = {oid: sum(scenario.handling_seconds(oid)) for oid in ids}
    limit = Fraction(str(scenario.settings.day_limit_min)) * 60
    pins = scenario.settings.pinned_orders or {}
    handling_by_subset = {}
    result = []
    for truck in scenario.trucks:
        allowed = {oid for oid in ids if pins.get(oid, truck.id) == truck.id}
        per_truck = {}
        seconds_per_tenth = drive_seconds(1, truck.speed_kmh)
        for index, (subset, entry) in enumerate(ctx.tables[truck.id].items()):
            if index % 256 == 0:
                _check_time(deadline)
            if not subset.issubset(allowed):
                continue
            if subset not in handling_by_subset:
                handling_by_subset[subset] = sum(service[oid] for oid in subset)
            drive = entry.km_tenths * seconds_per_tenth
            work = drive + handling_by_subset[subset]
            measured = work if scenario.settings.limit_includes_handling else drive
            if not enforce_limit or measured <= limit:
                mask = sum(bits[oid] for oid in subset)
                per_truck[mask] = _Choice(subset, entry, work, measured)
        result.append(per_truck)
    return result


def _available(options: dict[int, _Choice]) -> int:
    mask = 0
    for subset in options:
        mask |= subset
    return mask


def _subsets(options: dict[int, _Choice], remaining: int) -> Iterator[tuple[int, _Choice]]:
    if len(options) < (1 << remaining.bit_count()):
        for mask, choice in options.items():
            if mask & remaining == mask:
                yield mask, choice
        return
    mask = remaining
    while True:
        if mask in options:
            yield mask, options[mask]
        if mask == 0:
            return
        mask = (mask - 1) & remaining


def _partition(
    choices: list[dict[int, _Choice]], all_orders: int, prefer_used: bool, deadline: float,
    *, minimize_end: bool = False,
) -> tuple[list[_Choice], tuple[int, int | Fraction]]:
    # Za svaku uniju naloga čuvamo najbolji ključ i podskup uzet na zadnjem kamionu.
    scores: dict[int, tuple[int, int | Fraction]] = {0: (0, 0)}
    parents: list[dict[int, int]] = []
    for vehicle, options in enumerate(choices):
        _check_time(deadline)
        available = _available(options)
        next_scores = {}
        selected = {}

        def record(covered, previous_score, subset, choice):
            used, value = previous_score
            contribution = max(value, choice.work) if minimize_end else value + choice.entry.km_tenths
            candidate = (used - int(prefer_used and bool(subset)), contribution)
            union = covered | subset
            if union not in next_scores or candidate < next_scores[union]:
                next_scores[union] = candidate
                selected[union] = subset

        # Na zadnjem kamionu puni plan zahtijeva upravo komplement.
        # Kad postoji, nijedan djelomičan plan ne može ga nadmašiti.
        if vehicle == len(choices) - 1:
            for covered, score in scores.items():
                complement = all_orders ^ covered
                if complement in options:
                    record(covered, score, complement, options[complement])
        if not next_scores:
            for index, (covered, score) in enumerate(scores.items()):
                if index % 64 == 0:
                    _check_time(deadline)
                for subset, choice in _subsets(options, available & ~covered):
                    record(covered, score, subset, choice)
        scores = next_scores
        parents.append(selected)

    covered = min(scores, key=lambda mask: (-mask.bit_count(), scores[mask]))
    best_score = scores[covered]
    selected_choices = []
    for options, selected in reversed(list(zip(choices, parents))):
        subset = selected[covered]
        selected_choices.append(options[subset])
        covered ^= subset
    selected_choices.reverse()
    _check_time(deadline)
    return selected_choices, best_score


def solve_exact(
    scenario: Scenario, order_ids: list[str] | None = None, ctx: ExactContext | None = None,
    *, max_states: int = 1_000_000, deadline_s: float = 8.0,
) -> SolverOutput:
    start = perf_counter()
    deadline = start + deadline_s
    ids = [o.id for o in scenario.orders] if order_ids is None else order_ids
    if ctx is None:
        ctx = build_context(scenario, ids, max_states=max_states, deadline_s=deadline_s)
    combine_start = perf_counter()
    choices = _choices(scenario, ctx, ids, enforce_limit=True, deadline=deadline)
    all_mask = (1 << len(ids)) - 1
    all_required = scenario.settings.require_all_trucks
    selected, _ = _partition(choices, all_mask, all_required, deadline)
    max_served = sum(len(choice.subset) for choice in selected)
    incomplete = max_served < len(scenario.orders)
    if incomplete and not scenario.settings.allow_partial:
        status = "NO_FULL_PLAN"
        selected = [options[0] for options in choices]
    else:
        status = "OPTIMAL_PARTIAL" if incomplete else "OPTIMAL"
        if scenario.settings.objective == "makespan":
            # Drugi prolaz bira M* uz istu maksimalnu kardinalnost i prioritet
            # broja kamiona. Zadržavanjem svih ruta do M* treći prolaz unosi
            # kilometražu kao posljednji kriterij čak i kad se trajanja izjednače.
            _, (_, best_end) = _partition(choices, all_mask, all_required, deadline, minimize_end=True)
            within_end = [{mask: c for mask, c in options.items() if c.work <= best_end} for options in choices]
            selected, _ = _partition(within_end, all_mask, all_required, deadline)
    served = frozenset().union(*(choice.subset for choice in selected))
    routes = {t.id: choice.entry.ops for t, choice in zip(scenario.trucks, selected)}
    reported = {t.id: choice.entry.km_tenths / 10 for t, choice in zip(scenario.trucks, selected)}
    plan = Plan(routes=routes, reported_km=reported, reported_unserved=[o.id for o in scenario.orders if o.id not in served])
    _check_time(deadline)
    return SolverOutput(plan=plan, served=served, optimality="proven", solver="exact", status=status, info={
        "context": ctx, "states": ctx.states, "max_served": max_served,
        "elapsed_s": ctx.build_seconds + perf_counter() - combine_start,
    })


def iter_full_plan_assignments(
    scenario: Scenario, ctx: ExactContext, *, enforce_limit: bool = True,
    max_states: int = 1_000_000, deadline_s: float = 8.0,
) -> Iterator[Assignment]:
    """Potpune raspodjele za analizu. Za gornju granicu limita uključuju se i dulje rute."""
    deadline = perf_counter() + deadline_s
    ids = [o.id for o in scenario.orders]
    options = _choices(scenario, ctx, ids, enforce_limit=enforce_limit, deadline=deadline)
    available = [_available(per_truck) for per_truck in options]
    suffix = [0] * (len(options) + 1)
    for i in range(len(options) - 1, -1, -1):
        suffix[i] = suffix[i + 1] | available[i]
    empty = {t.id: frozenset() for t in scenario.trucks}

    def candidates(i, remaining):
        if i == len(options) - 1:
            choice = options[i].get(remaining)
            if choice is not None:
                yield remaining, choice
            return
        yield from _subsets(options[i], remaining & available[i])

    full = (1 << len(ids)) - 1
    if full & ~suffix[0]:
        return
    # Vlastiti stog obilazi jednu granu odjednom. Prazne kamione na kraju
    # raspodjele upisujemo odjednom, pa dubina Pythonovih poziva ne ovisi o floti.
    stack = [(0, full, 0, Fraction(0), Fraction(0), {}, candidates(0, full))]
    visited = 0
    while stack:
        i, remaining, km, end, measured, selected, choices = stack[-1]
        item = next(choices, None)
        if item is None:
            stack.pop()
            continue
        visited += 1
        if visited > max_states:
            raise StateLimitExceeded("Izračun raspodjela prekinut: dosegnuta je granica broja stanja.")
        if visited % 64 == 1:
            _check_time(deadline)
        mask, choice = item
        left = remaining ^ mask
        if left & ~suffix[i + 1]:
            continue
        allocation = {**selected, scenario.trucks[i].id: choice.subset} if mask else selected
        new_km = km + choice.entry.km_tenths
        new_end, new_measured = max(end, choice.work), max(measured, choice.measured)
        if left == 0:
            yield Assignment(empty | allocation, new_km, new_end, new_measured)
        else:
            stack.append((i + 1, left, new_km, new_end, new_measured, allocation, candidates(i + 1, left)))
    _check_time(deadline)


def full_plan_assignments(scenario: Scenario, ctx: ExactContext) -> list[Assignment]:
    return list(iter_full_plan_assignments(scenario, ctx))
