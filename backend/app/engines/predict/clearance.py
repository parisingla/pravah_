"""Clearance-time engine: load the CatBoost quantile models and serve p10/p50/p90.

This module is the single source of truth for the clearance feature spec — both
the offline trainer (`app.ml.train_clearance`) and online serving import the
feature lists / builders from here so training and inference never drift.

Models are process-wide singletons loaded once at startup (`get_models().load()`).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from catboost import CatBoostRegressor, Pool

from app.config import settings
from app.core.logging import get_logger
from app.features.temporal import is_night, is_rush, is_weekend

logger = get_logger("pravah.predict.clearance")

# --- Feature spec (order matters; cat features come first) ---------------------
CAT_FEATURES: tuple[str, ...] = (
    "cause_norm",
    "veh_type",
    "corridor",
    "zone",
    "event_type",
)
NUM_FEATURES: tuple[str, ...] = (
    "requires_road_closure",
    "hour_ist",
    "dow",
    "is_weekend",
    "is_night",
    "is_rush",
)
FEATURES: tuple[str, ...] = CAT_FEATURES + NUM_FEATURES

QUANTILES: dict[str, float] = {"p10": 0.1, "p50": 0.5, "p90": 0.9}

_UNKNOWN = "unknown"
_MODEL_DIR = settings.models_dir / "clearance"
_FEATURES_FILE = _MODEL_DIR / "features.json"


# --- Feature builders (shared train + serve) ----------------------------------
def normalize_cause_scalar(cause: str | None) -> str:
    """Scalar mirror of pipeline.normalize_cause (lowercase, merge debris*)."""
    text = (cause or "").strip().lower()
    if not text:
        return _UNKNOWN
    if "debris" in text:
        return "debris"
    return text


def _cat(value: str | None) -> str:
    value = (value or "").strip()
    return value if value else _UNKNOWN


def build_features(
    *,
    event_cause: str | None,
    veh_type: str | None,
    corridor: str | None,
    zone: str | None,
    event_type: str | None,
    requires_road_closure: bool | None,
    hour: int,
    dow: int,
) -> dict[str, Any]:
    """Build one ordered feature row from raw request/ORM values.

    `is_weekend` / `is_night` / `is_rush` are derived from hour/dow via the shared
    temporal rules so they match the training pipeline exactly.
    """
    return {
        "cause_norm": normalize_cause_scalar(event_cause),
        "veh_type": _cat(veh_type),
        "corridor": _cat(corridor),
        "zone": _cat(zone),
        "event_type": _cat(event_type),
        "requires_road_closure": int(bool(requires_road_closure)),
        "hour_ist": int(hour),
        "dow": int(dow),
        "is_weekend": int(is_weekend(dow)),
        "is_night": int(is_night(hour)),
        "is_rush": int(is_rush(hour)),
    }


def to_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Ordered DataFrame with cat columns as str — the shape CatBoost expects."""
    df = pd.DataFrame(rows, columns=list(FEATURES))
    for col in CAT_FEATURES:
        df[col] = df[col].astype(str)
    return df


# --- Model singleton ----------------------------------------------------------
class ClearanceModels:
    """Holds the three loaded quantile models + the persisted feature list."""

    def __init__(self) -> None:
        self._models: dict[str, CatBoostRegressor] = {}
        self.features: list[str] = []

    @property
    def loaded(self) -> bool:
        return len(self._models) == len(QUANTILES)

    def load(self) -> None:
        """Load p10/p50/p90 .cbm files. Raises if any artifact is missing."""
        missing = [
            name
            for name in (*(f"{q}.cbm" for q in QUANTILES), "features.json")
            if not (_MODEL_DIR / name).exists()
        ]
        if missing:
            raise FileNotFoundError(
                f"Clearance model artifacts missing in {_MODEL_DIR}: {missing}. "
                "Train them first:  python -m app.ml.train_clearance"
            )
        self.features = json.loads(_FEATURES_FILE.read_text())
        for q in QUANTILES:
            model = CatBoostRegressor()
            model.load_model(str(_MODEL_DIR / f"{q}.cbm"))
            self._models[q] = model
        logger.info("Loaded clearance models (%s) from %s", ", ".join(QUANTILES), _MODEL_DIR)

    def _pool(self, df: pd.DataFrame) -> Pool:
        return Pool(df[self.features], cat_features=list(CAT_FEATURES))

    def model(self, quantile: str) -> CatBoostRegressor:
        return self._models[quantile]

    def predict_batch(self, rows: list[dict[str, Any]]) -> list[dict[str, float]]:
        """Predict {p10,p50,p90} for many feature rows (monotonic-corrected)."""
        if not self.loaded:
            raise RuntimeError("Clearance models not loaded — call load() at startup.")
        if not rows:
            return []
        pool = self._pool(to_frame(rows))
        preds = {q: self._models[q].predict(pool) for q in QUANTILES}
        out: list[dict[str, float]] = []
        for i in range(len(rows)):
            p10, p50, p90 = float(preds["p10"][i]), float(preds["p50"][i]), float(preds["p90"][i])
            # Enforce non-crossing quantiles and a 1-min floor.
            p10 = max(1.0, p10)
            p50 = max(p10, p50)
            p90 = max(p50, p90)
            out.append({"p10": round(p10, 1), "p50": round(p50, 1), "p90": round(p90, 1)})
        return out

    def predict(self, features: dict[str, Any]) -> dict[str, float]:
        """Predict {p10,p50,p90} for a single feature row."""
        return self.predict_batch([features])[0]


_models = ClearanceModels()


def get_models() -> ClearanceModels:
    """Return the process-wide clearance model singleton."""
    return _models
