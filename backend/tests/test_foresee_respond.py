"""Tests for the Foresee + Respond engines, analytics, and their endpoints.

Pure unit tests always run. HTTP integration tests need all trained model
artifacts + a seeded DB, so they skip cleanly if missing (run
`python -m app.ml.train_all` and `python -m app.db.seed` first).
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.database import Base
from app.db.models import Event, Feedback
from app.engines.respond.optimizer import EventDemand, Unit, optimize
from app.engines.respond.whatif import _mitigations
from app.learning.feedback import on_event_close

_ALL_MODELS = all(
    [
        (settings.models_dir / "clearance" / "p50.cbm").exists(),
        (settings.models_dir / "triage" / "cause_head.joblib").exists(),
        (settings.models_dir / "foresee" / "forecaster.joblib").exists(),
    ]
)


# --- optimizer (pure) ---------------------------------------------------------
def test_optimizer_prefers_high_value_within_range():
    # Two events; one unit near event A (high value), far from B.
    units = [Unit("u1", 12.97, 77.59)]
    events = [
        EventDemand("A", p50=120, priority="high", lat=12.971, lng=77.591),  # close, high value
        EventDemand("B", p50=30, priority="low", lat=13.30, lng=77.90),       # far away
    ]
    plan = optimize(events, units, max_km=8.0)
    assert plan.units_used == 1
    assert plan.assignments[0].event_id == "A"


def test_optimizer_respects_distance_limit():
    units = [Unit("u1", 12.97, 77.59)]
    events = [EventDemand("Far", p50=999, priority="high", lat=20.0, lng=80.0)]
    plan = optimize(events, units, max_km=8.0)
    assert plan.units_used == 0  # nothing in range


def test_optimizer_empty_inputs():
    assert optimize([], [Unit("u", 0, 0)]).units_used == 0
    assert optimize([EventDemand("e", 10, "low", 0, 0)], []).units_used == 0


# --- whatif mitigations (pure) ------------------------------------------------
def test_mitigations_are_typed_per_trigger():
    for trigger in ("accident", "water logging", "road closure", "VIP movement", "anything"):
        items = _mitigations(trigger)
        assert items and all({"title", "detail"} <= m.keys() for m in items)


# --- feedback (isolated in-memory DB) -----------------------------------------
def test_feedback_written_on_close():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        event = Event(id="C-1", status="closed", corridor="Mysore Road", duration_min=42.0)
        db.add(event)
        db.commit()
        fb = on_event_close(db, event)
        assert fb.event_id == "C-1"
        assert fb.actual_duration_min == 42.0
        assert db.query(Feedback).count() == 1


# --- HTTP integration ---------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    if not _ALL_MODELS:
        pytest.skip("models not trained; run python -m app.ml.train_all")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:  # lifespan loads all engines + warms caches
        yield c


def _is_feature_collection(gj: dict) -> bool:
    if gj.get("type") != "FeatureCollection" or not isinstance(gj.get("features"), list):
        return False
    for f in gj["features"]:
        if f.get("type") != "Feature":
            return False
        if "geometry" not in f or "coordinates" not in f["geometry"]:
            return False
    return True


@pytest.mark.parametrize("horizon", ["now", "1h", "2h", "4h"])
def test_hotspots_valid_geojson(client, horizon):
    r = client.get("/api/hotspots", params={"horizon": horizon})
    assert r.status_code == 200
    gj = r.json()
    assert _is_feature_collection(gj)
    assert gj["features"], "expected at least one hotspot point"
    for f in gj["features"]:
        w = f["properties"]["weight"]
        assert 0.0 <= w <= 1.0
        lng, lat = f["geometry"]["coordinates"]
        assert 12.0 < lat < 14.0 and 77.0 < lng < 78.5  # Bengaluru-ish


def test_predictions_corridors(client):
    r = client.get("/api/predictions/corridors", params={"horizon": "2h"})
    assert r.status_code == 200
    rows = r.json()
    assert rows
    for row in rows:
        assert {"route", "from", "prob"} <= row.keys()
        assert 0.0 <= row["prob"] <= 100.0


def test_alerts(client):
    r = client.get("/api/alerts")
    assert r.status_code == 200
    for a in r.json():
        assert {"id", "type", "text", "severity", "time"} <= a.keys()
        assert a["severity"] in {"low", "moderate", "high", "severe"}


def test_simulate_full_schema(client):
    body = {"trigger": "accident", "corridor": "Mysore Road", "duration_hours": 3}
    r = client.post("/api/simulate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {
        "network_delay",
        "vehicles_affected",
        "emissions",
        "mitigation",
        "routes_geojson",
    }
    assert isinstance(data["network_delay"], (int, float)) and data["network_delay"] >= 0
    assert isinstance(data["vehicles_affected"], int)
    assert isinstance(data["emissions"], (int, float))
    assert data["mitigation"] and all({"title", "detail"} <= m.keys() for m in data["mitigation"])
    assert _is_feature_collection(data["routes_geojson"])


def test_simulate_validation(client):
    assert client.post("/api/simulate", json={"trigger": "x", "corridor": "y", "duration_hours": 0}).status_code == 422


def test_analytics_real_aggregates(client):
    r = client.get("/api/analytics", params={"range": "7d"})
    assert r.status_code == 200
    data = r.json()
    assert data["total_incidents"] > 0
    assert len(data["distribution"]) == 7
    assert len(data["volume_trend"]) == 7
    # Volume trend totals should reconcile with total_incidents.
    assert sum(v["count"] for v in data["volume_trend"]) == data["total_incidents"]
    for d in data["distribution"]:
        assert {"day", "accidents", "hazards"} <= d.keys()


def test_summary_units_available_real(client):
    data = client.get("/api/summary").json()
    assert data["units_available"] is not None
    assert 0 <= data["units_available"] <= settings.RESPOND_FLEET_SIZE


def test_stream_generator_emits_connected():
    """Exercise the SSE generator directly (consuming the live HTTP stream via
    TestClient would block on the infinite generator)."""
    import asyncio

    from app.api.routes.stream import _event_generator

    class _FakeRequest:
        async def is_disconnected(self) -> bool:
            return False

    async def first_message() -> str:
        gen = _event_generator(_FakeRequest())
        try:
            return await gen.__anext__()
        finally:
            await gen.aclose()

    msg = asyncio.run(first_message())
    assert "connected" in msg and msg.startswith("data: ")


def test_stream_publishes_bus_events():
    """A published event reaches a subscriber queue."""
    import asyncio

    from app.core.event_bus import get_event_bus

    async def roundtrip():
        bus = get_event_bus()
        q = bus.subscribe()
        bus.publish({"type": "create", "event": {"id": "X"}})
        msg = await asyncio.wait_for(q.get(), timeout=2)
        bus.unsubscribe(q)
        return msg

    msg = asyncio.run(roundtrip())
    assert msg["type"] == "create" and msg["event"]["id"] == "X"
