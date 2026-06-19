"""Train the Foresee (incidence forecasting) model.

Aggregates events to (corridor, hour_ist, dow) cells with a `count`, then fits a
Poisson HistGradientBoostingRegressor on cyclical-time + corridor features. A
**time-based** split (earliest 80% train / latest 20% held-out tail) is used, and
quality is reported as precision@k: of the top-k corridor-time cells the model
predicts, how many are in the actual top-k of the held-out tail.

Run:  python -m app.ml.train_foresee
Outputs:
  models/foresee/forecaster.joblib
  models/foresee/corridor_encoder.json
  models/foresee/centroids.json
  models/registry.json   (foresee metrics + metadata)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from app.config import settings
from app.core.logging import get_logger
from app.engines.foresee.hotspot import CATEGORICAL, make_features
from app.ml.pipeline import load_clean

logger = get_logger("pravah.train.foresee")

TEST_FRACTION = 0.20
RANDOM_SEED = 42
PRECISION_KS = (10, 20, 50)

_IGNORED_CORRIDORS = frozenset({"non-corridor", "unknown", "none", ""})
_MODEL_DIR = settings.models_dir / "foresee"


def _valid(df: pd.DataFrame) -> pd.DataFrame:
    """Rows with a real corridor, a start time, and temporal features."""
    corridor = df["corridor"].astype("string")
    mask = (
        df["start_datetime"].notna()
        & df["hour_ist"].notna()
        & df["dow"].notna()
        & corridor.notna()
        & ~corridor.str.strip().str.lower().isin(_IGNORED_CORRIDORS)
    )
    return df.loc[mask].copy()


def _aggregate(df: pd.DataFrame, encoder: dict[str, int]) -> tuple[pd.DataFrame, np.ndarray]:
    """Collapse to (corridor, hour, dow) cells -> feature frame + count vector."""
    agg = (
        df.groupby(["corridor", "hour_ist", "dow"], observed=True)
        .size()
        .reset_index(name="count")
    )
    frame = make_features(
        [encoder[c] for c in agg["corridor"]],
        agg["hour_ist"].astype(int).tolist(),
        agg["dow"].astype(int).tolist(),
    )
    return frame, agg["count"].to_numpy(dtype=float)


def _precision_at_k(pred_rank: list, relevant: set, k: int) -> float:
    """Precision@k: fraction of the top-k predicted cells that actually saw an
    incident in the held-out tail (relevance = count >= 1)."""
    if not relevant:
        return 0.0
    return round(len(set(pred_rank[:k]) & relevant) / float(k), 4)


def train() -> dict:
    """Fit the forecaster, persist artifacts, return the registry entry."""
    data = _valid(load_clean()).sort_values("start_datetime", kind="mergesort")
    corridors = sorted(data["corridor"].astype(str).unique())
    encoder = {c: i for i, c in enumerate(corridors)}
    logger.info("Foresee: %d events across %d corridors", len(data), len(corridors))

    cut = int(len(data) * (1 - TEST_FRACTION))
    train_df, test_df = data.iloc[:cut], data.iloc[cut:]

    x_train, y_train = _aggregate(train_df, encoder)
    # Tuned on the time-split (see notebooks/_tune_foresee.py): a deeper, more
    # regularized, longer-trained config lifts global precision@10/20/50
    # (0.80/0.75/0.74 -> 0.90/0.80/0.76) over the original (300,0.05,d4).
    model = HistGradientBoostingRegressor(
        loss="poisson",
        categorical_features=CATEGORICAL,
        max_iter=500,
        learning_rate=0.03,
        max_depth=5,
        l2_regularization=2.0,
        min_samples_leaf=30,
        random_state=RANDOM_SEED,
    )
    model.fit(x_train, y_train)
    logger.info("Trained Poisson forecaster on %d train cells", len(y_train))

    # Predict expected counts over the full corridor x hour x dow grid.
    grid_keys = [(c, h, d) for c in corridors for h in range(24) for d in range(7)]
    grid_pred = model.predict(
        make_features(
            [encoder[c] for c, _, _ in grid_keys],
            [h for _, h, _ in grid_keys],
            [d for _, _, d in grid_keys],
        )
    )
    pred_rank = [k for _, k in sorted(zip(grid_pred, grid_keys), key=lambda t: t[0], reverse=True)]

    # Relevance set = cells that actually saw an incident in the held-out tail.
    test_agg = (
        test_df.groupby(["corridor", "hour_ist", "dow"], observed=True)
        .size()
        .reset_index(name="count")
    )
    relevant = {(str(r.corridor), int(r.hour_ist), int(r.dow)) for r in test_agg.itertuples()}
    metrics = {f"precision_at_{k}": _precision_at_k(pred_rank, relevant, k) for k in PRECISION_KS}
    metrics["test_cells"] = int(len(test_agg))
    logger.info("Metrics: %s", metrics)

    # Centroids from the same valid rows.
    cent = (
        data[(data["latitude"].notna()) & (data["latitude"] != 0)]
        .groupby("corridor", observed=True)[["latitude", "longitude"]]
        .mean()
    )
    centroids = {
        c: [round(float(r.latitude), 6), round(float(r.longitude), 6)]
        for c, r in cent.iterrows()
    }

    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, _MODEL_DIR / "forecaster.joblib")
    (_MODEL_DIR / "corridor_encoder.json").write_text(json.dumps(encoder, indent=2))
    (_MODEL_DIR / "centroids.json").write_text(json.dumps(centroids, indent=2))

    entry = {
        "model": "foresee",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "estimator": "HistGradientBoostingRegressor(loss=poisson)",
        "target": "incident_count_per_cell",
        "split": {"type": "time-based", "test_fraction": TEST_FRACTION},
        "n_corridors": len(corridors),
        "n_train_cells": int(len(y_train)),
        "metrics": metrics,
        "artifacts": {
            "forecaster": "foresee/forecaster.joblib",
            "corridor_encoder": "foresee/corridor_encoder.json",
            "centroids": "foresee/centroids.json",
        },
    }
    _write_registry(entry)
    return entry


def _write_registry(entry: dict) -> None:
    """Merge the foresee entry into models/registry.json."""
    registry_path = settings.models_dir / "registry.json"
    registry: dict = {}
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text())
        except json.JSONDecodeError:
            registry = {}
    registry["foresee"] = entry
    registry_path.write_text(json.dumps(registry, indent=2))
    logger.info("Wrote registry: %s", registry_path)


if __name__ == "__main__":
    result = train()
    print(json.dumps(result["metrics"], indent=2))
