"""Anomaly detection for the Foresee engine.

Per-corridor rolling z-score on daily incident counts surfaces recent spikes; an
optional DBSCAN pass over recent active-event coordinates surfaces spatial
clusters. Produces alert dicts: {id, type, text, severity, time}.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import get_logger
from app.db.models import Event

logger = get_logger("pravah.foresee.anomaly")

_IGNORED = frozenset({"non-corridor", "unknown", "none", ""})
_WINDOW_DAYS = 7          # rolling baseline window
_Z_THRESHOLD = 2.0        # min |z| to raise a spike alert
_RECENT_DAYS = 3          # evaluate spikes within the last N days of data
_MAX_ALERTS = 15
_DBSCAN_EPS_KM = 1.0
_DBSCAN_MIN_SAMPLES = 8


def _severity_from_z(z: float) -> str:
    if z >= 4.0:
        return "severe"
    if z >= 3.0:
        return "high"
    if z >= 2.5:
        return "moderate"
    return "low"


def _spike_alerts(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(Event.corridor, Event.start_datetime)
        .filter(Event.start_datetime.isnot(None), Event.corridor.isnot(None))
        .all()
    )
    if not rows:
        return []
    df = pd.DataFrame(rows, columns=["corridor", "ts"])
    df = df[~df["corridor"].str.strip().str.lower().isin(_IGNORED)]
    if df.empty:
        return []
    df["day"] = pd.to_datetime(df["ts"]).dt.tz_localize(None).dt.floor("D")

    counts = df.groupby(["corridor", "day"]).size().rename("count").reset_index()
    full_range = pd.date_range(counts["day"].min(), counts["day"].max(), freq="D")
    last_day = full_range.max()
    recent_cutoff = last_day - pd.Timedelta(days=_RECENT_DAYS - 1)

    alerts: list[dict[str, Any]] = []
    for corridor, grp in counts.groupby("corridor"):
        series = grp.set_index("day")["count"].reindex(full_range, fill_value=0).astype(float)
        # Baseline excludes the current day (shift by 1).
        mean = series.shift(1).rolling(_WINDOW_DAYS, min_periods=_WINDOW_DAYS).mean()
        std = series.shift(1).rolling(_WINDOW_DAYS, min_periods=_WINDOW_DAYS).std()
        recent = series[series.index >= recent_cutoff]
        for day, value in recent.items():
            m, s = mean.get(day), std.get(day)
            if m is None or s is None or np.isnan(m) or np.isnan(s) or s < 1e-6:
                continue
            z = (value - m) / s
            if z < _Z_THRESHOLD:
                continue
            alerts.append(
                {
                    "id": f"spike-{corridor}-{day.date()}",
                    "type": "spike",
                    "text": (
                        f"{corridor}: {int(value)} incidents on {day.date()} "
                        f"vs ~{m:.1f} expected (z={z:.1f})."
                    ),
                    "severity": _severity_from_z(z),
                    "time": day.isoformat(),
                    "_z": z,
                }
            )
    alerts.sort(key=lambda a: a["_z"], reverse=True)
    for a in alerts:
        a.pop("_z", None)
    return alerts


def _cluster_alert(db: Session) -> list[dict[str, Any]]:
    """Optional DBSCAN over active-event coordinates -> spatial cluster alert."""
    rows = (
        db.query(Event.latitude, Event.longitude)
        .filter(
            Event.status == "active",
            Event.latitude.isnot(None),
            Event.longitude.isnot(None),
            Event.latitude != 0,
        )
        .all()
    )
    if len(rows) < _DBSCAN_MIN_SAMPLES:
        return []
    try:
        from sklearn.cluster import DBSCAN
    except ImportError:  # pragma: no cover
        return []

    coords = np.radians(np.array(rows, dtype=float))
    eps_rad = _DBSCAN_EPS_KM / 6371.0088  # haversine eps in radians
    labels = DBSCAN(eps=eps_rad, min_samples=_DBSCAN_MIN_SAMPLES, metric="haversine").fit_predict(coords)
    clustered = labels[labels >= 0]
    if clustered.size == 0:
        return []
    biggest = np.bincount(clustered).argmax()
    size = int((labels == biggest).sum())
    return [
        {
            "id": f"cluster-{biggest}",
            "type": "cluster",
            "text": f"Spatial cluster of {size} active incidents within ~{_DBSCAN_EPS_KM:.0f} km.",
            "severity": "high" if size >= 2 * _DBSCAN_MIN_SAMPLES else "moderate",
            "time": datetime.now(settings.tz).isoformat(),
        }
    ]


def detect_alerts(db: Session) -> list[dict[str, Any]]:
    """All current alerts (spike + spatial cluster), capped and ordered."""
    alerts = _spike_alerts(db)[:_MAX_ALERTS]
    alerts.extend(_cluster_alert(db))
    return alerts
