"""Heurističko raspoređivanje parova utovara i istovara uz OR-Tools Routing."""

from dataclasses import dataclass
from fractions import Fraction
from math import ceil, floor

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from uprent.distance import distance_matrix, drive_seconds
from uprent.domain import Scenario
from uprent.plan import Plan
from uprent.solvers.base import SolverOutput


def limit_capacity_seconds(minutes: float) -> int:
    return floor(Fraction(str(minutes)) * 60)


@dataclass
class _Nodes:
    distances: list[list[int]]
    kg: list[int]
    slots: list[int]
    service: list[int]

    @classmethod
    def build(cls, scenario, orders):
        distances = distance_matrix(scenario)
        weights = {m.id: m.weight_kg for m in scenario.machines}
        places = [scenario.depot]
        kg, slots, service = [0], [0], [0]
        for order in orders:
            places.extend((order.pickup, order.delivery))
            weight = weights[order.machine]
            kg.extend((weight, -weight))
            slots.extend((1, -1))
            service.extend(ceil(s) for s in scenario.handling_seconds(order.id))
        return cls([[distances[a, b] for b in places] for a in places], kg, slots, service)


def _time_dimensions(routing, scenario, nodes, max_work):
    by_speed = {}
    work_indices, limit_indices = [], []
    for truck in scenario.trucks:
        if truck.speed_kmh not in by_speed:
            # Native matrices avoid Python callbacks during the local search.
            distances = {d for row in nodes.distances for d in row}
            seconds = {d: ceil(drive_seconds(d, truck.speed_kmh)) for d in distances}
            drive = [[seconds[d] for d in row] for row in nodes.distances]
            work = [[s + nodes.service[i] for s in row] for i, row in enumerate(drive)]
            work_index = routing.RegisterTransitMatrix(work)
            limit_index = work_index if scenario.settings.limit_includes_handling else routing.RegisterTransitMatrix(drive)
            by_speed[truck.speed_kmh] = work_index, limit_index
        work_index, limit_index = by_speed[truck.speed_kmh]
        work_indices.append(work_index)
        limit_indices.append(limit_index)
    limit = min(limit_capacity_seconds(scenario.settings.day_limit_min), max_work)
    routing.AddDimensionWithVehicleTransits(limit_indices, 0, limit, True, "limit_time")
    routing.AddDimensionWithVehicleTransits(work_indices, 0, max_work, True, "work_time")
    return routing.GetDimensionOrDie("work_time")


def _plan_output(scenario, routes, kilometres, message=None):
    served = frozenset(order for ops in routes.values() for action, order in ops if action == "DELIVERY")
    unserved = [o.id for o in scenario.orders if o.id not in served]
    status = "FEASIBLE_PARTIAL" if unserved else "FEASIBLE"
    if message:
        status = "NOT_FOUND"
    plan = Plan(routes=routes, reported_km=kilometres, reported_unserved=unserved)
    return SolverOutput(plan=plan, served=served, optimality="none" if message else "best_found",
                        solver="ortools", status=status, info={"message": message} if message else {})


