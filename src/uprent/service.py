"""Od provjere ulaza do provjerenog plana i razloga za neizvršene naloge."""

from time import perf_counter

from uprent.analysis import analyze
from uprent.domain import Scenario, apply_overrides
from uprent.plan import Plan
from uprent.precheck import Reason, precheck
from uprent.result import Analysis, Sensitivity, SolveResult, Totals, Unserved, Validation
from uprent.solvers.auto import choose_solver
from uprent.solvers.base import SolverOutput
from uprent.solvers.exact import StateLimitExceeded, build_context, solve_exact
from uprent.solvers.ortools_solver import solve_ortools
from uprent.validator import ValidationReport, validate


MAX_STATES = 1_000_000
EXACT_SECONDS = 8.0


def _empty_analysis(scenario: Scenario) -> Analysis:
    basis = "drive+handling" if scenario.settings.limit_includes_handling else "drive"
    return Analysis(sensitivity=Sensitivity(limit_basis=basis))


def _optimize(s: Scenario, rejected: dict[str, Reason], messages: list[str]) -> SolverOutput:
    ids = [o.id for o in s.orders if o.id not in rejected]
    method = choose_solver(s, len(s.orders))
    if rejected and not s.settings.allow_partial:
        # Jedan dokazano neizvediv nalog isključuje svaki potpuni raspored.
        messages.append("Predprovjera je dokazala da potpuni plan nije moguć. Djelomičan plan je isključen.")
        return SolverOutput(Plan(routes={}), frozenset(), "proven", method, "NO_FULL_PLAN",
                            {"precheck_only": True})
    if method == "exact":
        # Tablice uključuju i naloge koji ne stanu u trenutačni limit kako bi
        # analiza drugih postavki mogla ponovno koristiti iste rute.
        table_ids = [o.id for o in s.orders if o.id not in rejected or rejected[o.id].code != "TOO_HEAVY"]
        start = perf_counter()
        try:
            ctx = build_context(s, table_ids, max_states=MAX_STATES, deadline_s=EXACT_SECONDS)
            remaining = EXACT_SECONDS - (perf_counter() - start)
            return solve_exact(s, ids, ctx, deadline_s=remaining)
        except StateLimitExceeded:
            messages.append("Egzaktni solver prekinut: prevelik prostor stanja ili istek vremena.")
            if ids:
                messages.append("Plan je od OR-Toolsa, bez dokaza optimalnosti.")
    if rejected and not ids:
        # Predprovjera je već dokazala maksimum nula. Provjeri prazan raspored
        # egzaktno. Tablice praznog skupa ne mogu služiti analizi drugih postavki.
        output = solve_exact(s, [])
        output.info.pop("context", None)
        messages.append("Predprovjera je za svaki nalog dokazala zašto nije izvediv.")
        return output
    return solve_ortools(s, ids, s.settings.ortools_time_limit_s)


def _reasons(s: Scenario, rejected: dict[str, Reason], output: SolverOutput,
             report: ValidationReport) -> list[Unserved]:
    result = []
    maximum = output.info.get("max_served", len(report.served))
    seconds = f"{s.settings.ortools_time_limit_s:g}".replace(".", ",")
    for oid in report.unserved:
        if oid in rejected:
            item = rejected[oid]
            reason, text = item.code, item.message
        elif output.info.get("precheck_only"):
            reason = "DOES_NOT_FIT_TOGETHER"
            text = f"{oid} nije raspoređen jer potpuni plan nije moguć, a djelomičan plan je isključen."
        elif output.solver == "exact":
            reason = "DOES_NOT_FIT_TOGETHER"
            text = f"Dokazano: najviše {maximum} od {len(s.orders)} naloga stane u dnevni limit. "
            if s.settings.allow_partial:
                text += f"Nalog {oid} izostavljen je iz najboljeg rasporeda za odabrani cilj."
            else:
                text += "Djelomičan plan je isključen."
        else:
            reason = "NOT_FOUND"
            text = f"OR-Tools nije pronašao raspored za {oid} u {seconds} s. Neizvedivost nije dokazana."
        result.append(Unserved(order=oid, reason=reason, message=text))
    return result


def solve(scenario: Scenario, solver_override: str | None = None, *, detailed: bool = False,
          include_analysis: bool = True) -> SolveResult:
    start = perf_counter()
    s = apply_overrides(scenario, {"solver": solver_override} if solver_override is not None else {})
    rejected = precheck(s)
    before_solver = perf_counter()
    messages = []
    output = _optimize(s, rejected, messages)
    after_solver = perf_counter()
    if output.info.get("message"):
        messages.append(output.info["message"])
    plan = output.plan
    if plan.reported_unserved is None:
        plan = plan.model_copy(update={"reported_unserved": [o.id for o in s.orders if o.id not in output.served]})
    report = validate(s, plan)
    before_analysis = perf_counter()
    status, optimality = output.status, output.optimality
    analyzed = _empty_analysis(s)
    trucks = report.trucks
    served, km = len(report.served), report.total_km
    unserved = []
    if not report.passed:
        status, optimality = "INVALID_PLAN", "none"
        trucks, served, km = [], 0, 0.0
        messages.append("Plan krši poslovna pravila. U kartici Provjera navedene su neuspjele provjere.")
    else:
        unserved = _reasons(s, rejected, output, report)
        if status == "NO_FULL_PLAN" and "max_served" in output.info:
            messages.append(f"Dokazano: najviše {output.info['max_served']} od {len(s.orders)} naloga "
                            "stane u dnevni limit. Djelomičan plan je isključen.")
        if status in {"NOT_FOUND", "NO_FULL_PLAN"}:
            analyzed.binding.append("Za analizu raspodjele potreban je plan koji je pronašao egzaktni solver.")
        else:
            if s.orders and not served:
                if output.solver == "ortools":
                    messages.append("OR-Tools u vremenu pretrage nije našao rutu. Neizvedivost nije dokazana.")
                else:
                    messages.append("Nijedan nalog nije moguće izvršiti.")
            unused = [t.id for t in trucks if not t.used]
            if s.settings.require_all_trucks and unused:
                conclusion = ("Uz najveći broj izvršenih naloga nije moguće koristiti više kamiona."
                              if output.solver == "exact" else "OR-Tools nije pronašao raspored koji koristi sve kamione.")
                messages.append(f"Nekorišteni kamioni: {', '.join(unused)}. {conclusion}")
            ctx = output.info.get("context") if output.solver == "exact" else None
            if include_analysis:
                analyzed = analyze(s, ctx, report, elapsed_s=output.info.get("elapsed_s", after_solver - before_solver),
                                   detailed=detailed)
    end = perf_counter()
    return SolveResult(
        status=status, optimality=optimality, solver=output.solver, settings=s.settings, trucks=trucks,
        totals=Totals(km=km, served=served, orders=len(s.orders), trucks_used=sum(t.used for t in trucks)),
        unserved=unserved, validation=Validation(passed=report.passed, checks=report.checks),
        analysis=analyzed, messages=messages, timings_ms={
            "precheck": (before_solver - start) * 1000, "solver": (after_solver - before_solver) * 1000,
            "validation": (before_analysis - after_solver) * 1000, "analysis": (end - before_analysis) * 1000,
            "total": (end - start) * 1000,
        },
    )
