"""STEP 1 — Triage audit + class-weight / LightGBM comparison.

Run:  .venv/Scripts/python.exe notebooks/_step1_triage_audit.py
Uses the cached LaBSE embeddings (data/interim/triage_embeddings.npz) so it's fast.
Prints every artifact STEP 1 asks for. The 04_triage_audit.ipynb notebook mirrors
this cell by cell.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Locate backend/ root.
root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

from app.features.text import LABSE_MODEL, TextEmbedder, clean_text, detect_lang
from app.ml.pipeline import load_clean

RANDOM_SEED = 42
TEST_FRACTION = 0.20
CACHE = Path("data/interim/triage_embeddings.npz")

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 40)


def line(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


# --------------------------------------------------------------------------- #
# Load rows + embeddings (same selection as train_triage.py)
# --------------------------------------------------------------------------- #
df = load_clean()
df = df.assign(_text=df["description"].map(clean_text))
mask = (df["_text"].str.len() > 0) & df["cause_norm"].notna() & df["priority"].notna()
rows = df.loc[mask, ["id", "_text", "cause_norm", "priority"]].copy()
rows = rows.sort_values("id", kind="mergesort").reset_index(drop=True)
ids = rows["id"].to_numpy()

if CACHE.exists():
    cached = np.load(CACHE, allow_pickle=True)
    if np.array_equal(cached["ids"], ids):
        emb = cached["emb"].astype(np.float32)
        print(f"Reusing cached embeddings {emb.shape}")
    else:
        emb = None
else:
    emb = None
if emb is None:
    embedder = TextEmbedder(LABSE_MODEL)
    embedder.load()
    emb = embedder.encode(rows["_text"].tolist())
    np.savez(CACHE, ids=ids, emb=emb)

from sklearn.preprocessing import LabelEncoder

cause_le = LabelEncoder().fit(rows["cause_norm"])
priority_le = LabelEncoder().fit(rows["priority"])
y_cause = cause_le.transform(rows["cause_norm"])
y_priority = priority_le.transform(rows["priority"])
is_indic = rows["_text"].map(lambda t: detect_lang(t) == "indic").to_numpy()

idx = np.arange(len(rows))
train_idx, test_idx = train_test_split(
    idx, test_size=TEST_FRACTION, random_state=RANDOM_SEED, stratify=y_cause
)

# --------------------------------------------------------------------------- #
# 1.1  priority class distribution (train)
# --------------------------------------------------------------------------- #
line("1.1  PRIORITY CLASS DISTRIBUTION (train set)")
train_prio = pd.Series(priority_le.inverse_transform(y_priority[train_idx]))
dist = train_prio.value_counts()
pct = (dist / dist.sum() * 100).round(1)
print(pd.DataFrame({"count": dist, "pct": pct}))
print(f"\nTotal train rows: {len(train_idx)} | classes: {list(priority_le.classes_)}")


def fit(x, y, **kw):
    clf = LogisticRegression(max_iter=2000, C=1.0, random_state=RANDOM_SEED, **kw)
    clf.fit(x, y)
    return clf


def macro_f1(yt, yp):
    return round(float(f1_score(yt, yp, average="macro", zero_division=0)), 4)


# --------------------------------------------------------------------------- #
# 1.3  Is the head currently class-weighted?  (train both ways)
# --------------------------------------------------------------------------- #
line("1.3  CURRENT CONFIG — is class_weight set?")
import inspect

from app.ml import train_triage

src = inspect.getsource(train_triage._fit_head)
weighted_now = 'class_weight="balanced"' in src or "class_weight='balanced'" in src
print(f"train_triage._fit_head uses class_weight='balanced': {weighted_now}")
print("  -> " + ("Already weighted (the requested fix is present)."
                  if weighted_now else "NOT weighted — applying the fix."))

# BEFORE = no class weights, AFTER = balanced
prio_before = fit(emb[train_idx], y_priority[train_idx])
prio_after = fit(emb[train_idx], y_priority[train_idx], class_weight="balanced")
cause_before = fit(emb[train_idx], y_cause[train_idx])
cause_after = fit(emb[train_idx], y_cause[train_idx], class_weight="balanced")

pb, pa = prio_before.predict(emb[test_idx]), prio_after.predict(emb[test_idx])
cb, ca = cause_before.predict(emb[test_idx]), cause_after.predict(emb[test_idx])
yt_p, yt_c = y_priority[test_idx], y_cause[test_idx]

# --------------------------------------------------------------------------- #
# 1.2  confusion matrix — priority (test), after fix
# --------------------------------------------------------------------------- #
line("1.2  PRIORITY CONFUSION MATRIX (test) — balanced head")
labels = list(range(len(priority_le.classes_)))
cm = confusion_matrix(yt_p, pa, labels=labels)
cm_df = pd.DataFrame(cm,
                     index=[f"true_{c}" for c in priority_le.classes_],
                     columns=[f"pred_{c}" for c in priority_le.classes_])
print(cm_df)

# --------------------------------------------------------------------------- #
# 1.4  macro-F1 before/after, both heads
# --------------------------------------------------------------------------- #
line("1.4  MACRO-F1 (and accuracy) — BEFORE vs AFTER class weights")
tbl = pd.DataFrame({
    "macro_f1_before": [macro_f1(yt_c, cb), macro_f1(yt_p, pb)],
    "macro_f1_after":  [macro_f1(yt_c, ca), macro_f1(yt_p, pa)],
    "acc_before": [round(accuracy_score(yt_c, cb), 4), round(accuracy_score(yt_p, pb), 4)],
    "acc_after":  [round(accuracy_score(yt_c, ca), 4), round(accuracy_score(yt_p, pa), 4)],
}, index=["cause (16-class)", "priority (binary)"])
print(tbl)

# --------------------------------------------------------------------------- #
# 1.5  Indic subset macro-F1
# --------------------------------------------------------------------------- #
line("1.5  INDIC SUBSET (Kannada/Hindi via detect_lang) — macro-F1")
indic_test = is_indic[test_idx]
print(f"Indic rows in test: {int(indic_test.sum())} / {len(test_idx)}")
if indic_test.any():
    print(pd.DataFrame({
        "macro_f1_after_all": [macro_f1(yt_c, ca), macro_f1(yt_p, pa)],
        "macro_f1_after_indic": [
            macro_f1(yt_c[indic_test], ca[indic_test]),
            macro_f1(yt_p[indic_test], pa[indic_test]),
        ],
    }, index=["cause", "priority"]))

# --------------------------------------------------------------------------- #
# 1.6  LightGBM comparison on the same embeddings
# --------------------------------------------------------------------------- #
line("1.6  LIGHTGBM vs LOGREG (balanced) on LaBSE embeddings — macro-F1")
try:
    from lightgbm import LGBMClassifier

    lgb_p = LGBMClassifier(
        n_estimators=400, learning_rate=0.05, num_leaves=31,
        class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1, verbose=-1,
    ).fit(emb[train_idx], y_priority[train_idx])
    lgb_c = LGBMClassifier(
        n_estimators=400, learning_rate=0.05, num_leaves=31,
        class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1, verbose=-1,
    ).fit(emb[train_idx], y_cause[train_idx])
    lp, lc = lgb_p.predict(emb[test_idx]), lgb_c.predict(emb[test_idx])
    print(pd.DataFrame({
        "logreg_balanced": [macro_f1(yt_c, ca), macro_f1(yt_p, pa)],
        "lightgbm_balanced": [macro_f1(yt_c, lc), macro_f1(yt_p, lp)],
    }, index=["cause", "priority"]))
except Exception as exc:  # pragma: no cover
    print("LightGBM unavailable:", exc)

line("STEP 1 ANALYSIS COMPLETE")
