"""Service logic for the Foresee endpoints (predictions, hotspots, alerts)."""
from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Event
from app.engines.foresee import detect_alerts, get_model
from app.engines.foresee.hotspot import HORIZONS
from app.schemas.foresee import Alert, CorridorPrediction

_IGNORED = frozenset({"non-corridor", "unknown", "none", ""})

# Caches (static seed).
_localities: dict[str, str] | None = None
_hotspot_cache: dict[str, dict[str, Any]] = {}

# Max corridors returned by /predictions/corridors.
_TOP_CORRIDORS = 10


def _corridor_localities(db: Session) -> dict[str, str]:
    """Most frequent junction (fallback zone) per corridor, for a 'from' label."""
    global _localities
    if _localities is None:
        rows = (
            db.query(Event.corridor, Event.junction, func.count(Event.id))
            .filter(Event.junction.isnot(None))
            .group_by(Event.corridor, Event.junction)
            .all()
        )
        best: dict[str, tuple[int, str]] = {}
        for corridor, junction, n in rows:
            if not corridor or not junction:
                continue
            if junction.strip().lower() in _IGNORED:
                continue
            if corridor not in best or n > best[corridor][0]:
                best[corridor] = (n, junction)
        _localities = {c: j for c, (_, j) in best.items()}
    return _localities


def corridor_predictions(db: Session, horizon: str) -> list[CorridorPrediction]:
    """Top corridors by forecast incidence probability for the horizon."""
    localities = _corridor_localities(db)
    rows = get_model().corridor_probabilities(horizon)
    out: list[CorridorPrediction] = []
    for row in rows[:_TOP_CORRIDORS]:
        corridor = row["corridor"]
        out.append(
            CorridorPrediction(
                route=corridor,
                **{"from": localities.get(corridor, corridor)},
                prob=row["prob"],
            )
        )
    return out


def hotspots(db: Session, horizon: str) -> dict[str, Any]:
    """GeoJSON hotspot heat points (uses the precomputed cache when present)."""
    if horizon in _hotspot_cache:
        return _hotspot_cache[horizon]
    return get_model().hotspots_geojson(horizon)


def precompute_hotspots() -> None:
    """Warm the hotspot cache for every horizon (called hourly by the scheduler)."""
    model = get_model()
    if not model.loaded:
        return
    for horizon in HORIZONS:
        _hotspot_cache[horizon] = model.hotspots_geojson(horizon)


def reset_caches() -> None:
    """Clear foresee service caches (used by tests / scheduler reloads)."""
    global _localities
    _localities = None
    _hotspot_cache.clear()


def alerts(db: Session) -> list[Alert]:
    """Current anomaly alerts."""
    return [Alert(**a) for a in detect_alerts(db)]
