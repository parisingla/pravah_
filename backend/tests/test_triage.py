"""Tests for the Triage engine: text features, locate, actions, and the API.

Pure unit tests always run. The HTTP integration tests need trained triage
artifacts (+ LaBSE cached) and a seeded DB, so they skip cleanly if missing
(run `python -m app.ml.train_triage` and `python -m app.db.seed` first).
"""
import pytest

from app.config import settings
from app.engines.triage.actions import get_actions
from app.engines.triage.locate import locate
from app.engines.triage.model import derive_severity
from app.features.text import clean_text, detect_lang

_TRIAGE_PRESENT = all(
    (settings.models_dir / "triage" / name).exists()
    for name in ("cause_head.joblib", "priority_head.joblib", "label_encoders.joblib")
)

# Native-script samples.
_KANNADA = "ಮರ ರಸ್ತೆಯ ಮೇಲೆ ಬಿದ್ದಿದೆ"  # "a tree has fallen on the road"
_HINDI = "सड़क पर पेड़ गिर गया"  # "a tree fell on the road"


# --- features/text.py ---------------------------------------------------------
def test_detect_lang():
    assert detect_lang("Tree fallen on ORR") == "latin"
    assert detect_lang(_KANNADA) == "indic"
    assert detect_lang(_HINDI) == "indic"
    assert detect_lang("") == "latin"
    assert detect_lang(None) == "latin"


def test_clean_text_collapses_whitespace():
    assert clean_text("  a\t b\n c  ") == "a b c"
    assert clean_text(None) == ""
    # Non-Latin script is preserved.
    assert clean_text(_KANNADA) == _KANNADA


# --- locate.py ----------------------------------------------------------------
def test_locate_matches_embedded_name():
    cands = ["ORR East 1", "Silk Board", "HSR Layout"]
    m = locate("Accident near Silk Board junction", cands)
    assert m is not None and m.location == "Silk Board" and m.score >= 70


def test_locate_returns_none_below_threshold():
    assert locate("completely unrelated xyz", ["Silk Board", "Peenya"]) is None
    assert locate("anything", []) is None


# --- actions.py ---------------------------------------------------------------
def test_actions_ordered_and_deduped():
    actions = get_actions("accident", "severe")
    assert actions[0].startswith("Escalate")  # severity-driven first
    assert "Send ambulance and tow vehicle" in actions  # cause-specific follows
    assert len(actions) == len(set(actions))  # no duplicates


def test_actions_unknown_cause_fallback():
    actions = get_actions("mystery", "low")
    assert "Verify details on site" in actions


# --- severity -----------------------------------------------------------------
def test_derive_severity_full_matrix():
    assert derive_severity("accident", "High") == "severe"
    assert derive_severity("vehicle_breakdown", "High") == "high"
    assert derive_severity("accident", "Low") == "moderate"
    assert derive_severity("vehicle_breakdown", "Low") == "low"


# --- HTTP integration ---------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    if not _TRIAGE_PRESENT:
        pytest.skip("triage models not trained; run python -m app.ml.train_triage")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:  # triggers lifespan -> clearance + triage + LaBSE
        yield c


def _assert_triage_shape(data: dict):
    assert data["severity"] in {"low", "moderate", "high", "severe"}
    assert 0 <= data["confidence"] <= 100
    assert isinstance(data["actions"], list) and data["actions"]
    assert data["event"] and data["impact"]
    assert isinstance(data["location"], str)


def test_triage_english(client):
    r = client.post("/api/triage", json={"text": "Car accident with injuries near Silk Board"})
    assert r.status_code == 200
    _assert_triage_shape(r.json())


def test_triage_kannada_end_to_end(client):
    r = client.post("/api/triage", json={"text": _KANNADA})
    assert r.status_code == 200
    _assert_triage_shape(r.json())


def test_triage_empty_text_rejected(client):
    assert client.post("/api/triage", json={"text": ""}).status_code == 422
