"""Severity scoring for the Predict engine.

Combines the predicted clearance time (p50), whether the event requires a road
closure, and how busy its corridor is (corridor volume) into a single Predicted
Severity Index (PSI, 0-100) and a discrete severity tier.

PSI is a transparent weighted blend (not a learned model) so it stays
explainable and stable; the foresee/triage engines refine it in later parts.
"""
from __future__ import annotations

from dataclasses import dataclass

# PSI component weights (sum to 1.0).
_W_TIME = 0.55
_W_CLOSURE = 0.20
_W_VOLUME = 0.25

# p50 minutes mapped to a 0-1 "long clearance" score; 8h saturates the scale.
_TIME_SATURATION_MIN = 480.0

# Severity tier cut points on PSI.
_TIERS = ((25.0, "low"), (50.0, "moderate"), (75.0, "high"))
SEVERITIES = ("low", "moderate", "high", "severe")


@dataclass(frozen=True, slots=True)
class SeverityResult:
    severity: str
    psi: float


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def tier_from_psi(psi: float) -> str:
    for threshold, label in _TIERS:
        if psi < threshold:
            return label
    return "severe"


def compute_severity(
    p50: float,
    requires_road_closure: bool | None,
    corridor_volume_ratio: float,
) -> SeverityResult:
    """Score severity from p50 (min), closure flag, and corridor volume ratio.

    `corridor_volume_ratio` is the corridor's event count normalized to [0, 1]
    against the busiest corridor (computed by the caller from the DB).
    """
    time_score = _clamp01(p50 / _TIME_SATURATION_MIN)
    closure_score = 1.0 if requires_road_closure else 0.0
    volume_score = _clamp01(corridor_volume_ratio)

    psi = 100.0 * (_W_TIME * time_score + _W_CLOSURE * closure_score + _W_VOLUME * volume_score)
    psi = round(_clamp01(psi / 100.0) * 100.0, 1)
    return SeverityResult(severity=tier_from_psi(psi), psi=psi)
