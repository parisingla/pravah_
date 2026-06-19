"""Train the Clearance (duration prediction) model — Predict engine.

Three CatBoost quantile regressors (alpha = 0.1 / 0.5 / 0.9) predict event
clearance time (`duration_min`). Trained CPU-only with a **time-based** split
(earliest 80% train / latest 20% test — never random) so metrics reflect true
forward-looking performance.

Run:  python -m app.ml.train_clearance
Outputs:
  models/clearance/{p10,p50,p90}.cbm
  models/clearance/features.json
  models/registry.json   (metrics + metadata)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from app.config import settings
from app.core.logging import get_logger
from app.engines.predict.clearance import CAT_FEATURES, FEATURES, NUM_FEATURES, QUANTILES
from app.ml import evaluate
from app.ml.pipeline import load_clean

logger = get_logger("pravah.train.clearance")

TARGET = "duration_min"
MIN_DURATION = 1.0
MAX_DURATION = 2880.0  # 48h cap — drop implausible long-tail / data errors
TEST_FRACTION = 0.20
RANDOM_SEED = 42

_UNKNOWN = "unknown"
_MODEL_DIR = settings.models_dir / "clearance"

# Regularized config: on this heavy-tailed, time-shifted target it keeps P90
# coverage ~0.90 and MAE near the median baseline (deep configs over-predict the
# bulk and inflate MAE).
_CATBOOST_PARAMS = dict(
    iterations=400,
    depth=4,
    learning_rate=0.03,
    l2_leaf_reg=8,
    random_seed=RANDOM_SEED,
    verbose=False,
)


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to the trainable target range and materialize the feature matrix."""
    mask = (
        df[TARGET].notna()
        & (df[TARGET] >= MIN_DURATION)
        & (df[TARGET] <= MAX_DURATION)
        & df["start_datetime"].notna()
    )
    data = df.loc[mask].copy()

    # Cat features -> filled strings; bool/num -> ints (CatBoost-friendly).
    for col in CAT_FEATURES:
        data[col] = data[col].astype("string").fillna(_UNKNOWN).replace("", _UNKNOWN).astype(str)
    for col in NUM_FEATURES:
        data[col] = data[col].astype("float").fillna(0).astype(int)

    data[TARGET] = data[TARGET].astype(float)
    return data


def _time_split(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sort by start time; earliest 80% -> train, latest 20% -> test."""
    ordered = data.sort_values("start_datetime", kind="mergesort").reset_index(drop=True)
    cut = int(len(ordered) * (1 - TEST_FRACTION))
    return ordered.iloc[:cut], ordered.iloc[cut:]


def _pool(frame: pd.DataFrame) -> Pool:
    return Pool(
        frame[list(FEATURES)],
        label=frame[TARGET],
        cat_features=list(CAT_FEATURES),
    )


def train() -> dict:
    """Train the quantile models, persist artifacts, return the registry entry."""
    logger.info("Loading cleaned events ...")
    data = _prepare(load_clean())
    train_df, test_df = _time_split(data)
    logger.info(
        "Rows: %d total | %d train | %d test (time-based 80/20 on start_datetime)",
        len(data), len(train_df), len(test_df),
    )
    logger.info(
        "Train window: %s -> %s | Test window: %s -> %s",
        train_df["start_datetime"].min(), train_df["start_datetime"].max(),
        test_df["start_datetime"].min(), test_df["start_datetime"].max(),
    )

    train_pool, test_pool = _pool(train_df), _pool(test_df)
    y_test = test_df[TARGET].to_numpy()
    y_train = train_df[TARGET].to_numpy()

    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    preds: dict[str, np.ndarray] = {}
    for q, alpha in QUANTILES.items():
        model = CatBoostRegressor(loss_function=f"Quantile:alpha={alpha}", **_CATBOOST_PARAMS)
        model.fit(train_pool)
        model.save_model(str(_MODEL_DIR / f"{q}.cbm"))
        preds[q] = model.predict(test_pool)
        logger.info("Trained %s (alpha=%.1f) -> %s", q, alpha, f"{q}.cbm")

    # Enforce non-crossing quantiles before scoring intervals.
    p10 = np.maximum(preds["p10"], 1.0)
    p50 = np.maximum(p10, preds["p50"])
    p90 = np.maximum(p50, preds["p90"])

    metrics = {
        "p50_mae": round(evaluate.mae(y_test, p50), 3),
        "p50_rmse": round(evaluate.rmse(y_test, p50), 3),
        "pinball_p10": round(evaluate.pinball_loss(y_test, p10, 0.1), 3),
        "pinball_p50": round(evaluate.pinball_loss(y_test, p50, 0.5), 3),
        "pinball_p90": round(evaluate.pinball_loss(y_test, p90, 0.9), 3),
        "p90_coverage": round(evaluate.coverage(y_test, p90), 3),
        "median_baseline_mae": round(evaluate.median_baseline_mae(y_train, y_test), 3),
    }
    logger.info("Metrics: %s", metrics)

    # Persist the feature list (serve-time source of truth for column order).
    (_MODEL_DIR / "features.json").write_text(json.dumps(list(FEATURES), indent=2))

    entry = {
        "model": "clearance",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "target": TARGET,
        "filter": {"min": MIN_DURATION, "max": MAX_DURATION},
        "split": {"type": "time-based", "test_fraction": TEST_FRACTION},
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "features": {"categorical": list(CAT_FEATURES), "numeric": list(NUM_FEATURES)},
        "metrics": metrics,
        "artifacts": {q: f"clearance/{q}.cbm" for q in QUANTILES},
    }
    _write_registry(entry)
    return entry


def _write_registry(entry: dict) -> None:
    """Merge the clearance entry into models/registry.json."""
    registry_path = settings.models_dir / "registry.json"
    registry: dict = {}
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text())
        except json.JSONDecodeError:
            registry = {}
    registry["clearance"] = entry
    registry_path.write_text(json.dumps(registry, indent=2))
    logger.info("Wrote registry: %s", registry_path)


if __name__ == "__main__":
    result = train()
    print(json.dumps(result["metrics"], indent=2))
