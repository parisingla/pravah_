"""Service logic for the /analytics endpoint (real DB aggregates)."""
from __future__ import annotations

import re

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Event
from app.schemas.analytics import AnalyticsResponse, DayDistribution, VolumePoint

# cause_norm buckets for the daily distribution.
_ACCIDENT = {"accident"}
_HAZARD = {
    "water_logging",
    "tree_fall",
    "pot_holes",
    "debris",
    "road_conditions",
    "fog / low visibility",
}

_DEFAULT_DAYS = 7


def _parse_range_days(range_str: str | None) -> int:
    """Parse '7d' / '30d' / '12w' -> number of days (defaults to 7)."""
    if not range_str:
        return _DEFAULT_DAYS
    m = re.fullmatch(r"\s*(\d+)\s*([dwm]?)\s*", range_str.lower())
    if not m:
        return _DEFAULT_DAYS
    n = int(m.group(1))
    unit = m.group(2) or "d"
    return n * {"d": 1, "w": 7, "m": 30}[unit]


def analytics(db: Session, range_str: str | None) -> AnalyticsResponse:
    """Incident totals/trends over the last N days of available data.

    The window is anchored to the most recent event in the DB (the seed is
    historical), so the response always contains real data.
    """
    days = _parse_range_days(range_str)
    latest = db.query(func.max(Event.start_datetime)).scalar()
    if latest is None:
        return AnalyticsResponse(
            total_incidents=0, avg_resolution_min=None, distribution=[], volume_trend=[]
        )

    end_day = pd.Timestamp(latest).tz_localize(None).floor("D")
    start_day = end_day - pd.Timedelta(days=days - 1)

    rows = (
        db.query(Event.start_datetime, Event.cause_norm, Event.duration_min)
        .filter(Event.start_datetime >= start_day.to_pydatetime())
        .all()
    )
    df = pd.DataFrame(rows, columns=["ts", "cause_norm", "duration_min"])

    full_days = pd.date_range(start_day, end_day, freq="D")
    if df.empty:
        distribution = [DayDistribution(day=str(d.date()), accidents=0, hazards=0) for d in full_days]
        volume = [VolumePoint(day=str(d.date()), count=0) for d in full_days]
        return AnalyticsResponse(
            total_incidents=0, avg_resolution_min=None, distribution=distribution, volume_trend=volume
        )

    df["day"] = pd.to_datetime(df["ts"]).dt.tz_localize(None).dt.floor("D")
    df = df[df["day"] <= end_day]
    cause = df["cause_norm"].astype("string").fillna("")
    df["is_accident"] = cause.isin(_ACCIDENT)
    df["is_hazard"] = cause.isin(_HAZARD)

    grouped = df.groupby("day")
    daily = grouped.agg(
        count=("ts", "size"),
        accidents=("is_accident", "sum"),
        hazards=("is_hazard", "sum"),
    ).reindex(full_days, fill_value=0)

    avg_resolution = df["duration_min"].dropna()
    avg_resolution_min = round(float(avg_resolution.mean()), 2) if not avg_resolution.empty else None

    distribution = [
        DayDistribution(day=str(d.date()), accidents=int(r["accidents"]), hazards=int(r["hazards"]))
        for d, r in daily.iterrows()
    ]
    volume_trend = [
        VolumePoint(day=str(d.date()), count=int(r["count"])) for d, r in daily.iterrows()
    ]

    return AnalyticsResponse(
        total_incidents=int(len(df)),
        avg_resolution_min=avg_resolution_min,
        distribution=distribution,
        volume_trend=volume_trend,
    )