def solve_ortools(scenario: Scenario, order_ids: list[str], time_limit_s: float) -> SolverOutput:
    selected = set(order_ids)
    orders = [order for order in scenario.orders if order.id in selected]
    routes = {t.id: [] for t in scenario.trucks}
    kilometres = {t.id: 0.0 for t in scenario.trucks}
    if not scenario.settings.allow_partial and len(orders) < len(scenario.orders):
        return _plan_output(scenario, routes, kilometres,
                            "Potpuni plan nije pronađen jer pretraga ne uključuje sve naloge.")
    if not orders:
        return _plan_output(scenario, routes, kilometres)

    nodes = _Nodes.build(scenario, orders)
    n, m = len(orders), len(scenario.trucks)
    arc_bound = 2 * n + 2 * m
    max_leg = max(max(row) for row in nodes.distances)
    max_distance = arc_bound * max_leg
    min_speed = min(t.speed_kmh for t in scenario.trucks)
    max_work = arc_bound * ceil(drive_seconds(max_leg, min_speed)) + sum(nodes.service)
    span_cost = max_distance + 1 if scenario.settings.objective == "makespan" else 0
    objective_bound = max_distance + span_cost * max_work
    truck_penalty = objective_bound + 1
    order_penalty = 2 * m * truck_penalty + objective_bound + 1
    cost_bound = objective_bound + (2 * m * truck_penalty if scenario.settings.require_all_trucks else 0)
    if scenario.settings.allow_partial:
        cost_bound += n * order_penalty
    mass_bound = sum(w for w in nodes.kg if w > 0)
    if max(max_work, cost_bound, mass_bound) >= 2**63 - 1:
        return _plan_output(scenario, routes, kilometres,
                            "Vrijednosti prelaze cjelobrojni raspon OR-Toolsa.")

    manager = pywrapcp.RoutingIndexManager(2 * n + 1, m, 0)
    routing = pywrapcp.RoutingModel(manager)
    routing.SetArcCostEvaluatorOfAllVehicles(routing.RegisterTransitMatrix(nodes.distances))
    for name, demand, capacities in (
        ("kg", nodes.kg, [min(t.capacity_kg, mass_bound) for t in scenario.trucks]),
        ("slots", nodes.slots, [min(t.slots, n) for t in scenario.trucks]),
    ):
        routing.AddDimensionWithVehicleCapacity(routing.RegisterUnaryTransitVector(demand),
                                                0, capacities, True, name)
    work = _time_dimensions(routing, scenario, nodes, max_work)
    if span_cost:
        work.SetGlobalSpanCostCoefficient(span_cost)

    # The action count also orders zero-distance operations with zero service time.
    counter = routing.RegisterUnaryTransitVector([0] + [1] * (2 * n))
    routing.AddDimension(counter, 0, 2 * n, True, "actions")
    actions = routing.GetDimensionOrDie("actions")
    pins = scenario.settings.pinned_orders or {}
    vehicles = {truck.id: i for i, truck in enumerate(scenario.trucks)}
    solver = routing.solver()
    for k, order in enumerate(orders):
        pickup, delivery = manager.NodeToIndex(2 * k + 1), manager.NodeToIndex(2 * k + 2)
        routing.AddPickupAndDelivery(pickup, delivery)
        solver.Add(routing.VehicleVar(pickup) == routing.VehicleVar(delivery))
        solver.Add(work.CumulVar(pickup) <= work.CumulVar(delivery))
        solver.Add(actions.CumulVar(pickup) + routing.ActiveVar(pickup) <= actions.CumulVar(delivery))
        if order.id in pins:
            # 9.15 Python cannot convert a list to the allowed-vehicles span.
            # The -1 vehicle keeps both nodes optional when the order cannot fit.
            values = [-1, vehicles[pins[order.id]]]
            routing.VehicleVar(pickup).SetValues(values)
            routing.VehicleVar(delivery).SetValues(values)
        if scenario.settings.allow_partial:
            routing.AddDisjunction([pickup], order_penalty)
            routing.AddDisjunction([delivery], 0)
    if scenario.settings.require_all_trucks:
        for v in range(m):
            routing.SetVehicleUsedWhenEmpty(True, v)
            actions.SetCumulVarSoftLowerBound(routing.End(v), 2, truck_penalty)

    search = pywrapcp.DefaultRoutingSearchParameters()
    search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    search.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search.time_limit.FromMilliseconds(max(1, int(time_limit_s * 1000)))
    solution = routing.SolveWithParameters(search)
    if solution is None:
        seconds = f"{time_limit_s:g}".replace(".", ",")
        return _plan_output(scenario, routes, kilometres,
                            f"Plan nije pronađen u {seconds} s.")

    for v, truck in enumerate(scenario.trucks):
        index = routing.Start(v)
        distance = 0
        while not routing.IsEnd(index):
            following = solution.Value(routing.NextVar(index))
            node = manager.IndexToNode(following)
            distance += nodes.distances[manager.IndexToNode(index)][node]
            if node:
                op = "PICKUP" if node % 2 else "DELIVERY"
                routes[truck.id].append((op, orders[(node - 1) // 2].id))
            index = following
        kilometres[truck.id] = distance / 10
    return _plan_output(scenario, routes, kilometres)
