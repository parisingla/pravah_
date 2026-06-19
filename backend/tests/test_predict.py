"""Tests for the Predict engine: metrics, severity, ripple, and the API.

Pure unit tests always run. The HTTP integration tests need trained clearance
artifacts + a seeded DB, so they skip cleanly if either is missing (run
`python -m app.ml.train_clearance` and `python -m app.db.seed` first).
"""
import numpy as np
import pytest

from app.config import settings
from app.engines.predict.ripple import estimate_ripple
from app.engines.predict.severity import compute_severity, tier_from_psi
from app.ml import evaluate

_MODELS_PRESENT = all(
    (settings.models_dir / "clearance" / name).exists()
    for name in ("p10.cbm", "p50.cbm", "p90.cbm", "features.json")
)


# --- evaluate.py --------------------------------------------------------------
def test_mae_rmse_zero_error():
    y = [10.0, 20.0, 30.0]
    assert evaluate.mae(y, y) == 0.0
    assert evaluate.rmse(y, y) == 0.0


def test_pinball_reduces_to_half_mae_at_median():
    y = np.array([10.0, 20.0, 30.0])
    p = np.array([15.0, 15.0, 15.0])
    # At alpha=0.5 pinball loss == 0.5 * MAE.
    assert evaluate.pinball_loss(y, p, 0.5) == pytest.approx(0.5 * evaluate.mae(y, p))


def test_coverage_fraction():
    y = [10.0, 20.0, 30.0, 40.0]
    upper = [100.0, 100.0, 5.0, 100.0]  # 3 of 4 covered
    assert evaluate.coverage(y, upper) == pytest.approx(0.75)


def test_median_baseline_mae():
    # train median = 20; test errors |0|,|10| -> mae 5
    assert evaluate.median_baseline_mae([10, 20, 30], [20, 30]) == pytest.approx(5.0)


# --- severity.py --------------------------------------------------------------
def test_severity_tiers_span_full_scale():
    assert compute_severity(5, False, 0.0).severity == "low"
    full = compute_severity(480, True, 1.0)
    assert full.psi == pytest.approx(100.0)
    assert full.severity == "severe"


def test_psi_bounded_and_monotone_in_time():
    low = compute_severity(30, False, 0.0).psi
    high = compute_severity(300, False, 0.0).psi
    assert 0.0 <= low <= high <= 100.0


def test_tier_from_psi_boundaries():
    assert tier_from_psi(0) == "low"
    assert tier_from_psi(25) == "moderate"
    assert tier_from_psi(50) == "high"
    assert tier_from_psi(75) == "severe"


# --- ripple.py ----------------------------------------------------------------
def test_ripple_closure_spreads_further():
    closed = estimate_ripple(120, True, 0.0).affected_km
    open_ = estimate_ripple(120, False, 0.0).affected_km
    assert closed > open_ > 0


def test_ripple_peak_floor():
    assert estimate_ripple(0, False, 0.0).peak_in_min >= 1


# --- HTTP integration ---------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    if not _MODELS_PRESENT:
        pytest.skip("clearance models not trained; run python -m app.ml.train_clearance")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:  # triggers lifespan -> model load + DB
        yield c


def test_predict_endpoint_real(client):
    body = {
        "event_cause": "accident",
        "veh_type": "heavy_vehicle",
        "corridor": "ORR East 1",
        "zone": "HSR Layout",
        "event_type": "unplanned",
        "requires_road_closure": True,
        "hour": 18,
        "dow": 0,
    }
    r = client.post("/api/predict", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["p10"] <= data["p50"] <= data["p90"]
    assert data["severity"] in {"low", "moderate", "high", "severe"}
    assert 0.0 <= data["psi"] <= 100.0
    assert data["shap"] and all({"feature", "value"} <= s.keys() for s in data["shap"])


def test_predict_validation(client):
    # hour out of range -> 422
    assert client.post("/api/predict", json={"event_cause": "accident", "hour": 99, "dow": 0}).status_code == 422


def test_events_enriched(client):
    rows = client.get("/api/events", params={"status": "active", "limit": 1}).json()
    if not rows:
        pytest.skip("no active events seeded")
    item = rows[0]
    assert item["psi"] is not None and item["eta"] and item["range"]

    detail = client.get(f"/api/events/{item['id']}").json()
    assert {"p10", "p50", "p90"} <= detail["prediction"].keys()
    assert {"affected_km", "peak_in_min"} <= detail["ripple"].keys()
    assert detail["shap"]
