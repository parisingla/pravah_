"""Feedback capture — record realized clearance vs. predicted p50 on close.

When an event closes we persist a `Feedback` row (predicted p50 vs. actual
duration) for the online-learning loop, and publish a `close` event on the bus
so SSE subscribers see it live. `on_event_create` publishes the matching `create`.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.core.event_bus import get_event_bus
from app.core.logging import get_logger
from app.db.models import Event, Feedback

logger = get_logger("pravah.learning.feedback")


def _predicted_p50(event: Event) -> float | None:
    """Predicted clearance p50 for the event, if the clearance model is loaded."""
    from app.engines.predict import get_models
    from app.services.events import build_event_features

    models = get_models()
    if not models.loaded:
        return None
    return models.predict(build_event_features(event))["p50"]


def record_feedback(db: Session, event: Event) -> Feedback:
    """Write a Feedback row capturing predicted vs. realized clearance time."""
    feedback = Feedback(
        event_id=event.id,
        predicted_p50=_predicted_p50(event),
        actual_duration_min=event.duration_min,
        closed_at=event.closed_datetime or datetime.now(settings.tz),
        model_version="clearance",
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def _event_payload(event: Event) -> dict:
    return {
        "id": event.id,
        "corridor": event.corridor,
        "cause": event.cause_norm,
        "status": event.status,
    }


def on_event_create(event: Event) -> None:
    """Publish a `create` event to SSE subscribers."""
    get_event_bus().publish({"type": "create", "event": _event_payload(event)})


def on_event_close(db: Session, event: Event) -> Feedback:
    """Record feedback for a closing event and publish a `close` event."""
    feedback = record_feedback(db, event)
    payload = _event_payload(event)
    payload["predicted_p50"] = feedback.predicted_p50
    payload["actual_duration_min"] = feedback.actual_duration_min
    get_event_bus().publish({"type": "close", "event": payload})
    logger.info("Recorded feedback for closed event %s", event.id)
    return feedback
