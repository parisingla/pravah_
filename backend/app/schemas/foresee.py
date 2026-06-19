"""Schemas for the Foresee endpoints (/predictions/corridors, /hotspots, /alerts)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CorridorPrediction(BaseModel):
    """Forecast row for a corridor over a horizon."""

    model_config = ConfigDict(populate_by_name=True)

    route: str
    # `from_` serialized as "from" (reserved word).
    from_: str = Field(alias="from")
    prob: float  # P(>=1 incident) over the horizon, 0-100


class Alert(BaseModel):
    """An anomaly alert."""

    id: str
    type: str
    text: str
    severity: str  # low | moderate | high | severe
    time: str      # ISO timestamp


# /hotspots returns a raw GeoJSON FeatureCollection (dict) — no fixed schema.
