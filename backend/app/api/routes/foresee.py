"""Foresee endpoints: corridor predictions, hotspots (GeoJSON), and alerts.

Auth-guarded under ``/api``. Thin handlers — logic lives in services.foresee.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.deps import DbSession
from app.engines.foresee.hotspot import HORIZONS
from app.schemas.foresee import Alert, CorridorPrediction
from app.services import foresee as svc

router = APIRouter(prefix="/api", tags=["foresee"], dependencies=[Depends(get_current_user)])


@router.get("/predictions/corridors", response_model=list[CorridorPrediction])
def predictions_corridors(
    db: DbSession,
    horizon: str = Query(default="2h", description="Forecast horizon, e.g. 1h, 2h, 4h."),
) -> list[CorridorPrediction]:
    """Top corridors by forecast incidence probability (0-100)."""
    return svc.corridor_predictions(db, horizon)


@router.get("/hotspots")
def hotspots(
    db: DbSession,
    horizon: str = Query(default="now", description="now | 1h | 2h | 4h"),
) -> dict[str, Any]:
    """GeoJSON FeatureCollection of weighted hotspot points."""
    horizon = horizon if horizon in HORIZONS else "now"
    return svc.hotspots(db, horizon)


@router.get("/alerts", response_model=list[Alert])
def alerts(db: DbSession) -> list[Alert]:
    """Current anomaly alerts (corridor spikes + spatial clusters)."""
    return svc.alerts(db)
