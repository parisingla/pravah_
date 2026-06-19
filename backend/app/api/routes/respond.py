"""Respond endpoint: what-if scenario simulation (POST /simulate)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.deps import DbSession
from app.schemas.respond import SimulateRequest, SimulateResponse
from app.services import respond as svc

router = APIRouter(prefix="/api", tags=["respond"], dependencies=[Depends(get_current_user)])


@router.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest, db: DbSession) -> SimulateResponse:
    """Estimate network delay, vehicles affected, emissions, and mitigations."""
    return svc.simulate(db, req)
