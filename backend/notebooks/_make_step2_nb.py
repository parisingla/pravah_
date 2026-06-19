"""Build 05_clearance_audit.ipynb (STEP 2)."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "05_clearance_audit.ipynb"


def md(t): return {"cell_type": "markdown", "metadata": {}, "source": _l(t)}
def code(t): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _l(t)}
def _l(t):
    t = t.strip("\n"); ls = t.splitlines()
    return [x + "\n" for x in ls[:-1]] + [ls[-1]] if ls else [""]


cells = [
    md("""
# 05 — STEP 2: Clearance verification

Confirms the clearance model's split is **chronological (no leakage)**, reports
P50 MAE/RMSE, compares to a **naive median baseline**, reports **pinball loss**
per quantile, and checks **P90 coverage**. Mirrors `_step2_clearance_audit.py`.
"""),
    code("""
import os, sys
from pathlib import Path
root = Path.cwd()
while not (root / "app").is_dir() and root != root.parent:
    root = root.parent
os.chdir(root); sys.path.insert(0, str(root))

import numpy as np, pandas as pd
from catboost import CatBoostRegressor, Pool
from app.engines.predict.clearance import CAT_FEATURES, FEATURES, NUM_FEATURES, QUANTILES
from app.ml import evaluate
from app.ml.pipeline import load_clean

TARGET = "duration_min"
MIN_DURATION, MAX_DURATION, TEST_FRACTION, SEED, UNK = 1.0, 2880.0, 0.20, 42, "unknown"
PARAMS = dict(iterations=400, depth=4, learning_rate=0.03, l2_leaf_reg=8, random_seed=SEED, verbose=False)
"""),
    md("### Prepare (filter to trainable range, materialize features)"),
    code("""
df = load_clean()
m = (df[TARGET].notna() & (df[TARGET] >= MIN_DURATION) & (df[TARGET] <= MAX_DURATION) & df["start_datetime"].notna())
data = df.loc[m].copy()
for c in CAT_FEATURES:
    data[c] = data[c].astype("string").fillna(UNK).replace("", UNK).astype(str)
for c in NUM_FEATURES:
    data[c] = data[c].astype("float").fillna(0).astype(int)
data[TARGET] = data[TARGET].astype(float)
print("trainable rows:", len(data))
"""),
    md("### 2.1 — Chronological split + exact dates (confirm NOT random)"),
    code("""
ordered = data.sort_values("start_datetime", kind="mergesort").reset_index(drop=True)
cut = int(len(ordered) * (1 - TEST_FRACTION))
train_df, test_df = ordered.iloc[:cut], ordered.iloc[cut:]
print("sorted ascending:", ordered["start_datetime"].is_monotonic_increasing)
print(f"{len(train_df)} train / {len(test_df)} test (cut {cut})")
print("TRAIN:", train_df["start_datetime"].min(), "->", train_df["start_datetime"].max())
print("TEST :", test_df["start_datetime"].min(), "->", test_df["start_datetime"].max())
print("no leakage:", test_df["start_datetime"].min() >= train_df["start_datetime"].max())
"""),
    md("### Train the three quantile models"),
    code("""
def _pool(f): return Pool(f[list(FEATURES)], label=f[TARGET], cat_features=list(CAT_FEATURES))
train_pool, test_pool = _pool(train_df), _pool(test_df)
y_train, y_test = train_df[TARGET].to_numpy(), test_df[TARGET].to_numpy()
preds = {}
for q, a in QUANTILES.items():
    preds[q] = CatBoostRegressor(loss_function=f"Quantile:alpha={a}", **PARAMS).fit(train_pool).predict(test_pool)
p10 = np.maximum(preds["p10"], 1.0); p50 = np.maximum(p10, preds["p50"]); p90 = np.maximum(p50, preds["p90"])
"""),
    md("### 2.2 — P50 MAE & RMSE (minutes)"),
    code("""
print(f"P50 MAE : {evaluate.mae(y_test, p50):.2f} min")
print(f"P50 RMSE: {evaluate.rmse(y_test, p50):.2f} min")
"""),
    md("### 2.3 — Naive median baseline vs model"),
    code("""
base = evaluate.median_baseline_mae(y_train, y_test); model = evaluate.mae(y_test, p50)
print(f"train median  : {np.median(y_train):.2f} min")
print(f"baseline MAE  : {base:.2f} min")
print(f"model P50 MAE : {model:.2f} min")
print(f"improvement   : {(base-model)/base*100:+.1f}%  ->", "model better" if model < base else "WORSE than baseline")
"""),
    md("### 2.4 — Pinball loss per alpha"),
    code("""
for q, a in QUANTILES.items():
    pred = {"p10": p10, "p50": p50, "p90": p90}[q]
    print(f"alpha={a}: {evaluate.pinball_loss(y_test, pred, a):.3f}")
"""),
    md("### 2.5 — P90 coverage (target 0.85–0.95)"),
    code("""
cov = evaluate.coverage(y_test, p90)
print(f"P90 coverage: {cov:.3f} ->", "PASS" if 0.85 <= cov <= 0.95 else "FAIL")
"""),
    md("""
### Verdict

* Split is **chronological, sorted, no leakage** ✔
* P90 coverage **0.90** — in range ✔
* **P50 MAE (176) is ~6% WORSE than the median baseline (166)** ✖ — the genuine
  weak spot. The heavy-tailed target (RMSE 445) drags the conditional median.
  Candidate fixes: train on `log1p(duration)`, or add an MAE-optimized point head
  separate from the pinball quantiles.
"""),
]

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3 (.venv)", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
OUT.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", OUT)
