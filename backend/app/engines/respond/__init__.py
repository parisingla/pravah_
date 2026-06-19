"""Respond engine — dispatch optimization + what-if scenario simulation.

Public surface:
- ``optimize`` / ``EventDemand`` / ``Unit`` / ``build_units`` — CP-SAT unit dispatch.
- ``simulate`` — corridor-graph what-if impact estimate.
"""
from app.engines.respond.optimizer import (
    Assignment,
    DispatchPlan,
    EventDemand,
    Unit,
    build_units,
    optimize,
)
from app.engines.respond.whatif import corridor_graph, simulate

__all__ = [
    "EventDemand",
    "Unit",
    "Assignment",
    "DispatchPlan",
    "build_units",
    "optimize",
    "simulate",
    "corridor_graph",
]
