"""Tiny in-process pub/sub bus for Server-Sent Events.

SSE handlers ``subscribe()`` to get an asyncio queue; producers (event create /
close) call ``publish()`` from any thread — delivery is marshalled back onto each
subscriber's event loop via ``call_soon_threadsafe``.
"""
from __future__ import annotations

import asyncio
from typing import Any

from app.core.logging import get_logger

logger = get_logger("pravah.event_bus")

_MAX_QUEUE = 100


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[asyncio.Queue, asyncio.AbstractEventLoop] = {}

    def subscribe(self) -> asyncio.Queue:
        """Register a subscriber bound to the current running loop."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE)
        self._subscribers[queue] = asyncio.get_running_loop()
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.pop(queue, None)

    def publish(self, event: dict[str, Any]) -> None:
        """Fan an event out to all subscribers (safe from any thread)."""
        for queue, loop in list(self._subscribers.items()):
            try:
                loop.call_soon_threadsafe(queue.put_nowait, event)
            except (RuntimeError, asyncio.QueueFull):  # pragma: no cover - best effort
                pass

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


_bus = EventBus()


def get_event_bus() -> EventBus:
    """Return the process-wide event bus singleton."""
    return _bus
