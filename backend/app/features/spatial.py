"""Spatial features for the Foresee / Respond engines.

Corridor centroids (mean coordinate per corridor) and a 0-1 criticality score
derived from historical event volume. Both are cached process-wide (the seed is
static) and computed straight from the events table.
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Event

# Corridor names that are not real, dispatchable locations.
_IGNORED = frozenset({"non-corridor", "unknown", "none", ""})

_centroids: dict[str, tuple[float, float]] | None = None
_criticality: dict[str, float] | None = None


def _valid_corridor(name: str | None) -> bool:
    return bool(name) and name.strip().lower() not in _IGNORED


def corridor_centroids(session: Session) -> dict[str, tuple[float, float]]:
    """Mean (lat, lng) per corridor, from rows with usable coordinates (cached)."""
    global _centroids
    if _centroids is None:
        rows = (
            session.query(
                Event.corridor,
                func.avg(Event.latitude),
                func.avg(Event.longitude),
            )
            .filter(
                Event.latitude.isnot(None),
                Event.longitude.isnot(None),
                Event.latitude != 0,
                Event.longitude != 0,
            )
            .group_by(Event.corridor)
            .all()
        )
        _centroids = {
            corridor: (float(lat), float(lng))
            for corridor, lat, lng in rows
            if _valid_corridor(corridor) and lat is not None and lng is not None
        }
    return _centroids


def criticality_map(session: Session) -> dict[str, float]:
    """Per-corridor criticality in [0, 1] = volume / max(volume) (cached)."""
    global _criticality
    if _criticality is None:
        rows = (
            session.query(Event.corridor, func.count(Event.id))
            .group_by(Event.corridor)
            .all()
        )
        volumes = {c: int(n) for c, n in rows if _valid_corridor(c)}
        top = max(volumes.values(), default=1)
        _criticality = {c: n / top for c, n in volumes.items()}
    return _criticality


def corridor_criticality(corridor: str | None, session: Session | None = None) -> float:
    """Criticality (0-1) for a corridor from historical volume.

    Requires the map to have been built once (pass `session` on first call, e.g.
    at startup). Returns 0.0 for unknown corridors.
    """
    global _criticality
    if _criticality is None:
        if session is None:
            raise RuntimeError("corridor_criticality: provide a session to build the cache first.")
        criticality_map(session)
    assert _criticality is not None
    if not corridor:
        return 0.0
    return _criticality.get(corridor, 0.0)


def reset_caches() -> None:
    """Clear spatial caches (used by tests)."""
    global _centroids, _criticality
    _centroids = None
    _criticality = None
