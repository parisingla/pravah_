"""Triage engine — multilingual classification, location, and actions.

Public surface:
- ``get_model()`` / ``TriageModel`` — cause + priority classifier singleton.
- ``derive_severity`` — (cause, priority) -> severity tier.
- ``locate`` — fuzzy match text against known corridor/junction/zone names.
- ``get_actions`` — (cause, severity) -> ordered operator actions.
"""
from app.engines.triage.actions import get_actions
from app.engines.triage.locate import LocationMatch, locate
from app.engines.triage.model import TriageModel, derive_severity, get_model

__all__ = [
    "TriageModel",
    "get_model",
    "derive_severity",
    "locate",
    "LocationMatch",
    "get_actions",
]
