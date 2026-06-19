"""SQLAlchemy ORM models.

`events` stores the raw Astram columns plus pipeline-derived columns (all
timestamps in IST). `feedback` records realized vs. predicted clearance times to
feed the online-learning loop in later parts.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Event(Base):
    """A traffic incident/event (one row per Astram event)."""

    __tablename__ = "events"

    # Source identifier from the CSV.
    id: Mapped[str] = mapped_column(String, primary_key=True)

    # --- Raw categorical / descriptive columns ---
    event_type: Mapped[str | None] = mapped_column(String, nullable=True)       # planned/unplanned
    event_cause: Mapped[str | None] = mapped_column(String, nullable=True)
    priority: Mapped[str | None] = mapped_column(String, nullable=True)         # High/Low
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    veh_type: Mapped[str | None] = mapped_column(String, nullable=True)         # null->unknown
    corridor: Mapped[str | None] = mapped_column(String, nullable=True)
    zone: Mapped[str | None] = mapped_column(String, nullable=True)             # null->unknown
    junction: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Geo ---
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Flags ---
    requires_road_closure: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # --- Timestamps (IST) ---
    start_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Derived ---
    duration_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    cause_norm: Mapped[str | None] = mapped_column(String, nullable=True)
    hour_ist: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dow: Mapped[int | None] = mapped_column(Integer, nullable=True)            # 0=Mon
    is_weekend: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_night: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_rush: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    __table_args__ = (
        Index("ix_events_status", "status"),
        Index("ix_events_corridor", "corridor"),
        Index("ix_events_event_cause", "event_cause"),
        Index("ix_events_start_datetime", "start_datetime"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Event id={self.id!r} cause_norm={self.cause_norm!r} status={self.status!r}>"


class Feedback(Base):
    """Realized clearance outcome vs. model prediction (online-learning signal)."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String, index=True)
    predicted_p50: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_duration_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Feedback event_id={self.event_id!r} actual={self.actual_duration_min!r}>"
