"""Service logic for the Respond engine (/simulate + fleet allocation)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Event
from app.engines.respond import EventDemand, build_units, optimize, simulate as _simulate
from app.features.spatial import corridor_centroids, criticality_map
from app.schemas.respond import SimulateRequest, SimulateResponse


def simulate(db: Session, req: SimulateRequest) -> SimulateResponse:
    """Run a what-if disruption scenario."""
    result = _simulate(db, req.trigger, req.corridor, req.duration_hours)
    return SimulateResponse(**result)


def _unit_locations(db: Session, n_units: int) -> list[tuple[float, float]]:
    """Pre-position units at the busiest corridor centroids (cycled to n_units)."""
    centroids = corridor_centroids(db)
    crit = criticality_map(db)
    ranked = [c for c in sorted(crit, key=lambda x: crit[x], reverse=True) if c in centroids]
    if not ranked:
        return []
    return [centroids[ranked[i % len(ranked)]] for i in range(n_units)]


def allocate_units(db: Session) -> dict[str, int]:
    """Optimize dispatch over active events; return fleet/deployed/available.

    Returns an empty dict if the clearance model is not loaded (no p50 to value).
    """
    from app.engines.predict import get_models
    from app.services.events import build_event_features

    models = get_models()
    if not models.loaded:
        return {}

    rows = (
        db.query(Event)
        .filter(
            Event.status == "active",
            Event.latitude.isnot(None),
            Event.longitude.isnot(None),
            Event.latitude != 0,
        )
        .all()
    )
    if not rows:
        return {"fleet": settings.RESPOND_FLEET_SIZE, "deployed": 0, "available": settings.RESPOND_FLEET_SIZE}

    preds = models.predict_batch([build_event_features(r) for r in rows])
    demands = [
        EventDemand(
            event_id=r.id,
            p50=p["p50"],
            priority="high" if (r.priority or "").strip().lower() == "high" else "low",
            lat=float(r.latitude),
            lng=float(r.longitude),
        )
        for r, p in zip(rows, preds)
    ]

    fleet = settings.RESPOND_FLEET_SIZE
    units = build_units(_unit_locations(db, fleet))
    plan = optimize(demands, units)
    return {"fleet": fleet, "deployed": plan.units_used, "available": fleet - plan.units_used}
