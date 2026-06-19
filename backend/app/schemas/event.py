"""Pydantic v2 schemas for events.

`EventRead` mirrors the full ORM row; `EventListItem` is the trimmed dashboard
shape consumed by the frontend events list. Request/response models for the
engine endpoints are added in later parts.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.predict import Prediction, Ripple, ShapItem


class EventRead(BaseModel):
    """Serialized event row."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str | None = None
    event_cause: str | None = None
    priority: str | None = None
    status: str | None = None
    veh_type: str | None = None
    corridor: str | None = None
    zone: str | None = None
    junction: str | None = None
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    requires_road_closure: bool | None = None
    start_datetime: datetime | None = None
    closed_datetime: datetime | None = None
    duration_min: float | None = None
    cause_norm: str | None = None
    hour_ist: int | None = None
    dow: int | None = None
    is_weekend: bool | None = None
    is_night: bool | None = None
    is_rush: bool | None = None


class EventCreate(BaseModel):
    """Request body for creating a live event (POST /api/events).

    Only `event_cause` is required. `id` is auto-generated when omitted;
    `start_datetime` defaults to now (IST). Derived fields (`cause_norm`, temporal
    flags, `status`) are computed server-side.
    """

    id: str | None = None
    event_cause: str = Field(min_length=1, description="Raw cause, e.g. 'accident'.")
    event_type: str | None = None
    priority: str | None = None
    veh_type: str | None = None
    corridor: str | None = None
    zone: str | None = None
    junction: str | None = None
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    requires_road_closure: bool = False
    start_datetime: datetime | None = None


class EventListItem(BaseModel):
    """Compact event card for the dashboard list.

    `sev` is derived from `priority` (High→high / Low→moderate). `psi`, `eta`,
    `range`, and `units` are placeholders here and get filled by the predict /
    respond engines in Part 3.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: str
    road: str | None = None
    near: str | None = None
    sev: str
    psi: float | None = None
    eta: str | None = None
    # `range_` avoids shadowing the builtin; serialized as "range".
    range_: str | None = Field(default=None, alias="range")
    units: int | None = None


class EventDetail(EventRead):
    """Full event row enriched with the Predict engine outputs.

    `prediction` / `ripple` / `shap` are None only if the clearance models are
    unavailable (they are loaded fail-fast at startup).
    """

    prediction: Prediction | None = None
    ripple: Ripple | None = None
    shap: list[ShapItem] | None = None
