"""Data pipeline: raw Astram events CSV -> cleaned, feature-derived parquet.

Steps
-----
1. Read the raw CSV (all columns as strings) and treat the literal ``"NULL"``
   token (and blanks) as missing.
2. Parse the UTC start/closed timestamps (``utc=True``) and convert to IST
   (Asia/Kolkata).
3. Derive ``duration_min`` = closed - start (minutes).
4. Normalise ``event_cause`` -> ``cause_norm`` (lowercase + merge ``debris*``).
5. Fill ``veh_type`` / ``zone`` nulls with ``"unknown"``; coerce
   ``requires_road_closure`` to a real boolean.
6. Derive temporal features (``hour_ist``, ``dow``, ``is_weekend``,
   ``is_night``, ``is_rush``) from the IST start timestamp.
7. Write ``data/interim/events_clean.parquet``.

Columns ``map_file`` / ``route_path`` / ``assigned_to_police_id`` are dropped and
must never be used downstream.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from app.config import settings
from app.core.logging import get_logger
from app.features.temporal import (
    EVENING_RUSH,
    MORNING_RUSH,
    NIGHT_END_HOUR,
    NIGHT_START_HOUR,
)

logger = get_logger("pravah.pipeline")

# Columns that must never be used downstream (PII / leakage / non-features).
FORBIDDEN_COLUMNS = ("map_file", "route_path", "assigned_to_police_id")

# Tokens treated as missing values when reading the raw CSV.
NULL_TOKENS = ("NULL", "null", "Null", "NaN", "nan", "", "None")

# Canonical string columns carried through to the cleaned dataset.
_STRING_COLUMNS = (
    "event_type",
    "event_cause",
    "priority",
    "status",
    "veh_type",
    "corridor",
    "zone",
    "junction",
    "description",
)

OUTPUT_PARQUET_NAME = "events_clean.parquet"


# --------------------------------------------------------------------------- #
# Column detection
# --------------------------------------------------------------------------- #
def _find_column(columns: list[str], *candidates: str) -> str | None:
    """Return the first dataframe column matching any candidate (case-insensitive)."""
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def _detect_timestamp_columns(columns: list[str]) -> tuple[str, str]:
    """Locate the start and closed UTC timestamp columns.

    Names vary across exports, so detect by intent: a 'start' column and a
    'closed'/'end' column. Explicit common names are tried first.
    """
    start = _find_column(
        columns, "start_datetime", "event_start", "start_time", "started_at", "start"
    )
    closed = _find_column(
        columns,
        "closed_datetime",
        "event_closed",
        "closed_time",
        "closed_at",
        "end_datetime",
        "end_time",
        "resolved_at",
        "closed",
    )
    if start is None:
        start = next((c for c in columns if "start" in c.lower()), None)
    if closed is None:
        closed = next(
            (c for c in columns if any(k in c.lower() for k in ("clos", "end", "resolv"))),
            None,
        )
    if start is None or closed is None:
        raise ValueError(
            "Could not detect start/closed timestamp columns in CSV. "
            f"Columns seen: {columns}"
        )
    return start, closed


# --------------------------------------------------------------------------- #
# Field-level transforms
# --------------------------------------------------------------------------- #
def normalize_cause(series: pd.Series) -> pd.Series:
    """Lowercase the cause and merge any debris variant into a single 'debris'."""
    norm = series.astype("string").str.strip().str.lower()
    norm = norm.where(~norm.str.contains("debris", na=False), "debris")
    return norm


def _coerce_bool(series: pd.Series) -> pd.Series:
    """Coerce assorted truthy/falsy string tokens to a nullable boolean."""
    truthy = {"true", "1", "yes", "y", "t"}
    falsy = {"false", "0", "no", "n", "f"}
    s = series.astype("string").str.strip().str.lower()
    out = s.map(lambda v: True if v in truthy else (False if v in falsy else pd.NA))
    return out.astype("boolean")


def _to_ist(series: pd.Series) -> pd.Series:
    """Parse a UTC timestamp series and convert to IST (tz-aware)."""
    parsed = pd.to_datetime(series, utc=True, errors="coerce")
    return parsed.dt.tz_convert(settings.TIMEZONE)


def _derive_temporal(df: pd.DataFrame, ts_col: str) -> pd.DataFrame:
    """Vectorized temporal features matching app.features.temporal rules."""
    ts = df[ts_col]
    hour = ts.dt.hour
    dow = ts.dt.dayofweek  # Monday=0
    df["hour_ist"] = hour.astype("Int16")
    df["dow"] = dow.astype("Int8")
    df["is_weekend"] = (dow >= 5).astype("boolean")
    df["is_night"] = ((hour >= NIGHT_START_HOUR) | (hour < NIGHT_END_HOUR)).astype("boolean")
    is_rush = hour.isin(list(MORNING_RUSH)) | hour.isin(list(EVENING_RUSH))
    df["is_rush"] = is_rush.astype("boolean")
    return df


# --------------------------------------------------------------------------- #
# Main entry points
# --------------------------------------------------------------------------- #
def run_pipeline(
    csv_path: Path | str | None = None,
    output_path: Path | str | None = None,
) -> pd.DataFrame:
    """Run the full clean+feature pipeline and write the interim parquet.

    Returns the cleaned dataframe.
    """
    csv_path = Path(csv_path) if csv_path else settings.raw_csv_path
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Raw CSV not found at {csv_path}. Place the Astram event CSV in "
            "data/raw/ (see .env RAW_CSV_PATH)."
        )

    output_path = (
        Path(output_path)
        if output_path
        else settings.interim_dir / OUTPUT_PARQUET_NAME
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Reading raw CSV: %s", csv_path)
    raw = pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_values=list(NULL_TOKENS))
    logger.info("Read %d rows, %d columns", len(raw), raw.shape[1])

    columns = list(raw.columns)
    start_col, closed_col = _detect_timestamp_columns(columns)
    id_col = _find_column(columns, "id", "event_id") or columns[0]
    closure_col = _find_column(
        columns, "requires_road_closure", "road_closure", "requires_closure"
    )
    lat_col = _find_column(columns, "latitude", "lat")
    lon_col = _find_column(columns, "longitude", "lon", "lng")

    df = pd.DataFrame()
    df["id"] = raw[id_col].astype("string")

    for col in _STRING_COLUMNS:
        src = _find_column(columns, col)
        df[col] = raw[src].astype("string") if src else pd.Series(pd.NA, index=raw.index, dtype="string")

    # Coordinates
    df["latitude"] = pd.to_numeric(raw[lat_col], errors="coerce") if lat_col else np.nan
    df["longitude"] = pd.to_numeric(raw[lon_col], errors="coerce") if lon_col else np.nan

    # Road closure boolean
    df["requires_road_closure"] = (
        _coerce_bool(raw[closure_col]) if closure_col else pd.Series(pd.NA, index=raw.index, dtype="boolean")
    )

    # Timestamps -> IST
    df["start_datetime"] = _to_ist(raw[start_col])
    df["closed_datetime"] = _to_ist(raw[closed_col])

    # Duration in minutes (closed - start)
    delta = df["closed_datetime"] - df["start_datetime"]
    df["duration_min"] = (delta.dt.total_seconds() / 60.0).round(2)
    # Guard against clock-skew / bad rows producing negative durations.
    df.loc[df["duration_min"] < 0, "duration_min"] = np.nan

    # Normalised cause
    df["cause_norm"] = normalize_cause(df["event_cause"])

    # Null fills
    df["veh_type"] = df["veh_type"].fillna("unknown")
    df["zone"] = df["zone"].fillna("unknown")

    # Temporal features from IST start
    df = _derive_temporal(df, "start_datetime")

    logger.info(
        "Cleaned %d rows | %d with valid duration | %d unique causes",
        len(df),
        int(df["duration_min"].notna().sum()),
        df["cause_norm"].nunique(dropna=True),
    )

    df.to_parquet(output_path, index=False)
    logger.info("Wrote interim parquet: %s", output_path)
    return df


def load_clean(output_path: Path | str | None = None) -> pd.DataFrame:
    """Load the cleaned parquet, running the pipeline first if it is missing."""
    output_path = (
        Path(output_path) if output_path else settings.interim_dir / OUTPUT_PARQUET_NAME
    )
    if not output_path.exists():
        return run_pipeline(output_path=output_path)
    return pd.read_parquet(output_path)


if __name__ == "__main__":
    run_pipeline()
