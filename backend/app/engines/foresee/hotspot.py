"""Foresee hotspot engine: corridor incidence forecasting -> GeoJSON heat points.

Single source of truth for the foresee feature spec (shared by the trainer and
serving). Loads a HistGradientBoostingRegressor (Poisson) plus the corridor
encoder and centroids as a process-wide singleton, and turns per-corridor
expected counts into a GeoJSON FeatureCollection of jittered, weighted points.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("pravah.foresee.hotspot")

# Feature columns; corridor_code is categorical.
FEATURE_COLUMNS = ["corridor_code", "hour", "hour_sin", "hour_cos", "dow", "is_weekend"]
CATEGORICAL = ["corridor_code"]

# Horizon label -> hours offset from "now".
HORIZONS = {"now": 0, "1h": 1, "2h": 2, "4h": 4}

# Heat-point generation.
_MAX_POINTS_PER_CORRIDOR = 8
_JITTER_DEG = 0.004  # ~450 m

_MODEL_DIR = settings.models_dir / "foresee"
_MODEL_FILE = _MODEL_DIR / "forecaster.joblib"
_ENCODER_FILE = _MODEL_DIR / "corridor_encoder.json"
_CENTROIDS_FILE = _MODEL_DIR / "centroids.json"


def make_features(corridor_codes: list[int], hours: list[int], dows: list[int]) -> pd.DataFrame:
    """Build the foresee feature frame (cyclical hour encoding)."""
    hour_arr = np.asarray(hours, dtype=float)
    df = pd.DataFrame(
        {
            "corridor_code": np.asarray(corridor_codes, dtype=np.int32),
            "hour": hour_arr,
            "hour_sin": np.sin(2 * math.pi * hour_arr / 24.0),
            "hour_cos": np.cos(2 * math.pi * hour_arr / 24.0),
            "dow": np.asarray(dows, dtype=float),
            "is_weekend": (np.asarray(dows) >= 5).astype(float),
        },
        columns=FEATURE_COLUMNS,
    )
    return df


class ForeseeModel:
    """Holds the loaded forecaster, corridor encoder, and centroids."""

    def __init__(self) -> None:
        self._model: Any = None
        self.encoder: dict[str, int] = {}
        self.centroids: dict[str, tuple[float, float]] = {}

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        missing = [p.name for p in (_MODEL_FILE, _ENCODER_FILE, _CENTROIDS_FILE) if not p.exists()]
        if missing:
            raise FileNotFoundError(
                f"Foresee model artifacts missing in {_MODEL_DIR}: {missing}. "
                "Train them first:  python -m app.ml.train_foresee"
            )
        self._model = joblib.load(_MODEL_FILE)
        self.encoder = json.loads(_ENCODER_FILE.read_text())
        self.centroids = {k: tuple(v) for k, v in json.loads(_CENTROIDS_FILE.read_text()).items()}
        logger.info("Loaded foresee model (%d corridors) from %s", len(self.encoder), _MODEL_DIR)

    # --- core prediction ------------------------------------------------------
    def expected_counts(self, hour: int, dow: int) -> dict[str, float]:
        """Predicted expected incident count per corridor at (hour, dow)."""
        if not self.loaded:
            raise RuntimeError("Foresee model not loaded — call load() at startup.")
        corridors = list(self.encoder)
        codes = [self.encoder[c] for c in corridors]
        frame = make_features(codes, [hour] * len(codes), [dow] * len(codes))
        preds = np.clip(self._model.predict(frame), 0.0, None)
        return dict(zip(corridors, (float(p) for p in preds)))

    def _target_time(self, horizon: str, now: datetime | None = None) -> datetime:
        now = now or datetime.now(settings.tz)
        return now + timedelta(hours=HORIZONS.get(horizon, 0))

    # --- public outputs -------------------------------------------------------
    def corridor_probabilities(
        self, horizon: str, now: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Per-corridor P(>=1 incident) over the horizon, as a percentage 0-100."""
        target = self._target_time(horizon, now)
        counts = self.expected_counts(target.hour, target.weekday())
        out = []
        for corridor, lam in counts.items():
            prob = (1.0 - math.exp(-max(lam, 0.0))) * 100.0
            out.append({"corridor": corridor, "prob": round(prob, 1), "expected": round(lam, 3)})
        out.sort(key=lambda r: r["prob"], reverse=True)
        return out

    def hotspots_geojson(self, horizon: str, now: datetime | None = None) -> dict[str, Any]:
        """GeoJSON FeatureCollection of jittered, weighted heat points."""
        target = self._target_time(horizon, now)
        counts = self.expected_counts(target.hour, target.weekday())
        top = max(counts.values(), default=0.0) or 1.0

        rng = np.random.default_rng(seed=int(target.hour) * 7 + int(target.weekday()))
        features: list[dict[str, Any]] = []
        for corridor, lam in counts.items():
            if corridor not in self.centroids:
                continue
            weight = round(lam / top, 3)
            lat, lng = self.centroids[corridor]
            n_points = max(1, round(weight * _MAX_POINTS_PER_CORRIDOR))
            for _ in range(n_points):
                jlat = lat + float(rng.uniform(-_JITTER_DEG, _JITTER_DEG))
                jlng = lng + float(rng.uniform(-_JITTER_DEG, _JITTER_DEG))
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [round(jlng, 6), round(jlat, 6)]},
                        "properties": {
                            "corridor": corridor,
                            "weight": weight,
                            "expected_count": round(lam, 3),
                            "horizon": horizon,
                        },
                    }
                )
        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {"horizon": horizon, "target_time": target.isoformat()},
        }


_model = ForeseeModel()


def get_model() -> ForeseeModel:
    """Return the process-wide foresee model singleton."""
    return _model
