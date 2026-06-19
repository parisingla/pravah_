"""Foresee engine — spatio-temporal incident forecasting + anomaly alerts.

Public surface:
- ``get_model()`` / ``ForeseeModel`` — Poisson corridor forecaster singleton.
- ``detect_alerts`` — rolling z-score + DBSCAN anomaly alerts.
"""
from app.engines.foresee.anomaly import detect_alerts
from app.engines.foresee.hotspot import ForeseeModel, get_model

__all__ = ["ForeseeModel", "get_model", "detect_alerts"]
