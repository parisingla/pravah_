"""Tests for geo helpers."""
from app.utils.geo import centroid, haversine_km


def test_haversine_zero_distance():
    assert haversine_km(12.97, 77.59, 12.97, 77.59) == 0.0


def test_haversine_known_distance():
    # Bengaluru (MG Road area) to roughly 1 degree north ~ 111 km.
    d = haversine_km(12.97, 77.59, 13.97, 77.59)
    assert 110.0 < d < 112.0


def test_centroid_basic():
    c = centroid([(0.0, 0.0), (2.0, 2.0)])
    assert c == (1.0, 1.0)


def test_centroid_skips_none_and_empty():
    assert centroid([]) is None
    assert centroid([(None, None), (4.0, 6.0)]) == (4.0, 6.0)
