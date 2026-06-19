"""Read + enrichment logic backing the events / summary endpoints.

Kept separate from the route handlers so the HTTP layer stays thin. List/detail
responses are enriched with Predict-engine outputs (clearance quantiles ->
eta/range, severity + PSI, ripple, SHAP). Falls back to priority-based severity
only if the models are not loaded.
"""
from __future__ import annotations

import statistics
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Event
from app.engines.predict import (
    build_features,
    compute_severity,
    estimate_ripple,
    explain_p50,
    get_models,
)
from app.schemas.event import EventCreate, EventDetail, EventListItem
from app.schemas.predict import Prediction, Ripple, ShapItem
from app.schemas.summary import SummaryResponse

# Default + cap for list pagination.
DEFAULT_LIMIT = 50
MAX_LIMIT = 500

# Human-friendly labels for the common normalized causes; anything else falls
# back to title-cased words.
_CAUSE_LABELS: dict[str, str] = {
    "vehicle_breakdown": "Breakdown",
    "water_logging": "Waterlogging",
    "accident": "Accident",
    "construction": "Construction",
    "pot_holes": "Potholes",
    "tree_fall": "Tree Fall",
    "road_conditions": "Road Conditions",
    "congestion": "Congestion",
    "public_event": "Public Event",
    "debris": "Debris",
    "others": "Other",
}

# Corridor volume lookup (built once from the static seed; reset in tests).
_corridor_volumes: dict[str, int] | None = None
_corridor_max: int = 1


# --- Small presentation helpers ----------------------------------------------
def severity_from_priority(priority: str | None) -> str:
    """Fallback severity from raw priority (High->high, else moderate)."""
    if priority and priority.strip().lower() == "high":
        return "high"
    return "moderate"


def humanize_cause(cause: str | None) -> str:
    """Readable label for a normalized cause string."""
    key = (cause or "").strip().lower()
    if not key:
        return "Event"
    return _CAUSE_LABELS.get(key, key.replace("_", " ").title())


def humanize_type(event: Event) -> str:
    """Readable event type from the normalized/raw cause."""
    return humanize_cause(event.cause_norm or event.event_cause)


def format_minutes(minutes: float) -> str:
    """Compact human duration: 41m / 1h / 1h 15m."""
    total = max(0, int(round(minutes)))
    if total < 60:
        return f"{total}m"
    hours, rem = divmod(total, 60)
    return f"{hours}h" if rem == 0 else f"{hours}h {rem}m"


def format_range(p10: float, p90: float) -> str:
    """Compact prediction interval, e.g. (22-95m). ASCII hyphen for safe transport."""
    return f"({int(round(p10))}-{int(round(p90))}m)"


# --- Corridor volume ----------------------------------------------------------
def get_corridor_volumes(db: Session) -> dict[str, int]:
    """Event count per corridor (cached for the process; static seed)."""
    global _corridor_volumes, _corridor_max
    if _corridor_volumes is None:
        rows = (
            db.query(Event.corridor, func.count(Event.id))
            .group_by(Event.corridor)
            .all()
        )
        _corridor_volumes = {corridor: n for corridor, n in rows if corridor}
        _corridor_max = max(_corridor_volumes.values(), default=1)
    return _corridor_volumes


def corridor_ratio(db: Session, corridor: str | None) -> float:
    """Corridor's event count normalized to [0, 1] against the busiest corridor."""
    volumes = get_corridor_volumes(db)
    if not corridor:
        return 0.0
    return volumes.get(corridor, 0) / _corridor_max


def reset_caches() -> None:
    """Clear the corridor-volume cache (used by tests)."""
    global _corridor_volumes, _corridor_max
    _corridor_volumes = None
    _corridor_max = 1


# --- Feature building from a stored event ------------------------------------
def build_event_features(event: Event) -> dict[str, Any]:
    """Build the clearance feature row from an ORM event."""
    hour = event.hour_ist
    dow = event.dow
    if hour is None or dow is None:
        ts = event.start_datetime
        hour = ts.hour if (hour is None and ts is not None) else (hour or 12)
        dow = ts.weekday() if (dow is None and ts is not None) else (dow or 0)
    return build_features(
        event_cause=event.cause_norm or event.event_cause,
        veh_type=event.veh_type,
        corridor=event.corridor,
        zone=event.zone,
        event_type=event.event_type,
        requires_road_closure=event.requires_road_closure,
        hour=int(hour),
        dow=int(dow),
    )


# --- List / detail / summary --------------------------------------------------
def to_list_item(event: Event) -> EventListItem:
    """Unenriched card (used when models are unavailable)."""
    return EventListItem(
        id=event.id,
        type=humanize_type(event),
        road=event.corridor,
        near=event.junction or event.zone,
        sev=severity_from_priority(event.priority),
    )


