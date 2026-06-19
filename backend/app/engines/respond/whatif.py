"""Respond engine: what-if scenario simulation.

Models a corridor network as a graph (corridors linked when they share a zone)
and estimates the ripple of a disruption: network delay, vehicles affected, and
extra idle emissions, with rule-based mitigations and reroute LineStrings.

These are transparent analytical heuristics (criticality x duration with
graph-distance decay) — not a microsimulation.
"""
from __future__ import annotations

from typing import Any

import networkx as nx
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models import Event
from app.features.spatial import corridor_centroids, corridor_criticality

logger = get_logger("pravah.respond.whatif")

_IGNORED = frozenset({"non-corridor", "unknown", "none", ""})

# Heuristic constants.
_DELAY_MIN_PER_CRIT_HOUR = 30.0     # avg added delay (min) at criticality 1, per hour
_VEH_PER_CRIT_HOUR = 1200.0         # vehicles passing through at criticality 1, per hour
_IDLE_FRACTION = 0.25               # share of trip time spent idling in the jam
_CO2_KG_PER_VEH_HOUR = 1.6          # idling passenger-vehicle CO2
_HOP_DECAY = 0.4                    # propagation decay per graph hop
_MAX_HOPS = 2

_graph: nx.Graph | None = None


def _valid(name: str | None) -> bool:
    return bool(name) and name.strip().lower() not in _IGNORED


def corridor_graph(db: Session) -> nx.Graph:
    """Corridor graph: an edge between corridors that share a zone (cached)."""
    global _graph
    if _graph is None:
        graph = nx.Graph()
        rows = (
            db.query(Event.corridor, Event.zone)
            .filter(Event.corridor.isnot(None), Event.zone.isnot(None))
            .distinct()
            .all()
        )
        zone_to_corridors: dict[str, set[str]] = {}
        for corridor, zone in rows:
            if not _valid(corridor) or not _valid(zone):
                continue
            graph.add_node(corridor)
            zone_to_corridors.setdefault(zone, set()).add(corridor)
        for corridors in zone_to_corridors.values():
            corridors = sorted(corridors)
            for i in range(len(corridors)):
                for j in range(i + 1, len(corridors)):
                    graph.add_edge(corridors[i], corridors[j], zone=True)
        _graph = graph
        logger.info("Built corridor graph: %d nodes, %d edges", graph.number_of_nodes(), graph.number_of_edges())
    return _graph


def reset_caches() -> None:
    """Clear the corridor-graph cache (used by tests)."""
    global _graph
    _graph = None


def _mitigations(trigger: str) -> list[dict[str, str]]:
    t = trigger.lower()
    if "accident" in t:
        return [
            {"title": "Divert through alternate corridors", "detail": "Route through neighbouring zones to bypass the blockage."},
            {"title": "Dispatch ambulance and tow", "detail": "Clear casualties and stalled vehicles to reopen lanes faster."},
            {"title": "Push commuter advisory", "detail": "Notify navigation apps and signage of the incident."},
        ]
    if "water" in t or "flood" in t or "rain" in t:
        return [
            {"title": "Restrict heavy vehicles", "detail": "Keep low-clearance vehicles off the flooded stretch."},
            {"title": "Deploy dewatering crews", "detail": "Coordinate with BBMP/BWSSB to pump standing water."},
            {"title": "Activate alternate routes", "detail": "Signpost higher-ground corridors for through traffic."},
        ]
    if "clos" in t or "construction" in t or "block" in t:
        return [
            {"title": "Retime downstream signals", "detail": "Lengthen green phases on diversion corridors."},
            {"title": "Schedule works off-peak", "detail": "Shift lane occupancy to night windows where possible."},
            {"title": "Publish detour map", "detail": "Share the official diversion with the public."},
        ]
    if "vip" in t or "protest" in t or "procession" in t or "rally" in t or "event" in t:
        return [
            {"title": "Rolling lane closures", "detail": "Close and reopen lanes just ahead of the movement."},
            {"title": "Pre-position marshals", "detail": "Staff key junctions along the route for manual control."},
            {"title": "Stagger commuter advisory", "detail": "Warn of timed closures on affected corridors."},
        ]
    return [
        {"title": "Deploy traffic marshals", "detail": "Manual control at the most affected junctions."},
        {"title": "Divert through neighbours", "detail": "Shift through-traffic to adjacent corridors."},
        {"title": "Issue commuter advisory", "detail": "Broadcast expected delays and alternates."},
    ]


def simulate(db: Session, trigger: str, corridor: str, duration_hours: float) -> dict[str, Any]:
    """Estimate the network impact of a disruption on `corridor`."""
    graph = corridor_graph(db)
    centroids = corridor_centroids(db)
    corridor_criticality(corridor, db)  # ensure criticality cache is built

    duration_hours = max(0.0, float(duration_hours))
    base_crit = corridor_criticality(corridor)

    # Affected set: the trigger corridor (hop 0) + neighbours up to _MAX_HOPS.
    hops: dict[str, int] = {corridor: 0}
    if corridor in graph:
        hops.update(nx.single_source_shortest_path_length(graph, corridor, cutoff=_MAX_HOPS))

    network_delay = 0.0
    vehicles_affected = 0.0
    for node, hop in hops.items():
        decay = _HOP_DECAY**hop
        crit = base_crit if node == corridor else corridor_criticality(node)
        network_delay += crit * duration_hours * _DELAY_MIN_PER_CRIT_HOUR * decay
        vehicles_affected += crit * duration_hours * _VEH_PER_CRIT_HOUR * decay

    vehicles_affected_int = int(round(vehicles_affected))
    emissions_kg = vehicles_affected_int * _IDLE_FRACTION * duration_hours * _CO2_KG_PER_VEH_HOUR

    # Reroute LineStrings from the trigger corridor to its direct neighbours.
    features: list[dict[str, Any]] = []
    if corridor in centroids:
        src_lat, src_lng = centroids[corridor]
        neighbours = [n for n in graph.neighbors(corridor)] if corridor in graph else []
        for nb in sorted(neighbours):
            if nb not in centroids:
                continue
            dst_lat, dst_lng = centroids[nb]
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[src_lng, src_lat], [dst_lng, dst_lat]],
                    },
                    "properties": {"from": corridor, "to": nb, "type": "reroute"},
                }
            )

    return {
        "network_delay": round(network_delay, 1),
        "vehicles_affected": vehicles_affected_int,
        "emissions": round(emissions_kg, 1),
        "mitigation": _mitigations(trigger),
        "routes_geojson": {"type": "FeatureCollection", "features": features},
    }
