"""Service logic for the /predict endpoint (ad-hoc clearance + severity)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.engines.predict import (
    build_features,
    compute_severity,
    explain_p50,
    get_models,
)
from app.schemas.predict import PredictRequest, PredictResponse, ShapItem
from app.services.events import corridor_ratio


def predict(db: Session, req: PredictRequest) -> PredictResponse:
    """Run the Predict engine for one hypothetical event."""
    models = get_models()
    feats = build_features(
        event_cause=req.event_cause,
        veh_type=req.veh_type,
        corridor=req.corridor,
        zone=req.zone,
        event_type=req.event_type,
        requires_road_closure=req.requires_road_closure,
        hour=req.hour,
        dow=req.dow,
    )
    pred = models.predict(feats)
    sev = compute_severity(
        pred["p50"], req.requires_road_closure, corridor_ratio(db, req.corridor)
    )
    shap = [ShapItem(**item) for item in explain_p50(models, feats)]
    return PredictResponse(
        p10=pred["p10"],
        p50=pred["p50"],
        p90=pred["p90"],
        severity=sev.severity,
        psi=sev.psi,
        shap=shap,
    )
