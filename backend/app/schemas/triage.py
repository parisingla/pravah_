"""Pydantic schemas for the Triage engine (/triage)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TriageRequest(BaseModel):
    """Free-text incident report (any language) to triage."""

    text: str = Field(min_length=1, description="Incident description in any language.")


class TriageResponse(BaseModel):
    """Triaged incident summary."""

    event: str            # human-readable cause label
    severity: str         # low | moderate | high | severe
    location: str         # matched corridor/junction/zone, or "Unknown"
    impact: str           # short impact sentence
    confidence: int       # cause-classifier confidence, percent (0-100)
    actions: list[str]    # ordered recommended actions
