"""Server-Sent Events stream of event create/close (GET /stream).

Subscribes to the in-process event bus and forwards messages as SSE. Emits a
``connected`` event immediately and periodic ``heartbeat`` comments so proxies
keep the connection open.
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.event_bus import get_event_bus
from app.core.security import get_current_user

router = APIRouter(prefix="/api", tags=["stream"], dependencies=[Depends(get_current_user)])

_HEARTBEAT_SECONDS = 15


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def _event_generator(request: Request):
    bus = get_event_bus()
    queue = bus.subscribe()
    try:
        yield _sse({"type": "connected"})
        while True:
            if await request.is_disconnected():
                break
            try:
                message = await asyncio.wait_for(queue.get(), timeout=_HEARTBEAT_SECONDS)
                yield _sse(message)
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"
    finally:
        bus.unsubscribe(queue)


@router.get("/stream")
async def stream(request: Request) -> StreamingResponse:
    """Live SSE feed of incident create/close events."""
    return StreamingResponse(
        _event_generator(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
