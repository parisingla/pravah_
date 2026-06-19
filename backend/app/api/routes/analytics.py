"""Analytics endpoint: incident totals and trends (GET /analytics)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.deps import DbSession
from app.schemas.analytics import AnalyticsResponse
from app.services import analytics as svc

router = APIRouter(prefix="/api", tags=["analytics"], dependencies=[Depends(get_current_user)])


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(
    db: DbSession,
    range: str = Query(default="7d", description="Window, e.g. 7d, 30d."),
) -> AnalyticsResponse:
    """Incident totals, average resolution, daily distribution, and volume trend."""
    return svc.analytics(db, range)
