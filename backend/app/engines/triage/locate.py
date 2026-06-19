"""Fuzzy location resolution for the Triage engine.

Matches free text against the known set of corridor / junction / zone names
(from the events table) using RapidFuzz. Returns the best match above a score
threshold, or None when nothing plausible is found (e.g. native-script text with
Latin place names).
"""
from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz, process

# Minimum similarity (0-100) to accept a match.
DEFAULT_THRESHOLD = 70.0

# Placeholder location tokens that should never be returned as matches.
_IGNORED = frozenset({"unknown", "non-corridor", "none", ""})


@dataclass(frozen=True, slots=True)
class LocationMatch:
    location: str
    score: float


def locate(
    text: str,
    candidates: list[str],
    threshold: float = DEFAULT_THRESHOLD,
) -> LocationMatch | None:
    """Best fuzzy match of `text` against `candidates`, or None below threshold.

    Uses token-set ratio so a short place name embedded in a longer description
    still scores well.
    """
    if not text or not candidates:
        return None
    best = process.extractOne(text, candidates, scorer=fuzz.token_set_ratio)
    if best is None:
        return None
    name, score, _ = best
    if score < threshold or name.strip().lower() in _IGNORED:
        return None
    return LocationMatch(location=name, score=round(float(score), 1))
