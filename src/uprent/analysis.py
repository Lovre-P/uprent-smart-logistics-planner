"""Objašnjenja dodjele, granice postavki i nedominirane potpune raspodjele."""

from bisect import bisect_left
from fractions import Fraction
from time import perf_counter

from uprent.distance import drive_seconds
from uprent.domain import Scenario, apply_overrides
from uprent.result import Alternative, Analysis, CurvePoint, Sensitivity, UnusedTruck, WhyRow
from uprent.solvers.exact import Assignment, ExactContext, StateLimitExceeded, iter_full_plan_assignments, solve_exact
from uprent.validator import ValidationReport, validate


MAX_ASSIGNMENTS = 1_000_000
ANALYSIS_SECONDS = 8.0


def _num(value) -> str:
    return f"{float(value):,.4f}".rstrip("0").rstrip(".").translate(str.maketrans(".,", ",."))


def _km(value: float) -> str:
    return f"{value:,.1f}".translate(str.maketrans(".,", ",."))


def _duration(minutes: float) -> str:
    hours, mins = divmod(int(minutes + 0.5), 60)
    if not hours:
        return f"{mins} min"
    return f"{hours} h {mins:02} min" if mins else f"{hours} h"


def _drive(s: Scenario, report: ValidationReport) -> dict[str, Fraction]:
    km = {v.id: Fraction(str(v.km)) for v in report.trucks}
    return {t.id: drive_seconds(int(10 * km[t.id]), t.speed_kmh) for t in s.trucks}


def _assignment(s: Scenario, report: ValidationReport) -> Assignment:
    drive = _drive(s, report)
    by_truck = {v.id: frozenset(v.orders) for v in report.trucks}
    end = max(drive[tid] + sum(sum(s.handling_seconds(oid)) for oid in orders) for tid, orders in by_truck.items())
    measured = end if s.settings.limit_includes_handling else max(drive.values())
    return Assignment(by_truck, int(10 * Fraction(str(report.total_km))), end, measured)


def _variant(s: Scenario, ctx: ExactContext, patch: dict, notes: list[str], deadline: float) -> Assignment | None:
    changed = apply_overrides(s, patch)
    try:
        output = solve_exact(changed, ctx=ctx, deadline_s=deadline - perf_counter())
    except StateLimitExceeded:
        note = "Izračun alternativne raspodjele prekinut je zbog trajanja pretrage."
        if note not in notes:
            notes.append(note)
        return None
    report = validate(changed, output.plan)
    if not report.passed:
        notes.append("Alternativna raspodjela nije prošla provjeru plana.")
        return None
    return _assignment(changed, report)


def _used(plan: Assignment) -> int:
    return sum(bool(orders) for orders in plan.by_truck.values())


def _served(plan: Assignment) -> int:
    return sum(len(orders) for orders in plan.by_truck.values())


def _key(s: Scenario, plan: Assignment) -> tuple:
    return (-_served(plan), -_used(plan) if s.settings.require_all_trucks else 0,
            plan.end_seconds if s.settings.objective == "makespan" else plan.km_tenths, plan.km_tenths)


def _binding(s: Scenario, report: ValidationReport, *, unrestricted: bool = False) -> list[str]:
    used = [t for t in report.trucks if t.used]
    if not used:
        return ["Svi kamioni ostaju u bazi."]
    truck = min(used, key=lambda t: t.slack_min)
    if unrestricted and not s.settings.limit_includes_handling and truck.slack_min > 0:
        return [f"Limit vožnje nije aktivan: {truck.id} vozi {_duration(truck.drive_min)} od {_duration(truck.limit_min)}."]
    minutes = truck.total_min if s.settings.limit_includes_handling else truck.drive_min
    return [f"{truck.id} koristi {_num(minutes)} od {_num(truck.limit_min)} min (rezerva {_num(truck.slack_min)} min) "
            f"i nosi do {_num(truck.peak_kg)} od {_num(truck.capacity_kg)} kg."]


