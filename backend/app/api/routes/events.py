"""Events & summary endpoints (DB-only).

All routes here live under ``/api`` and require auth (a no-op when
``AUTH_DISABLED``). Handlers stay thin — the work lives in
``app.services.events``.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import DbSession
from app.core.security import get_current_user
from app.schemas.event import EventCreate, EventDetail, EventListItem
from app.schemas.summary import SummaryResponse
from app.services import events as svc

router = APIRouter(
    prefix="/api",
    tags=["events"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary", response_model=SummaryResponse)
def get_summary(db: DbSession) -> SummaryResponse:
    """Dashboard KPI tiles (active events, median clearance, units, severe)."""
    return svc.build_summary(db)


@router.get("/events", response_model=list[EventListItem])
def list_events(
    db: DbSession,
    status: str | None = Query(default="active", description="Filter by event status."),
    limit: int = Query(default=svc.DEFAULT_LIMIT, ge=1, le=svc.MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[EventListItem]:
    """Paginated event cards, newest first."""
    return svc.list_events(db, status=status, limit=limit, offset=offset)


@router.post("/events", response_model=EventDetail, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: DbSession) -> EventDetail:
    """Create a live event and publish a `create` to the SSE stream."""
    event = svc.create_event(db, payload)
    return svc.get_event_detail(db, event.id)


@router.get("/events/{event_id}", response_model=EventDetail)
def get_event(event_id: str, db: DbSession) -> EventDetail:
    """Full event row enriched with prediction, ripple, and SHAP."""
    detail = svc.get_event_detail(db, event_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id!r} not found",
        )
    return detail


@router.post("/events/{event_id}/close", response_model=EventDetail)
def close_event(event_id: str, db: DbSession) -> EventDetail:
    """Close an active event and publish a `close` to the SSE stream."""
    event = svc.close_event(db, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id!r} not found",
        )
    return svc.get_event_detail(db, event.id)