def list_events(
    db: Session,
    *,
    status: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> list[EventListItem]:
    """Paginated event cards, newest first, enriched with predictions."""
    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)

    query = db.query(Event)
    if status:
        query = query.filter(Event.status == status)
    rows = (
        query.order_by(Event.start_datetime.desc()).offset(offset).limit(limit).all()
    )

    models = get_models()
    if not models.loaded or not rows:
        return [to_list_item(row) for row in rows]

    preds = models.predict_batch([build_event_features(row) for row in rows])
    items: list[EventListItem] = []
    for row, pred in zip(rows, preds):
        sev = compute_severity(
            pred["p50"], row.requires_road_closure, corridor_ratio(db, row.corridor)
        )
        items.append(
            EventListItem(
                id=row.id,
                type=humanize_type(row),
                road=row.corridor,
                near=row.junction or row.zone,
                sev=sev.severity,
                psi=sev.psi,
                eta=format_minutes(pred["p50"]),
                range=format_range(pred["p10"], pred["p90"]),
                units=None,  # respond engine, later part
            )
        )
    return items


def get_event(db: Session, event_id: str) -> Event | None:
    """Fetch a single full event row by id."""
    return db.get(Event, event_id)


def create_event(db: Session, payload: EventCreate) -> Event:
    """Insert a live event, derive its features, and publish a `create` to SSE.

    `id` is auto-generated when omitted; `start_datetime` defaults to now (IST).
    Temporal flags + `cause_norm` are derived with the same rules as the pipeline.
    """
    import uuid
    from datetime import datetime

    from app.config import settings
    from app.engines.predict.clearance import normalize_cause_scalar
    from app.features.temporal import derive_temporal_features
    from app.learning.feedback import on_event_create

    start = payload.start_datetime or datetime.now(settings.tz)
    temporal = derive_temporal_features(start)
    event = Event(
        id=payload.id or f"EVT-{uuid.uuid4().hex[:8].upper()}",
        event_type=payload.event_type,
        event_cause=payload.event_cause,
        priority=payload.priority,
        status="active",
        veh_type=payload.veh_type,
        corridor=payload.corridor,
        zone=payload.zone,
        junction=payload.junction,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        requires_road_closure=payload.requires_road_closure,
        start_datetime=start,
        cause_norm=normalize_cause_scalar(payload.event_cause),
        **temporal.as_dict(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    on_event_create(event)  # -> publishes {"type": "create", ...} to the SSE bus
    return event


def close_event(db: Session, event_id: str) -> Event | None:
    """Close an active event, stamp duration, and publish a `close` to SSE.

    Returns None if the event does not exist. Recording feedback + publishing the
    bus message is delegated to ``learning.feedback.on_event_close``.
    """
    from datetime import datetime

    from app.config import settings
    from app.learning.feedback import on_event_close

    event = db.get(Event, event_id)
    if event is None:
        return None

    closed = datetime.now(settings.tz)
    event.closed_datetime = closed
    event.status = "closed"
    if event.start_datetime is not None:
        # The DB round-trips timestamps as naive IST wall-clock (SQLite drops the
        # tz). Compare both as naive so we never mix aware/naive datetimes.
        start = event.start_datetime
        if start.tzinfo is not None:
            start = start.replace(tzinfo=None)
        delta = (closed.replace(tzinfo=None) - start).total_seconds() / 60.0
        event.duration_min = round(max(delta, 0.0), 2)
    db.add(event)
    db.commit()
    db.refresh(event)
    on_event_close(db, event)  # records Feedback + publishes {"type": "close", ...}
    return event


def get_event_detail(db: Session, event_id: str) -> EventDetail | None:
    """Full event row enriched with prediction, ripple, and SHAP."""
    event = db.get(Event, event_id)
    if event is None:
        return None

    detail = EventDetail.model_validate(event)
    models = get_models()
    if models.loaded:
        feats = build_event_features(event)
        pred = models.predict(feats)
        ratio = corridor_ratio(db, event.corridor)
        ripple = estimate_ripple(pred["p50"], event.requires_road_closure, ratio)
        detail.prediction = Prediction(**pred)
        detail.ripple = Ripple(affected_km=ripple.affected_km, peak_in_min=ripple.peak_in_min)
        detail.shap = [ShapItem(**item) for item in explain_p50(models, feats)]
    return detail


def build_summary(db: Session) -> SummaryResponse:
    """Compute the dashboard KPI tiles from DB aggregates."""
    active_events = (
        db.query(func.count(Event.id)).filter(Event.status == "active").scalar() or 0
    )
    # Most severe tier derivable from the DB today is High-priority active events.
    severe_count = (
        db.query(func.count(Event.id))
        .filter(Event.status == "active", func.lower(Event.priority) == "high")
        .scalar()
        or 0
    )
    durations = [
        d
        for (d,) in db.query(Event.duration_min)
        .filter(Event.duration_min.isnot(None))
        .all()
    ]
    median_clearance = round(statistics.median(durations), 2) if durations else None

    # Respond engine: free units after optimizing dispatch over active events.
    # Lazy import avoids an events<->respond import cycle.
    from app.services.respond import allocate_units

    allocation = allocate_units(db)
    units_available = allocation.get("available")

    return SummaryResponse(
        active_events=active_events,
        median_clearance_min=median_clearance,
        units_available=units_available,
        severe_count=severe_count,
    )
