"""Pydantic schemas for the Predict engine (/predict) and event enrichment."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Inputs for an ad-hoc clearance/severity prediction."""

    event_cause: str
    veh_type: str | None = None
    corridor: str | None = None
    zone: str | None = None
    event_type: str | None = None
    requires_road_closure: bool = False
    hour: int = Field(ge=0, le=23, description="Hour of day (IST), 0-23.")
    dow: int = Field(ge=0, le=6, description="Day of week, 0=Monday .. 6=Sunday.")


class ShapItem(BaseModel):
    """A single SHAP feature contribution (minutes vs. base value)."""

    feature: str
    value: float


class Prediction(BaseModel):
    """Quantile clearance-time estimate in minutes."""

    p10: float
    p50: float
    p90: float


class Ripple(BaseModel):
    """Spillback footprint estimate."""

    affected_km: float
    peak_in_min: int


class PredictResponse(BaseModel):
    """Full prediction payload returned by POST /predict."""

    p10: float
    p50: float
    p90: float
    severity: str
    psi: float
    shap: list[ShapItem]
