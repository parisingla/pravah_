"""Recommended-action rules for the Triage engine.

A static rule table maps (cause, severity) to an ordered, deduplicated list of
operator actions: severity-driven dispatch first, then cause-specific
remediation. Deterministic — no model, fully explainable.
"""
from __future__ import annotations

# Severity-driven response (urgency ladder).
_SEVERITY_ACTIONS: dict[str, list[str]] = {
    "severe": [
        "Escalate to control room and dispatch a senior officer",
        "Set up a diversion on an alternate corridor",
    ],
    "high": [
        "Dispatch the nearest field unit immediately",
        "Alert downstream signals to ease congestion",
    ],
    "moderate": [
        "Assign the nearest patrol to assess on site",
        "Monitor for escalation",
    ],
    "low": [
        "Log the incident and monitor",
    ],
}

# Cause-specific remediation.
_CAUSE_ACTIONS: dict[str, list[str]] = {
    "accident": ["Send ambulance and tow vehicle", "Secure the scene and clear debris"],
    "vehicle_breakdown": ["Dispatch a tow truck", "Guide the vehicle to the shoulder"],
    "water_logging": ["Notify BBMP/BWSSB for dewatering", "Place flood-warning signage"],
    "tree_fall": ["Dispatch a tree-cutting crew", "Cordon off the affected lane"],
    "pot_holes": ["Raise a repair ticket with the road authority", "Mark the hazard with cones"],
    "construction": ["Verify the work permit and signage", "Coordinate lane management with the contractor"],
    "road_conditions": ["Inspect the road surface", "Place caution signage"],
    "congestion": ["Deploy traffic marshals at the junction", "Optimize signal timing"],
    "public_event": ["Activate crowd-management plan", "Coordinate with event organisers"],
    "procession": ["Activate route-management plan", "Provide a moving escort"],
    "protest": ["Coordinate with local police", "Cordon the protest area"],
    "vip_movement": ["Clear and hold the route", "Coordinate the security escort"],
    "debris": ["Dispatch a cleanup crew", "Cordon off the affected lane"],
    "congestion / heavy traffic": ["Deploy traffic marshals", "Optimize signal timing"],
    "fog / low visibility": ["Activate fog signage", "Advise reduced speed limits"],
}

_GENERIC = ["Verify details on site", "Notify the relevant department"]


def get_actions(cause: str, severity: str) -> list[str]:
    """Ordered, deduplicated action list for a (cause, severity) pair."""
    ordered = [
        *_SEVERITY_ACTIONS.get(severity, []),
        *_CAUSE_ACTIONS.get(cause, _GENERIC),
    ]
    seen: set[str] = set()
    result: list[str] = []
    for action in ordered:
        if action not in seen:
            seen.add(action)
            result.append(action)
    return result
