"""Predict engine endpoint (POST /predict).

Auth-guarded under ``/api`` (a no-op when ``AUTH_DISABLED``). Thin handler — the
work lives in ``app.services.predict``.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.deps import DbSession
from app.schemas.predict import PredictRequest, PredictResponse
from app.services import predict as svc

router = APIRouter(
    prefix="/api",
    tags=["predict"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, db: DbSession) -> PredictResponse:
    """Clearance quantiles + severity/PSI + SHAP for a hypothetical event."""
    return svc.predict(db, req)
