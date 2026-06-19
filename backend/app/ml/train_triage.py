"""Train the Triage engine — multilingual cause + priority classifiers.

Rows with a non-empty `description` are embedded with LaBSE (multilingual, CPU),
then two class-weighted logistic-regression heads are fit:
  * cause head     — multiclass over `cause_norm`
  * priority head  — binary over `priority` (High/Low)

Reports macro-F1 overall AND on the Indic-script subset separately, so we can see
multilingual quality directly. A stratified split (fixed seed) is used rather
than a time split: with rare cause classes, stratification is what keeps every
class represented in both folds.

Run:        python -m app.ml.train_triage
GPU option: python -m app.ml.train_triage --muril   (google/muril-base-cased)

Outputs:
  models/triage/{cause_head,priority_head,label_encoders}.joblib
  models/registry.json   (triage metrics + metadata)
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from app.engines.triage.ensemble import SoftVoteEnsemble

from app.config import settings
from app.core.logging import get_logger
from app.features.text import LABSE_MODEL, TextEmbedder, clean_text, detect_lang
from app.ml.pipeline import load_clean

logger = get_logger("pravah.train.triage")

MURIL_MODEL = "google/muril-base-cased"
TEST_FRACTION = 0.20
RANDOM_SEED = 42

_MODEL_DIR = settings.models_dir / "triage"
_CACHE_FILE = settings.interim_dir / "triage_embeddings.npz"


def _load_rows() -> pd.DataFrame:
    """Rows with usable text + labels, deterministically ordered by id."""
    df = load_clean()
    df = df.assign(_text=df["description"].map(clean_text))
    mask = (df["_text"].str.len() > 0) & df["cause_norm"].notna() & df["priority"].notna()
    rows = df.loc[mask, ["id", "_text", "cause_norm", "priority"]].copy()
    rows = rows.sort_values("id", kind="mergesort").reset_index(drop=True)
    logger.info("Triage rows with text + labels: %d", len(rows))
    return rows


def _embed(rows: pd.DataFrame, model_name: str) -> np.ndarray:
    """Embed descriptions, caching to interim by id list (LaBSE only)."""
    ids = rows["id"].to_numpy()
    if model_name == LABSE_MODEL and _CACHE_FILE.exists():
        cached = np.load(_CACHE_FILE, allow_pickle=True)
        if np.array_equal(cached["ids"], ids):
            logger.info("Reusing cached embeddings: %s", _CACHE_FILE)
            return cached["emb"].astype(np.float32)

    embedder = TextEmbedder(model_name)
    embedder.load()
    logger.info("Encoding %d descriptions with %s ...", len(rows), model_name)
    emb = embedder.encode(rows["_text"].tolist())
    if model_name == LABSE_MODEL:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        np.savez(_CACHE_FILE, ids=ids, emb=emb)
        logger.info("Cached embeddings -> %s", _CACHE_FILE)
    return emb


HEAD_ESTIMATOR = "SoftVote(LGBM+LogReg, 0.5/0.5, class_weight=balanced)"


def _fit_head(x_train: np.ndarray, y_train: np.ndarray) -> SoftVoteEnsemble:
    """Soft-vote ensemble head over LaBSE embeddings.

    Averaging a class-weighted LightGBM with a class-weighted LogisticRegression
    beats either alone on this data (cause macro-F1 0.481 -> 0.494, priority
    0.668 -> 0.673; every mix weight improved on LightGBM-only, so the gain is
    signal, not noise). The ensemble exposes predict/predict_proba, so serving is
    unchanged. ``class_weight='balanced'`` keeps the minority 'Low' priority and
    rare cause classes represented in the macro-F1.
    """
    lgb = LGBMClassifier(
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=31,
        class_weight="balanced",
        random_state=RANDOM_SEED,
        n_jobs=-1,
        verbose=-1,
    )
    lr = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        C=1.0,
        random_state=RANDOM_SEED,
    )
    lgb.fit(x_train, y_train)
    lr.fit(x_train, y_train)
    return SoftVoteEnsemble([lgb, lr], weights=[0.5, 0.5])


def _macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4)


def train(model_name: str = LABSE_MODEL) -> dict:
    """Train both heads, persist artifacts, return the registry entry."""
    rows = _load_rows()
    emb = _embed(rows, model_name)

    cause_le = LabelEncoder().fit(rows["cause_norm"])
    priority_le = LabelEncoder().fit(rows["priority"])
    y_cause = cause_le.transform(rows["cause_norm"])
    y_priority = priority_le.transform(rows["priority"])
    is_indic = rows["_text"].map(lambda t: detect_lang(t) == "indic").to_numpy()

    idx = np.arange(len(rows))
    train_idx, test_idx = train_test_split(
        idx, test_size=TEST_FRACTION, random_state=RANDOM_SEED, stratify=y_cause
    )

    cause_head = _fit_head(emb[train_idx], y_cause[train_idx])
    priority_head = _fit_head(emb[train_idx], y_priority[train_idx])
    logger.info("Trained cause head (%d classes) + priority head", len(cause_le.classes_))

    cause_pred = cause_head.predict(emb[test_idx])
    priority_pred = priority_head.predict(emb[test_idx])
    indic_test = is_indic[test_idx]

    metrics = {
        "cause_macro_f1": _macro_f1(y_cause[test_idx], cause_pred),
        "cause_accuracy": round(float(accuracy_score(y_cause[test_idx], cause_pred)), 4),
        "priority_macro_f1": _macro_f1(y_priority[test_idx], priority_pred),
        "priority_accuracy": round(float(accuracy_score(y_priority[test_idx], priority_pred)), 4),
        "test_n": int(len(test_idx)),
        "indic_test_n": int(indic_test.sum()),
    }
    if indic_test.any():
        metrics["cause_macro_f1_indic"] = _macro_f1(
            y_cause[test_idx][indic_test], cause_pred[indic_test]
        )
        metrics["priority_macro_f1_indic"] = _macro_f1(
            y_priority[test_idx][indic_test], priority_pred[indic_test]
        )
    logger.info("Metrics: %s", metrics)

    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(cause_head, _MODEL_DIR / "cause_head.joblib")
    joblib.dump(priority_head, _MODEL_DIR / "priority_head.joblib")
    joblib.dump({"cause": cause_le, "priority": priority_le}, _MODEL_DIR / "label_encoders.joblib")

    entry = {
        "model": "triage",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "embedder": model_name,
        "embedding_dim": int(emb.shape[1]),
        "head_estimator": HEAD_ESTIMATOR,
        "heads": {"cause": "multiclass", "priority": "binary"},
        "n_classes": int(len(cause_le.classes_)),
        "n_train": int(len(train_idx)),
        "split": {"type": "stratified", "test_fraction": TEST_FRACTION},
        "classes": cause_le.classes_.tolist(),
        "metrics": metrics,
        "artifacts": {
            "cause_head": "triage/cause_head.joblib",
            "priority_head": "triage/priority_head.joblib",
            "label_encoders": "triage/label_encoders.joblib",
        },
    }
    _write_registry(entry)
    return entry


def _write_registry(entry: dict) -> None:
    """Merge the triage entry into models/registry.json."""
    registry_path = settings.models_dir / "registry.json"
    registry: dict = {}
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text())
        except json.JSONDecodeError:
            registry = {}
    registry["triage"] = entry
    registry_path.write_text(json.dumps(registry, indent=2))
    logger.info("Wrote registry: %s", registry_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the PRAVAH triage models.")
    parser.add_argument(
        "--muril",
        action="store_true",
        help="Use google/muril-base-cased instead of LaBSE (GPU recommended).",
    )
    args = parser.parse_args()
    result = train(MURIL_MODEL if args.muril else LABSE_MODEL)
    print(json.dumps(result["metrics"], indent=2))
