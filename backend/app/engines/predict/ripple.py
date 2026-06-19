"""Ripple (spillback) estimation for the Predict engine.

Translates a predicted clearance time into a first-order congestion footprint:
how far the queue is likely to back up (`affected_km`) and when congestion peaks
(`peak_in_min`). These are deterministic analytical heuristics derived from the
model's p50 — not random — and get replaced by the Foresee engine's spatial
propagation model in a later part.
"""
from __future__ import annotations

from dataclasses import dataclass

# Queue growth rate (km of backup per hour of clearance time).
_SPREAD_KM_PER_H_CLOSURE = 1.5
_SPREAD_KM_PER_H_OPEN = 0.8
_MAX_AFFECTED_KM = 20.0

# Congestion typically peaks partway through clearance, then recovers.
_PEAK_FRACTION = 0.4


@dataclass(frozen=True, slots=True)
class RippleResult:
    affected_km: float
    peak_in_min: int


def estimate_ripple(
    p50: float,
    requires_road_closure: bool | None,
    corridor_volume_ratio: float = 0.0,
) -> RippleResult:
    """Estimate spillback footprint from p50 clearance minutes.

    Busier corridors (`corridor_volume_ratio` in [0, 1]) spill back further.
    """
    hours = max(0.0, p50) / 60.0
    rate = _SPREAD_KM_PER_H_CLOSURE if requires_road_closure else _SPREAD_KM_PER_H_OPEN
    volume_factor = 1.0 + max(0.0, min(corridor_volume_ratio, 1.0))

    affected_km = round(min(hours * rate * volume_factor, _MAX_AFFECTED_KM), 1)
    peak_in_min = max(1, round(p50 * _PEAK_FRACTION))
    return RippleResult(affected_km=affected_km, peak_in_min=peak_in_min)
