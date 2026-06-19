"""Triage engine endpoint (POST /triage).

Auth-guarded under ``/api`` (a no-op when ``AUTH_DISABLED``). Thin handler — the
work lives in ``app.services.triage``.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.deps import DbSession
from app.schemas.triage import TriageRequest, TriageResponse
from app.services import triage as svc

router = APIRouter(
    prefix="/api",
    tags=["triage"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/triage", response_model=TriageResponse)
def triage(req: TriageRequest, db: DbSession) -> TriageResponse:
    """Classify a free-text incident report and recommend actions."""
    return svc.triage(db, req.text)
