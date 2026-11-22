"""Naredbeni redak za izračun plana i usporedbu scenarija."""

import argparse
import sys
from io import TextIOWrapper

from uprent.domain import ScenarioError, apply_overrides, load_scenario
from uprent.result import SolveResult
from uprent.service import solve


class _Parser(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        super().__init__(add_help=False, allow_abbrev=False, **kwargs)
        self._positionals.title = "Argumenti"
        self._optionals.title = "Mogućnosti"
        self.add_argument("-h", "--help", action="help", help="Prikaži upute za naredbu.")

    def format_help(self):
        return super().format_help().replace("usage:", "Uporaba:", 1)

    def format_usage(self):
        return super().format_usage().replace("usage:", "Uporaba:", 1)

    def error(self, message):
        unknown = "unrecognized arguments: "
        if message.startswith(unknown):
            detail = f"Nepoznati argumenti: {message.removeprefix(unknown)}."
        else:
            detail = "Provjerite naziv naredbe, putanju i vrijednosti argumenata."
        raise ScenarioError(f"{detail}\n{self.format_usage().rstrip()}")


def _parser():
    parser = _Parser(prog="uprent", description="Raspored prijevoza radnih strojeva.")
    commands = parser.add_subparsers(dest="command", title="Naredbe", required=True)
    plan = commands.add_parser("solve", prog="uprent solve", help="Izračunaj plan prijevoza.")
    plan.add_argument("path", metavar="PUTANJA", help="JSON datoteka sa scenarijem.")
    plan.add_argument("--json", action="store_true", help="Ispiši cjeloviti rezultat kao JSON.")
    plan.add_argument("--solver", metavar="auto|exact|ortools", help="Odaberi način izračuna.")
    plan.add_argument("--set", metavar="KLJUČ=VRIJEDNOST", action="append", default=[],
                      help="Promijeni postavku za ovaj izračun. Opcija se može ponoviti.")
    variants = commands.add_parser("compare", prog="uprent compare", help="Usporedi šest tumačenja scenarija.")
    variants.add_argument("path", metavar="PUTANJA", help="JSON datoteka sa scenarijem.")
    return parser


def _overrides(pairs):
    values = {}
    for pair in pairs:
        key, separator, value = pair.partition("=")
        if not separator or not key.strip() or not value.strip():
            raise ScenarioError(f"--set očekuje KLJUČ=VRIJEDNOST. Primljeno: {pair!r}.")
        values[key.strip()] = value.strip()
    return values


def _number(value, digits=1):
    return format(value, f",.{digits}f").translate(str.maketrans(".,", ",."))


def _print_plan(result: SolveResult):
    labels = {
        "OPTIMAL": "Dokazano optimalno", "OPTIMAL_PARTIAL": "Dokazano optimalan djelomičan plan",
        "FEASIBLE": "Najbolje pronađeno", "FEASIBLE_PARTIAL": "Najbolji pronađeni djelomičan plan",
        "NO_FULL_PLAN": "Potpuni plan nije izvediv", "NOT_FOUND": "Plan nije pronađen",
        "INVALID_PLAN": "Plan nije prošao provjeru",
    }
    actions = {"PICKUP": "Utovar", "DELIVERY": "Istovar", "RETURN": "Povratak"}
    totals = result.totals
    print(labels[result.status])
    print(f"Ukupno {_number(totals.km)} km · {totals.served}/{totals.orders} naloga"
          f" · korištenih kamiona: {totals.trucks_used}")
    for truck in result.trucks:
        if not truck.used:
            print(f"\n{truck.name} ostaje u bazi · 0,0 km · 0 naloga")
            continue
        print(f"\n{truck.name} · {_number(truck.km)} km · izvršenih naloga: {len(truck.orders)}"
              f" · vožnja {_number(truck.drive_min)} min · ukupno {_number(truck.total_min)} min")
        print("#\tLokacija\tRadnja\tNalog\tStroj\tDionica (km)\tUkupno (km)\tDolazak\tOdlazak\tTeret (kg)\tStrojeva")
        for step in truck.steps:
            print(step.seq, step.location, actions[step.action], step.order or "—", step.machine or "—",
                  _number(step.leg_km), _number(step.cum_km), step.arrive, step.depart,
                  _number(step.load_kg, 0), step.load_slots, sep="\t")
    if result.unserved:
        print("\nUpozorenja")
        for order in result.unserved:
            print(f"{order.order} [{order.reason}] {order.message}")
    for message in result.messages:
        print(message)
    if not result.validation.passed:
        for check in result.validation.checks:
            if check.severity == "hard" and not check.passed:
                print(f"{check.rule}: {check.detail}")


def _print_comparison(rows):
    print("Tumačenje\tUkupno (km)\tIzvršeno\tKorišteni kamioni\tVrijedi i za")
    for row in rows:
        print(row.label, _number(row.km), f"{row.served}/{row.orders}", row.trucks_used,
              ", ".join(row.valid_under) or "—", sep="\t")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        # Windows pipes otherwise use the active code page, including for JSON.
        for stream in (sys.stdout, sys.stderr):
            if isinstance(stream, TextIOWrapper) and not stream.isatty():
                stream.reconfigure(encoding="utf-8")
    try:
        try:
            args = _parser().parse_args(argv)
        except SystemExit as exc:
            return int(exc.code or 0)  # argparse help
        scenario = load_scenario(args.path)
        if args.command == "compare":
            from uprent.compare import compare

            _print_comparison(compare(scenario))
        else:
            scenario = apply_overrides(scenario, _overrides(args.set))
            result = solve(scenario, solver_override=args.solver)
            if args.json:
                print(result.model_dump_json())
            else:
                _print_plan(result)
    except ScenarioError as exc:
        print(f"Pogreška: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
