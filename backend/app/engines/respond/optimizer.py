"""Respond engine: unit dispatch optimization (OR-Tools CP-SAT).

Given active events (each with a predicted clearance p50, priority, and location)
and a fleet of `n_units` pre-positioned at the busiest corridors, choose which
events to cover to **maximize the total covered value** Sigma(priority x p50),
subject to one unit per event, each unit covering at most one event, and a
maximum dispatch distance. Falls back to a greedy assignment if CP-SAT does not
return a usable solution.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.utils.geo import haversine_km

logger = get_logger("pravah.respond.optimizer")

# Priority -> value weight.
_PRIORITY_WEIGHT = {"high": 2.0, "low": 1.0}
DEFAULT_MAX_DISPATCH_KM = 8.0
# Scale value to integers for CP-SAT (which is integer-only).
_VALUE_SCALE = 100
_SOLVER_TIME_LIMIT_S = 3.0
# Cap candidate events considered (top by value) to keep the solve fast.
_MAX_CANDIDATES = 200


@dataclass(frozen=True, slots=True)
class EventDemand:
    event_id: str
    p50: float
    priority: str          # "high" | "low"
    lat: float
    lng: float

    @property
    def value(self) -> float:
        return _PRIORITY_WEIGHT.get(self.priority.lower(), 1.0) * max(self.p50, 0.0)


@dataclass(frozen=True, slots=True)
class Unit:
    unit_id: str
    lat: float
    lng: float


@dataclass
class Assignment:
    unit_id: str
    event_id: str
    distance_km: float


@dataclass
class DispatchPlan:
    assignments: list[Assignment] = field(default_factory=list)
    covered_value: float = 0.0
    units_used: int = 0
    method: str = "cp-sat"

    @property
    def covered_event_ids(self) -> set[str]:
        return {a.event_id for a in self.assignments}


def build_units(unit_locations: list[tuple[float, float]]) -> list[Unit]:
    """Wrap (lat, lng) depots into Unit records."""
    return [Unit(f"unit-{i+1}", lat, lng) for i, (lat, lng) in enumerate(unit_locations)]


def _feasible_pairs(units: list[Unit], events: list[EventDemand], max_km: float):
    """Yield (u, e, distance) for unit/event pairs within range."""
    for u, unit in enumerate(units):
        for e, ev in enumerate(events):
            dist = haversine_km(unit.lat, unit.lng, ev.lat, ev.lng)
            if dist <= max_km:
                yield u, e, dist


def optimize(
    events: list[EventDemand],
    units: list[Unit],
    max_km: float = DEFAULT_MAX_DISPATCH_KM,
) -> DispatchPlan:
    """Assign units to events maximizing covered value (CP-SAT, greedy fallback)."""
    if not events or not units:
        return DispatchPlan(method="empty")

    events = sorted(events, key=lambda e: e.value, reverse=True)[:_MAX_CANDIDATES]
    pairs = list(_feasible_pairs(units, events, max_km))
    if not pairs:
        return DispatchPlan(method="cp-sat")

    try:
        return _solve_cp_sat(events, units, pairs)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("CP-SAT failed (%s); using greedy fallback.", exc)
        return _solve_greedy(events, units, pairs)


def _solve_cp_sat(events, units, pairs) -> DispatchPlan:
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    x = {(u, e): model.NewBoolVar(f"x_{u}_{e}") for u, e, _ in pairs}
    by_event: dict[int, list] = {}
    by_unit: dict[int, list] = {}
    for (u, e), var in x.items():
        by_event.setdefault(e, []).append(var)
        by_unit.setdefault(u, []).append(var)

    for vars_ in by_event.values():
        model.Add(sum(vars_) <= 1)   # each event covered by <= 1 unit
    for vars_ in by_unit.values():
        model.Add(sum(vars_) <= 1)   # each unit handles <= 1 event

    model.Maximize(
        sum(int(events[e].value * _VALUE_SCALE) * var for (u, e), var in x.items())
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = _SOLVER_TIME_LIMIT_S
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return _solve_greedy(events, units, pairs)

    dist_lookup = {(u, e): d for u, e, d in pairs}
    plan = DispatchPlan(method="cp-sat" if status == cp_model.OPTIMAL else "cp-sat-feasible")
    for (u, e), var in x.items():
        if solver.Value(var):
            plan.assignments.append(
                Assignment(units[u].unit_id, events[e].event_id, round(dist_lookup[(u, e)], 2))
            )
            plan.covered_value += events[e].value
    plan.units_used = len(plan.assignments)
    plan.covered_value = round(plan.covered_value, 1)
    return plan


def _solve_greedy(events, units, pairs) -> DispatchPlan:
    """Greedy: highest-value events first, assign nearest free in-range unit."""
    pairs_by_event: dict[int, list] = {}
    for u, e, d in pairs:
        pairs_by_event.setdefault(e, []).append((d, u))

    used_units: set[int] = set()
    plan = DispatchPlan(method="greedy")
    # `events` is already value-sorted desc.
    for e in range(len(events)):
        for dist, u in sorted(pairs_by_event.get(e, [])):
            if u not in used_units:
                used_units.add(u)
                plan.assignments.append(
                    Assignment(units[u].unit_id, events[e].event_id, round(dist, 2))
                )
                plan.covered_value += events[e].value
                break
    plan.units_used = len(plan.assignments)
    plan.covered_value = round(plan.covered_value, 1)
    return plan
