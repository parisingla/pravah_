"""Temporal feature derivation from an IST timestamp.

Single source of truth for the calendar/time-of-day rules used by both the
offline pipeline (vectorized over pandas) and online inference (scalar). Keep the
rule definitions here so training and serving never drift.

Rules
-----
- ``hour_ist`` : hour 0-23 in IST.
- ``dow``      : day of week, 0=Monday .. 6=Sunday.
- ``is_weekend``: Saturday/Sunday.
- ``is_night`` : 22:00-04:59 inclusive (22-05 window).
- ``is_rush``  : 08:00-10:59 or 17:00-20:59 (8-11 | 17-21 windows).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

NIGHT_START_HOUR = 22  # inclusive
NIGHT_END_HOUR = 5     # exclusive -> covers 22,23,0,1,2,3,4
MORNING_RUSH = range(8, 11)   # 8,9,10
EVENING_RUSH = range(17, 21)  # 17,18,19,20


def is_weekend(dow: int) -> bool:
    return dow >= 5


def is_night(hour: int) -> bool:
    return hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR


def is_rush(hour: int) -> bool:
    return hour in MORNING_RUSH or hour in EVENING_RUSH


@dataclass(frozen=True, slots=True)
class TemporalFeatures:
    hour_ist: int
    dow: int
    is_weekend: bool
    is_night: bool
    is_rush: bool

    def as_dict(self) -> dict[str, int | bool]:
        return asdict(self)


def derive_temporal_features(ts_ist: datetime) -> TemporalFeatures:
    """Derive temporal features from a timezone-aware IST datetime.

    The datetime is expected to already be in IST (Asia/Kolkata). Naive
    datetimes are treated as already-IST wall-clock time.
    """
    hour = ts_ist.hour
    dow = ts_ist.weekday()  # Monday=0
    return TemporalFeatures(
        hour_ist=hour,
        dow=dow,
        is_weekend=is_weekend(dow),
        is_night=is_night(hour),
        is_rush=is_rush(hour),
    )
