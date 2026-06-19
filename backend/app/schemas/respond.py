"""Schemas for the Respond endpoint (/simulate)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SimulateRequest(BaseModel):
    """A what-if disruption scenario."""

    trigger: str = Field(min_length=1, description="Disruption type, e.g. 'accident', 'road closure'.")
    corridor: str = Field(min_length=1, description="Affected corridor name.")
    duration_hours: float = Field(gt=0, le=72, description="Expected disruption duration (hours).")


class MitigationItem(BaseModel):
    title: str
    detail: str


class SimulateResponse(BaseModel):
    """Estimated network impact + recommended mitigations."""

    network_delay: float           # added delay, minutes
    vehicles_affected: int
    emissions: float               # extra idle CO2, kg
    mitigation: list[MitigationItem]
    routes_geojson: dict[str, Any]  # GeoJSON FeatureCollection of reroutes
