"""Soft-vote ensemble test: LightGBM + LogReg on LaBSE embeddings.

Trains both heads once on the train split, then evaluates the probability-averaged
ensemble at several mix weights on the held-out test (macro-F1, overall + Indic).
Writes results to /tmp progressively so progress is visible.
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

import numpy as np
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from app.features.text import clean_text, detect_lang
from app.ml.pipeline import load_clean

SEED, TEST_FRACTION = 42, 0.20
CACHE = Path("data/interim/triage_embeddings.npz")


def log(msg):
    print(msg, flush=True)


df = load_clean().assign(_text=lambda d: d["description"].map(clean_text))
m = (df["_text"].str.len() > 0) & df["cause_norm"].notna() & df["priority"].notna()
rows = df.loc[m, ["id", "_text", "cause_norm", "priority"]].sort_values("id", kind="mergesort").reset_index(drop=True)
cached = np.load(CACHE, allow_pickle=True)
assert np.array_equal(cached["ids"], rows["id"].to_numpy())
emb = cached["emb"].astype(np.float32)

cause_le = LabelEncoder().fit(rows["cause_norm"])
prio_le = LabelEncoder().fit(rows["priority"])
y_cause = cause_le.transform(rows["cause_norm"])
y_prio = prio_le.transform(rows["priority"])
indic = rows["_text"].map(lambda t: detect_lang(t) == "indic").to_numpy()
tr, te = train_test_split(np.arange(len(rows)), test_size=TEST_FRACTION, random_state=SEED, stratify=y_cause)
it = indic[te]


def mf1(yt, yp): return round(float(f1_score(yt, yp, average="macro", zero_division=0)), 4)


def evaluate(name, y, n_classes):
    log(f"\n--- {name} ---")
    lgb = LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                         class_weight="balanced", random_state=SEED, n_jobs=-1, verbose=-1)
    lr = LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0, random_state=SEED)
    log("  fitting LightGBM ..."); lgb.fit(emb[tr], y[tr])
    log("  fitting LogReg ..."); lr.fit(emb[tr], y[tr])

    # Align proba columns to 0..n_classes-1 (both use sorted labels -> already aligned).
    p_lgb = lgb.predict_proba(emb[te])
    p_lr = lr.predict_proba(emb[te])
    yt = y[te]

    for w in (1.0, 0.8, 0.6, 0.5, 0.0):  # weight on LightGBM
        pred = (w * p_lgb + (1 - w) * p_lr).argmax(1)
        tag = {1.0: "LGBM only", 0.0: "LogReg only"}.get(w, f"ens w={w}")
        log(f"  {tag:14} macroF1={mf1(yt, pred):.4f}  acc={accuracy_score(yt, pred):.4f}  "
            f"macroF1@Indic={mf1(yt[it], pred[it]):.4f}")


evaluate("CAUSE (16-class)", y_cause, len(cause_le.classes_))
evaluate("PRIORITY (binary)", y_prio, len(prio_le.classes_))
log("\nDONE")
