"""STEP 2 — Clearance verification. Reproduces the real training split + metrics.

Run:  .venv/Scripts/python.exe notebooks/_step2_clearance_audit.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from app.engines.predict.clearance import CAT_FEATURES, FEATURES, NUM_FEATURES, QUANTILES
from app.ml import evaluate
from app.ml.pipeline import load_clean

TARGET = "duration_min"
MIN_DURATION, MAX_DURATION = 1.0, 2880.0
TEST_FRACTION, RANDOM_SEED, _UNKNOWN = 0.20, 42, "unknown"
_CATBOOST_PARAMS = dict(iterations=400, depth=4, learning_rate=0.03,
                        l2_leaf_reg=8, random_seed=RANDOM_SEED, verbose=False)


def line(t):
    print("\n" + "=" * 74 + f"\n{t}\n" + "=" * 74)


# Prepare (same as train_clearance._prepare)
df = load_clean()
mask = (df[TARGET].notna() & (df[TARGET] >= MIN_DURATION)
        & (df[TARGET] <= MAX_DURATION) & df["start_datetime"].notna())
data = df.loc[mask].copy()
for c in CAT_FEATURES:
    data[c] = data[c].astype("string").fillna(_UNKNOWN).replace("", _UNKNOWN).astype(str)
for c in NUM_FEATURES:
    data[c] = data[c].astype("float").fillna(0).astype(int)
data[TARGET] = data[TARGET].astype(float)

# --- 2.1 chronological split + dates ---------------------------------------
line("2.1  TRAIN/TEST SPLIT — chronological (earliest 80% / latest 20%)")
ordered = data.sort_values("start_datetime", kind="mergesort").reset_index(drop=True)
is_sorted = ordered["start_datetime"].is_monotonic_increasing
cut = int(len(ordered) * (1 - TEST_FRACTION))
train_df, test_df = ordered.iloc[:cut], ordered.iloc[cut:]
print(f"sorted by start_datetime ascending: {is_sorted}")
print(f"rows: {len(ordered)} total | {len(train_df)} train | {len(test_df)} test "
      f"(cut at index {cut} = {(1-TEST_FRACTION):.0%})")
print(f"TRAIN window: {train_df['start_datetime'].min()}  ->  {train_df['start_datetime'].max()}")
print(f"TEST  window: {test_df['start_datetime'].min()}  ->  {test_df['start_datetime'].max()}")
overlap = test_df['start_datetime'].min() >= train_df['start_datetime'].max()
print(f"test starts at/after train ends (no leakage): {overlap}")

# Train the three quantile models
def _pool(f):
    return Pool(f[list(FEATURES)], label=f[TARGET], cat_features=list(CAT_FEATURES))
train_pool, test_pool = _pool(train_df), _pool(test_df)
y_train, y_test = train_df[TARGET].to_numpy(), test_df[TARGET].to_numpy()
preds = {}
for q, a in QUANTILES.items():
    m = CatBoostRegressor(loss_function=f"Quantile:alpha={a}", **_CATBOOST_PARAMS)
    m.fit(train_pool)
    preds[q] = m.predict(test_pool)
p10 = np.maximum(preds["p10"], 1.0)
p50 = np.maximum(p10, preds["p50"])
p90 = np.maximum(p50, preds["p90"])

# --- 2.2 P50 MAE/RMSE -------------------------------------------------------
line("2.2  P50 point-estimate error (minutes)")
mae50, rmse50 = evaluate.mae(y_test, p50), evaluate.rmse(y_test, p50)
print(f"P50 MAE : {mae50:8.2f} min")
print(f"P50 RMSE: {rmse50:8.2f} min")

# --- 2.3 median baseline ----------------------------------------------------
line("2.3  Naive median baseline (always predict train median)")
train_median = float(np.median(y_train))
base_mae = evaluate.median_baseline_mae(y_train, y_test)
print(f"train median        : {train_median:8.2f} min")
print(f"baseline MAE        : {base_mae:8.2f} min")
print(f"model P50 MAE       : {mae50:8.2f} min")
improv = (base_mae - mae50) / base_mae * 100
print(f"improvement vs base : {improv:+6.1f}%  "
      f"({'model better' if mae50 < base_mae else 'WORSE than baseline'})")

# --- 2.4 pinball losses -----------------------------------------------------
line("2.4  Pinball (quantile) loss per alpha — lower is better")
print(f"alpha=0.1: {evaluate.pinball_loss(y_test, p10, 0.1):8.3f}")
print(f"alpha=0.5: {evaluate.pinball_loss(y_test, p50, 0.5):8.3f}")
print(f"alpha=0.9: {evaluate.pinball_loss(y_test, p90, 0.9):8.3f}")

# --- 2.5 P90 coverage -------------------------------------------------------
line("2.5  P90 coverage — fraction of actuals <= predicted P90")
cov = evaluate.coverage(y_test, p90)
ok = 0.85 <= cov <= 0.95
print(f"P90 coverage: {cov:.3f}   target [0.85, 0.95] -> {'PASS' if ok else 'FAIL'}")

line("STEP 2 COMPLETE")
