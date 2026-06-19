"""Triage classifier engine.

Two sklearn heads over LaBSE embeddings — cause (multiclass) and priority
(binary) — plus a deterministic (cause, priority) -> severity mapping. Loaded as
a process-wide singleton at startup.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from app.config import settings
from app.core.logging import get_logger
from app.features.text import clean_text, get_embedder

logger = get_logger("pravah.triage.model")

_MODEL_DIR = settings.models_dir / "triage"
CAUSE_HEAD_FILE = _MODEL_DIR / "cause_head.joblib"
PRIORITY_HEAD_FILE = _MODEL_DIR / "priority_head.joblib"
ENCODERS_FILE = _MODEL_DIR / "label_encoders.joblib"

# Causes that imply a high physical/safety impact — escalate the severity tier.
_HIGH_IMPACT_CAUSES = frozenset(
    {
        "accident",
        "tree_fall",
        "water_logging",
        "protest",
        "procession",
        "public_event",
        "vip_movement",
        "fog / low visibility",
    }
)


def derive_severity(cause: str, priority: str) -> str:
    """Map (cause, priority) to a severity tier (low|moderate|high|severe)."""
    high_impact = cause in _HIGH_IMPACT_CAUSES
    if priority == "High":
        return "severe" if high_impact else "high"
    return "moderate" if high_impact else "low"


class TriageModel:
    """Holds the loaded cause/priority heads and their label encoders."""

    def __init__(self) -> None:
        self._cause_head: Any = None
        self._priority_head: Any = None
        self._encoders: dict[str, Any] = {}

    @property
    def loaded(self) -> bool:
        return self._cause_head is not None and self._priority_head is not None

    def load(self) -> None:
        """Load joblib heads + encoders and the LaBSE embedder. Fails fast."""
        missing = [p.name for p in (CAUSE_HEAD_FILE, PRIORITY_HEAD_FILE, ENCODERS_FILE) if not p.exists()]
        if missing:
            raise FileNotFoundError(
                f"Triage model artifacts missing in {_MODEL_DIR}: {missing}. "
                "Train them first:  python -m app.ml.train_triage"
            )
        self._cause_head = joblib.load(CAUSE_HEAD_FILE)
        self._priority_head = joblib.load(PRIORITY_HEAD_FILE)
        self._encoders = joblib.load(ENCODERS_FILE)
        get_embedder().load()
        logger.info("Loaded triage heads + encoders from %s", _MODEL_DIR)

    def triage(self, text: str) -> dict[str, Any]:
        """Classify free text -> {cause, severity, priority, confidence}.

        `confidence` is the cause head's max class probability (0-1).
        """
        if not self.loaded:
            raise RuntimeError("Triage model not loaded — call load() at startup.")

        cleaned = clean_text(text)
        emb = get_embedder().encode([cleaned])

        cause_proba = self._cause_head.predict_proba(emb)[0]
        cause_idx = int(cause_proba.argmax())
        cause = str(self._encoders["cause"].inverse_transform([cause_idx])[0])
        confidence = float(cause_proba[cause_idx])

        priority_idx = int(self._priority_head.predict(emb)[0])
        priority = str(self._encoders["priority"].inverse_transform([priority_idx])[0])

        return {
            "cause": cause,
            "priority": priority,
            "severity": derive_severity(cause, priority),
            "confidence": confidence,
        }


_model = TriageModel()


def get_model() -> TriageModel:
    """Return the process-wide triage model singleton."""
    return _model