def _why(s: Scenario, ctx: ExactContext, current: Assignment, lazy: bool, analysis: Analysis,
         deadline: float) -> set[str]:
    carrier = {oid: tid for tid, orders in current.by_truck.items() for oid in orders}
    weights = {m.id: m.weight_kg for m in s.machines}
    comparable = {t.id for t in s.trucks}
    for order in s.orders:
        if order.id not in carrier:
            continue
        for truck in s.trucks:
            if truck.id == carrier[order.id]:
                continue
            row = WhyRow(order=order.id, truck=carrier[order.id], other_truck=truck.id)
            analysis.why.append(row)
            weight = weights[order.machine]
            if weight > truck.capacity_kg:
                row.impossible = (f"{order.machine} ({_num(weight)} kg) teži je od nosivosti "
                                  f"kamiona {truck.id} ({_num(truck.capacity_kg)} kg).")
                continue
            if lazy:
                row.lazy = True
                comparable.discard(truck.id)
                continue
            pins = {**(s.settings.pinned_orders or {}), order.id: truck.id}
            other = _variant(s, ctx, {"pinned_orders": pins}, analysis.binding, deadline)
            if other is None:
                row.lazy = True
                comparable.discard(truck.id)
                continue
            if order.id not in other.by_truck[truck.id]:
                row.impossible = f"Uz prikvačivanje na {truck.id} odabrani plan izostavlja {order.id}."
                comparable.discard(truck.id)
                continue
            row.other_truck_orders = sorted(other.by_truck[truck.id])
            row.other_km = other.km_tenths / 10
            row.delta_km = (other.km_tenths - current.km_tenths) / 10
            row.delta_objective = (float((other.end_seconds - current.end_seconds) / 60)
                                   if s.settings.objective == "makespan" else row.delta_km)
            if _served(other) != _served(current):
                comparable.discard(truck.id)
                analysis.binding.append(f"S nalogom {order.id} na {truck.id} izvršava se "
                                        f"{_served(other)}/{len(s.orders)} naloga.")
    return comparable


def _unused(s: Scenario, current: Assignment, analysis: Analysis, comparable: set[str]) -> None:
    used = [tid for tid, orders in current.by_truck.items() if orders]
    additional_km = {}
    for row in analysis.why:
        if row.delta_km is not None:
            previous = additional_km.get(row.other_truck, row.delta_km)
            additional_km[row.other_truck] = min(previous, row.delta_km)
    for truck in s.trucks:
        if truck.id in used:
            continue
        name = truck.name or f"Kamion {truck.id}"
        text = f"{name} nije korišten u odabranom rasporedu."
        extra = additional_km.get(truck.id)
        if (len(used) == 1 and len(s.trucks) == 2 and _served(current) == len(s.orders)
                and s.settings.objective == "km" and extra is not None and extra > 0
                and truck.id in comparable and not s.settings.pinned_orders):
            text = (f"{name} nije korišten: {used[0]} stigne sve sam, a svaki nalog prebačen "
                    f"na {truck.id} dodao bi najmanje {_km(extra)} km.")
        analysis.unused_trucks.append(UnusedTruck(truck=truck.id, message=text))


def _alternatives(s: Scenario, ctx: ExactContext, current: Assignment, a: Analysis, deadline: float) -> None:
    for setting in ("limit_includes_handling", "require_all_trucks"):
        value = not getattr(s.settings, setting)
        other = _variant(s, ctx, {setting: value}, a.binding, deadline)
        if other is None or (other.by_truck == current.by_truck and other.km_tenths == current.km_tenths):
            continue
        used = [(tid, orders) for tid, orders in other.by_truck.items() if orders]
        if used:
            tid, group = min(used, key=lambda item: len(item[1]))
            summary = f"{tid} vozi {', '.join(sorted(group))}."
        elif not s.settings.allow_partial and s.orders:
            summary = "Potpuni plan uz ovo tumačenje nije moguć."
        else:
            summary = "Svi kamioni ostaju u bazi."
        a.alternatives.append(Alternative(setting=setting, value=value, km=other.km_tenths / 10,
                                          served=_served(other), trucks_used=len(used), summary=summary))


def _frontier_add(distances: list[int], frontier: list[Assignment], new: Assignment) -> None:
    # Po rastućoj kilometraži na krivulji završeci strogo padaju.
    i = bisect_left(distances, new.km_tenths)
    if i and frontier[i - 1].end_seconds <= new.end_seconds:
        return
    if i < len(frontier) and distances[i] == new.km_tenths and frontier[i].end_seconds <= new.end_seconds:
        return
    j = i
    while j < len(frontier) and frontier[j].end_seconds >= new.end_seconds:
        j += 1
    distances[i:j] = [new.km_tenths]
    frontier[i:j] = [new]


def _full_assignments(s: Scenario, ctx: ExactContext, current: Assignment, a: Analysis, thresholds: bool,
                      deadline: float) -> None:
    if _served(current) < len(s.orders):
        a.binding.append("Krivulja se ne prikazuje jer potpuni plan nije izvediv uz zadane postavke.")
        return
    if not s.orders:
        return
    limit = Fraction(str(s.settings.day_limit_min)) * 60
    key, used = _key(s, current), _used(current)
    better = None
    frontier, distances = [], []
    for candidate in iter_full_plan_assignments(s, ctx, enforce_limit=not thresholds,
                                               max_states=MAX_ASSIGNMENTS, deadline_s=deadline - perf_counter()):
        if candidate.limit_seconds <= limit and (not s.settings.require_all_trucks or _used(candidate) == used):
            _frontier_add(distances, frontier, candidate)
        elif thresholds:
            candidate_key = _key(s, candidate)
            if candidate_key < key:
                entry = (candidate.limit_seconds, candidate_key)
                if better is None or entry < better:
                    better = entry
    if better is not None:
        seconds, best_key = better
        a.sensitivity.better_plan_at_min = float(seconds / 60)
        a.sensitivity.better_plan_km = best_key[-1] / 10
    a.curve = [CurvePoint(km=p.km_tenths / 10, end_min=float(p.end_seconds / 60),
                          by_truck={tid: sorted(orders) for tid, orders in p.by_truck.items()}) for p in frontier]


