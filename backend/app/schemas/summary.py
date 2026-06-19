"""Dashboard summary schema (top-of-page KPI tiles)."""
from __future__ import annotations

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    """Aggregate KPIs computed from the events table.

    `units_available` is a placeholder (None) until the respond engine adds a
    fleet/units inventory in a later part — there is no units source in the DB.
    """

    active_events: int
    median_clearance_min: float | None = None
    units_available: int | None = None
    severe_count: int
