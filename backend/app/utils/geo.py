"""Geospatial helpers — haversine distance and centroid."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088

Coord = tuple[float, float]  # (latitude, longitude)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two (lat, lon) points in kilometres."""
    lat1_r, lon1_r, lat2_r, lon2_r = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    return haversine_km(lat1, lon1, lat2, lon2) * 1000.0


def centroid(points: Iterable[Sequence[float]]) -> Coord | None:
    """Arithmetic mean of (lat, lon) points. Returns None for an empty input.

    Adequate for small, geographically-local clusters (single city corridors);
    not a spherical centroid, which is unnecessary at this scale.
    """
    lat_sum = lon_sum = 0.0
    count = 0
    for lat, lon in points:
        if lat is None or lon is None:
            continue
        lat_sum += float(lat)
        lon_sum += float(lon)
        count += 1
    if count == 0:
        return None
    return (lat_sum / count, lon_sum / count)
