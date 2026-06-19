"""API tests for the DB-only endpoints, auth, and the model-less fallback path.

Runs against an isolated in-memory SQLite DB (via a `get_db` dependency
override) seeded with a few hand-built rows, so the real `pravah.db` and the raw
CSV pipeline are never touched. The fixture forces the clearance singleton into
the *unloaded* state so these tests deterministically exercise the priority-based
fallback regardless of test ordering (see test_predict.py for the enriched path).
"""
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.db.models import Event
from app.main import app
from app.services import events as svc

# Single shared in-memory DB for the test module.
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    # Force the model-less fallback path (decouple from test ordering).
    from app.engines.predict import get_models

    get_models()._models.clear()
    svc.reset_caches()

    Base.metadata.create_all(bind=_engine)
    with _TestSession() as db:
        db.add_all(
            [
                Event(
                    id="EVT-1",
                    event_cause="vehicle_breakdown",
                    cause_norm="vehicle_breakdown",
                    priority="High",
                    status="active",
                    corridor="Mysore Rd",
                    junction="Kengeri",
                    duration_min=60.0,
                ),
                Event(
                    id="EVT-2",
                    event_cause="construction",
                    cause_norm="construction",
                    priority="Low",
                    status="active",
                    corridor="Old Madras Rd",
                    junction="KR Puram",
                    duration_min=120.0,
                ),
                Event(
                    id="EVT-3",
                    event_cause="accident",
                    cause_norm="accident",
                    priority="High",
                    status="closed",
                    corridor="Silk Board",
                    duration_min=30.0,
                ),
            ]
        )
        db.commit()

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_engine)


def test_health_has_models_loaded(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["models_loaded"] is False


def test_summary_aggregates(client):
    body = client.get("/api/summary").json()
    assert body["active_events"] == 2
    assert body["severe_count"] == 1  # active + High
    assert body["median_clearance_min"] == 60.0  # median(30, 60, 120)
    assert body["units_available"] is None


def test_events_list_filters_and_shape(client):
    rows = client.get("/api/events", params={"status": "active"}).json()
    assert {r["id"] for r in rows} == {"EVT-1", "EVT-2"}
    by_id = {r["id"]: r for r in rows}
    assert by_id["EVT-1"]["sev"] == "high"
    assert by_id["EVT-2"]["sev"] == "moderate"
    assert by_id["EVT-1"]["type"] == "Breakdown"
    assert by_id["EVT-1"]["road"] == "Mysore Rd"
    assert by_id["EVT-1"]["near"] == "Kengeri"
    # Placeholders, enriched in Part 3.
    for key in ("psi", "eta", "range", "units"):
        assert by_id["EVT-1"][key] is None


def test_event_detail_and_404(client):
    assert client.get("/api/events/EVT-3").json()["event_cause"] == "accident"
    assert client.get("/api/events/MISSING").status_code == 404


def test_create_and_close_event_publishes_to_bus(client):
    """POST create/close lifecycle: derives features, persists, fans out to SSE."""
    from app.core.event_bus import get_event_bus
    from app.db.models import Feedback

    # Capture what the create/close hooks publish to the in-process bus.
    published: list[dict] = []
    bus = get_event_bus()
    orig_publish = bus.publish
    bus.publish = lambda evt: published.append(evt)
    try:
        created = client.post(
            "/api/events",
            json={"event_cause": "accident", "corridor": "Hosur Road", "priority": "High"},
        )
        assert created.status_code == 201
        body = created.json()
        eid = body["id"]
        assert body["status"] == "active"
        assert body["cause_norm"] == "accident"
        # Temporal features were derived server-side.
        assert body["hour_ist"] is not None and body["dow"] is not None

        closed = client.post(f"/api/events/{eid}/close")
        assert closed.status_code == 200
        cbody = closed.json()
        assert cbody["status"] == "closed"
        assert cbody["duration_min"] is not None and cbody["duration_min"] >= 0
    finally:
        bus.publish = orig_publish

    # Bus saw both a create and a close.
    types = [m["type"] for m in published]
    assert "create" in types and "close" in types

    # Closing wrote a Feedback row for the online-learning loop.
    with _TestSession() as db:
        assert db.query(Feedback).filter(Feedback.event_id == eid).count() == 1

    # Unknown id -> 404 on close.
    assert client.post("/api/events/NOPE/close").status_code == 404


def test_severity_helper():
    assert svc.severity_from_priority("High") == "high"
    assert svc.severity_from_priority("Low") == "moderate"
    assert svc.severity_from_priority(None) == "moderate"


def test_auth_enforced_when_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "test-secret")

    assert client.get("/api/summary").status_code == 401
    assert (
        client.get(
            "/api/summary", headers={"Authorization": "Bearer not.a.jwt"}
        ).status_code
        == 401
    )

    expired = create_access_token({"sub": "u"}, expires_delta=timedelta(minutes=-5))
    assert (
        client.get(
            "/api/summary", headers={"Authorization": f"Bearer {expired}"}
        ).status_code
        == 401
    )

    good = create_access_token({"sub": "u", "role": "admin"})
    assert (
        client.get(
            "/api/summary", headers={"Authorization": f"Bearer {good}"}
        ).status_code
        == 200
    )
    # /health stays open even with auth enabled.
    assert client.get("/health").status_code == 200
