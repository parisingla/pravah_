"""Idempotent database seeding: run the pipeline, then bulk-insert events.

Usage:
    python -m app.db.seed

Re-running is safe: the `events` table is truncated and reloaded from the
freshly-cleaned parquet so the DB always mirrors the current pipeline output.
"""
from __future__ import annotations

import math
from datetime import datetime

import pandas as pd

from app.core.database import SessionLocal, init_db
from app.core.logging import get_logger
from app.db.models import Event
from app.ml.pipeline import run_pipeline

logger = get_logger("pravah.seed")

# DataFrame column -> Event attribute. (Names already align, but explicit is safe.)
_EVENT_FIELDS = (
    "id",
    "event_type",
    "event_cause",
    "priority",
    "status",
    "veh_type",
    "corridor",
    "zone",
    "junction",
    "description",
    "latitude",
    "longitude",
    "requires_road_closure",
    "start_datetime",
    "closed_datetime",
    "duration_min",
    "cause_norm",
    "hour_ist",
    "dow",
    "is_weekend",
    "is_night",
    "is_rush",
)


def _clean(value: object) -> object:
    """Convert pandas missing markers / numpy scalars to plain Python / None."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    # pandas/numpy scalar -> native python
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return value.item()
        except (ValueError, AttributeError):
            return value
    return value


def _records(df: pd.DataFrame) -> list[dict]:
    records: list[dict] = []
    for row in df.to_dict(orient="records"):
        records.append({field: _clean(row.get(field)) for field in _EVENT_FIELDS})
    return records


def seed(csv_path: str | None = None) -> int:
    """Run the pipeline and (re)load all events into the database.

    Returns the number of rows inserted.
    """
    init_db()
    df = run_pipeline(csv_path=csv_path)
    df = df.drop_duplicates(subset="id", keep="first")
    records = _records(df)

    started = datetime.now()
    with SessionLocal() as session:
        deleted = session.query(Event).delete()
        if deleted:
            logger.info("Cleared %d existing event rows (idempotent reload)", deleted)
        session.bulk_insert_mappings(Event, records)
        session.commit()
        total = session.query(Event).count()

    logger.info(
        "Seed complete: %d rows inserted (%d in table) in %.2fs",
        len(records),
        total,
        (datetime.now() - started).total_seconds(),
    )
    return total


if __name__ == "__main__":
    count = seed()
    print(f"Seeded {count} events into the database.")