def _sensitivity(s: Scenario, ctx: ExactContext, current: Assignment, report: ValidationReport, a: Analysis,
                 deadline: float) -> None:
    sensitivity = a.sensitivity
    lower = current.limit_seconds / 60
    sensitivity.limit_lower_min = float(lower)
    text = f"Za sadašnji raspored treba najmanje {_num(lower)} min dnevnog limita."
    settings = s.settings
    if not _used(current):
        sensitivity.note = text + " Trajanje radnje nije primjenjivo jer kamioni ostaju u bazi."
    elif _served(current) < len(s.orders):
        sensitivity.note = text + " Za djelomičan plan prikazuje se samo donja granica limita."
    elif settings.load_min != settings.unload_min or any(o.load_min is not None or o.unload_min is not None for o in s.orders):
        sensitivity.note = text + " Granica trajanja vrijedi za jednake radnje; trajanja su različita ili nalog ima vlastitu vrijednost."
    elif not settings.limit_includes_handling:
        if settings.objective == "km":
            sensitivity.note = text + " Trajanje utovara i istovara ne mijenja plan jer u limit ulazi samo vožnja."
        else:
            sensitivity.note = text + " Trajanje radnji ne ulazi u limit vožnje, ali utječe na najraniji završetak."
    else:
        drive = _drive(s, report)
        limit = Fraction(str(settings.day_limit_min))
        maximum = min((limit - drive[tid] / 60) / (2 * len(group)) for tid, group in current.by_truck.items() if group)
        sensitivity.handling_max_min = float(maximum)
        next_min = maximum.numerator // maximum.denominator + 1
        other = _variant(s, ctx, {"load_min": next_min, "unload_min": next_min}, a.binding, deadline)
        sensitivity.note = text + f" Pri povećanju trajanja svake radnje sadašnji raspored stane u limit do {_num(maximum)} min po radnji."
        if other is not None:
            if _served(other) or settings.allow_partial:
                sensitivity.next_plan_km = other.km_tenths / 10
                sensitivity.note += f" Na {next_min} min izvršava se {_served(other)}/{len(s.orders)} naloga uz {_km(sensitivity.next_plan_km)} km."
            else:
                sensitivity.note += f" Na {next_min} min potpuni plan više nije izvediv."


def analyze(scenario: Scenario, ctx: ExactContext | None, report: ValidationReport, *,
            elapsed_s: float = 0.0, detailed: bool = False) -> Analysis:
    deadline = perf_counter() + ANALYSIS_SECONDS
    basis = "drive+handling" if scenario.settings.limit_includes_handling else "drive"
    a = Analysis(binding=_binding(scenario, report), sensitivity=Sensitivity(limit_basis=basis))
    if ctx is None:
        a.binding.append("Za analizu raspodjele i osjetljivosti potreban je egzaktni solver.")
        return a
    current = _assignment(scenario, report)
    slow = max(elapsed_s, ctx.build_seconds) > 2
    eager_details = detailed or not slow
    comparable = _why(scenario, ctx, current, len(scenario.trucks) >= 3 or slow, a, deadline)
    _unused(scenario, current, a, comparable)
    scan_complete = True
    try:
        _full_assignments(scenario, ctx, current, a, thresholds=eager_details, deadline=deadline)
    except StateLimitExceeded:
        scan_complete = False
        a.binding.append("Izračun svih raspodjela prekinut je zbog granice broja stanja ili trajanja pretrage. "
                         "Krivulja nije izračunata.")
    if eager_details:
        _alternatives(scenario, ctx, current, a, deadline)
        _sensitivity(scenario, ctx, current, report, a, deadline)
        if not scan_complete:
            a.sensitivity.note += " Zbog prekida izračuna gornja granica limita nije poznata."
        elif _served(current) == len(scenario.orders):
            threshold = a.sensitivity.better_plan_at_min
            if threshold is None:
                a.binding[:1] = _binding(scenario, report, unrestricted=True)
            else:
                a.binding.append(f"Uz limit od {_num(threshold)} min dostupan je bolji plan "
                                 f"od {_km(a.sensitivity.better_plan_km)} km.")
    else:
        a.sensitivity.note = "Druga tumačenja i osjetljivost dostupni su na zahtjev."
    return a
