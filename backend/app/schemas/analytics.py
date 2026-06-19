"""Schemas for the analytics endpoint (/analytics)."""
from __future__ import annotations

from pydantic import BaseModel


class DayDistribution(BaseModel):
    """Per-day incident breakdown."""

    day: str        # YYYY-MM-DD
    accidents: int
    hazards: int


class VolumePoint(BaseModel):
    """Per-day total incident volume."""

    day: str
    count: int


class AnalyticsResponse(BaseModel):
    total_incidents: int
    avg_resolution_min: float | None
    distribution: list[DayDistribution]
    volume_trend: list[VolumePoint]
