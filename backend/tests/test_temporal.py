"""Tests for temporal feature derivation rules."""
from datetime import datetime

from app.features.temporal import (
    derive_temporal_features,
    is_night,
    is_rush,
    is_weekend,
)


def test_dow_monday_is_zero():
    # 2026-06-15 is a Monday
    feats = derive_temporal_features(datetime(2026, 6, 15, 12, 0))
    assert feats.dow == 0
    assert feats.is_weekend is False


def test_weekend_detection():
    # 2026-06-20 is a Saturday
    assert is_weekend(derive_temporal_features(datetime(2026, 6, 20, 9, 0)).dow) is True
    # 2026-06-21 is a Sunday
    assert derive_temporal_features(datetime(2026, 6, 21, 9, 0)).is_weekend is True


def test_night_window_22_to_05():
    assert is_night(22) is True
    assert is_night(23) is True
    assert is_night(0) is True
    assert is_night(4) is True
    assert is_night(5) is False
    assert is_night(12) is False
    assert is_night(21) is False


def test_rush_windows():
    for h in (8, 9, 10):
        assert is_rush(h) is True
    for h in (17, 18, 19, 20):
        assert is_rush(h) is True
    for h in (11, 12, 16, 21, 7):
        assert is_rush(h) is False


def test_full_derivation_rush_morning():
    feats = derive_temporal_features(datetime(2026, 6, 18, 9, 30))  # Thursday 09:30
    assert feats.hour_ist == 9
    assert feats.dow == 3
    assert feats.is_rush is True
    assert feats.is_night is False
    assert feats.is_weekend is False
