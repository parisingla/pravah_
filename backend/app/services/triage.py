"""Service logic for the /triage endpoint.

Orchestrates the triage engine: classify -> resolve location -> compose impact ->
recommend actions.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Event
from app.engines.triage import get_actions, get_model, locate
from app.schemas.triage import TriageResponse
from app.services.events import humanize_cause

# Location tokens that must never be offered as candidates.
_IGNORED_LOCATIONS = frozenset({"unknown", "non-corridor", "none", ""})

# Cached unique location names (static seed).
_location_candidates: list[str] | None = None


def get_location_candidates(db: Session) -> list[str]:
    """Unique corridor/junction/zone names from the events table (cached)."""
    global _location_candidates
    if _location_candidates is None:
        names: set[str] = set()
        for column in (Event.corridor, Event.junction, Event.zone):
            for (value,) in db.query(column).distinct():
                if value and value.strip().lower() not in _IGNORED_LOCATIONS:
                    names.add(value.strip())
        _location_candidates = sorted(names)
    return _location_candidates


def reset_caches() -> None:
    """Clear the location-candidate cache (used by tests)."""
    global _location_candidates
    _location_candidates = None


def _impact_sentence(event: str, severity: str, location: str) -> str:
    """Compose a short, human-readable impact statement."""
    where = "" if location == "Unknown" else f" near {location}"
    return (
        f"{severity.capitalize()}-severity {event.lower()}{where} "
        "likely to disrupt traffic flow."
    )


def triage(db: Session, text: str) -> TriageResponse:
    """Run the full triage pipeline for one free-text report."""
    result = get_model().triage(text)
    event = humanize_cause(result["cause"])
    severity = result["severity"]

    match = locate(text, get_location_candidates(db))
    location = match.location if match else "Unknown"

    return TriageResponse(
        event=event,
        severity=severity,
        location=location,
        impact=_impact_sentence(event, severity, location),
        confidence=round(result["confidence"] * 100),
        actions=get_actions(result["cause"], severity),
    )
