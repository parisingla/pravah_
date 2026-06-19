"""#1 — Clearance log1p experiment: current vs log1p target, MAE vs baseline.

Trains the quantile models two ways on the SAME chronological split and compares
P50 MAE against the naive median baseline. No production files touched.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

import numpy as np
from catboost import CatBoostRegressor, Pool

from app.engines.predict.clearance import CAT_FEATURES, FEATURES, NUM_FEATURES, QUANTILES
from app.ml import evaluate
from app.ml.pipeline import load_clean

TARGET = "duration_min"
MIN_D, MAX_D, TEST_FRACTION, SEED, UNK = 1.0, 2880.0, 0.20, 42, "unknown"
PARAMS = dict(iterations=400, depth=4, learning_rate=0.03, l2_leaf_reg=8, random_seed=SEED, verbose=False)


def prep():
    df = load_clean()
    m = (df[TARGET].notna() & (df[TARGET] >= MIN_D) & (df[TARGET] <= MAX_D) & df["start_datetime"].notna())
    d = df.loc[m].copy()
    for c in CAT_FEATURES:
        d[c] = d[c].astype("string").fillna(UNK).replace("", UNK).astype(str)
    for c in NUM_FEATURES:
        d[c] = d[c].astype("float").fillna(0).astype(int)
    d[TARGET] = d[TARGET].astype(float)
    d = d.sort_values("start_datetime", kind="mergesort").reset_index(drop=True)
    cut = int(len(d) * (1 - TEST_FRACTION))
    return d.iloc[:cut], d.iloc[cut:]


train_df, test_df = prep()
y_train = train_df[TARGET].to_numpy()
y_test = test_df[TARGET].to_numpy()
Xtr = train_df[list(FEATURES)]
Xte = test_df[list(FEATURES)]
cat = list(CAT_FEATURES)


def fit_predict(y_tr_target):
    """Train the 3 quantiles on a (possibly transformed) target; return raw preds dict."""
    pool_tr = Pool(Xtr, label=y_tr_target, cat_features=cat)
    pool_te = Pool(Xte, cat_features=cat)
    out = {}
    for q, a in QUANTILES.items():
        out[q] = CatBoostRegressor(loss_function=f"Quantile:alpha={a}", **PARAMS).fit(pool_tr).predict(pool_te)
    return out


def metrics(p10, p50, p90):
    p10 = np.maximum(p10, 1.0)
    p50 = np.maximum(p10, p50)
    p90 = np.maximum(p50, p90)
    return {
        "p50_mae": round(evaluate.mae(y_test, p50), 2),
        "p50_rmse": round(evaluate.rmse(y_test, p50), 2),
        "pinball_p50": round(evaluate.pinball_loss(y_test, p50, 0.5), 3),
        "p90_coverage": round(evaluate.coverage(y_test, p90), 3),
    }


baseline = round(evaluate.median_baseline_mae(y_train, y_test), 2)

# --- CURRENT: train directly on minutes ------------------------------------
cur = fit_predict(y_train)
cur_m = metrics(cur["p10"], cur["p50"], cur["p90"])

# --- LOG1P: train on log1p(minutes), invert with expm1 ----------------------
logp = fit_predict(np.log1p(y_train))
log_m = metrics(np.expm1(logp["p10"]), np.expm1(logp["p50"]), np.expm1(logp["p90"]))

# --- MAE-LOSS P50: direct MAE-optimized point head (keeps minutes) ----------
pool_tr = Pool(Xtr, label=y_train, cat_features=cat)
pool_te = Pool(Xte, cat_features=cat)
mae_p50 = CatBoostRegressor(loss_function="MAE", **PARAMS).fit(pool_tr).predict(pool_te)
mae_p50 = np.maximum(mae_p50, 1.0)
mae_only_mae = round(evaluate.mae(y_test, mae_p50), 2)

print("=" * 72)
print("CLEARANCE P50 MAE vs BASELINE — current (minutes) vs log1p target")
print("=" * 72)
print(f"naive median baseline MAE : {baseline:8.2f} min   (always predict train median)")
print("-" * 72)
print(f"{'metric':<16}{'CURRENT':>14}{'LOG1P':>14}{'better?':>12}")
for k in ("p50_mae", "p50_rmse", "pinball_p50", "p90_coverage"):
    cv, lv = cur_m[k], log_m[k]
    better = "log1p" if (lv < cv if k != "p90_coverage" else abs(lv - 0.9) < abs(cv - 0.9)) else "current"
    print(f"{k:<16}{cv:>14}{lv:>14}{better:>12}")
print("-" * 72)
print(f"CURRENT  p50 MAE {cur_m['p50_mae']:.2f}  beats baseline: {cur_m['p50_mae'] < baseline}  "
      f"({(baseline - cur_m['p50_mae'])/baseline*100:+.1f}%)")
print(f"LOG1P    p50 MAE {log_m['p50_mae']:.2f}  beats baseline: {log_m['p50_mae'] < baseline}  "
      f"({(baseline - log_m['p50_mae'])/baseline*100:+.1f}%)")
print(f"MAE-LOSS p50 MAE {mae_only_mae:.2f}  beats baseline: {mae_only_mae < baseline}  "
      f"({(baseline - mae_only_mae)/baseline*100:+.1f}%)")
print("=" * 72)
