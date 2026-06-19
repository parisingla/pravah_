"""STEP 3 — Foresee verification: per-corridor precision@10 + GeoJSON weight check.

Run:  .venv/Scripts/python.exe notebooks/_step3_foresee_audit.py
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
from sklearn.ensemble import HistGradientBoostingRegressor

from app.engines.foresee.hotspot import CATEGORICAL, make_features
from app.ml.pipeline import load_clean

TEST_FRACTION, SEED = 0.20, 42
IGNORED = frozenset({"non-corridor", "unknown", "none", ""})
pd.set_option("display.width", 140)
pd.set_option("display.max_rows", 60)


def line(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# Reproduce training (same as train_foresee)
df = load_clean()
corr = df["corridor"].astype("string")
mask = (df["start_datetime"].notna() & df["hour_ist"].notna() & df["dow"].notna()
        & corr.notna() & ~corr.str.strip().str.lower().isin(IGNORED))
data = df.loc[mask].copy().sort_values("start_datetime", kind="mergesort")
corridors = sorted(data["corridor"].astype(str).unique())
encoder = {c: i for i, c in enumerate(corridors)}
cut = int(len(data) * (1 - TEST_FRACTION))
train_df, test_df = data.iloc[:cut], data.iloc[cut:]

agg = train_df.groupby(["corridor", "hour_ist", "dow"], observed=True).size().reset_index(name="count")
x_train = make_features([encoder[c] for c in agg["corridor"]],
                        agg["hour_ist"].astype(int).tolist(), agg["dow"].astype(int).tolist())
y_train = agg["count"].to_numpy(dtype=float)
model = HistGradientBoostingRegressor(loss="poisson", categorical_features=CATEGORICAL,
                                      max_iter=300, learning_rate=0.05, max_depth=4,
                                      l2_regularization=1.0, random_state=SEED).fit(x_train, y_train)

# Predict whole grid
grid = [(c, h, d) for c in corridors for h in range(24) for d in range(7)]
gp = model.predict(make_features([encoder[c] for c, _, _ in grid],
                                 [h for _, h, _ in grid], [d for _, _, d in grid]))
pred_rank = [k for _, k in sorted(zip(gp, grid), key=lambda t: t[0], reverse=True)]
pred_by_corr = {c: [] for c in corridors}
for score, key in sorted(zip(gp, grid), key=lambda t: t[0], reverse=True):
    pred_by_corr[key[0]].append((key[1], key[2]))

# Relevance = (corridor,hour,dow) cells with an incident in the held-out tail
test_agg = test_df.groupby(["corridor", "hour_ist", "dow"], observed=True).size().reset_index(name="count")
relevant = {(str(r.corridor), int(r.hour_ist), int(r.dow)) for r in test_agg.itertuples()}
rel_by_corr: dict[str, set] = {c: set() for c in corridors}
for (c, h, d) in relevant:
    if c in rel_by_corr:
        rel_by_corr[c].add((h, d))


def precision_at_k(rank, rel, k):
    return len(set(rank[:k]) & rel) / float(k) if rel else 0.0


# --- 3.0 global (sanity vs registry) ---------------------------------------
line("3.0  GLOBAL precision@k (sanity vs registry)")
for k in (10, 20, 50):
    print(f"precision@{k}: {len(set(pred_rank[:k]) & relevant)/k:.4f}")

# --- 3.1 per-corridor precision@10 -----------------------------------------
line("3.1  PER-CORRIDOR precision@10  (rel = # test cells with an incident)")
recs = []
for c in corridors:
    rel = rel_by_corr[c]
    p10 = precision_at_k([(h, d) for (h, d) in pred_by_corr[c]], rel, 10)
    recs.append({"corridor": c, "test_incidents": int(test_df[test_df["corridor"].astype(str) == c].shape[0]),
                 "relevant_cells": len(rel), "precision_at_10": round(p10, 3)})
res = pd.DataFrame(recs).sort_values("precision_at_10", ascending=False).reset_index(drop=True)
print(res.to_string(index=False))

nonzero = res[res["precision_at_10"] > 0]
zero = res[res["precision_at_10"] == 0]
print(f"\nmean per-corridor p@10            : {res['precision_at_10'].mean():.3f}")
print(f"corridors with p@10 > 0           : {len(nonzero)} / {len(res)}")
print(f"corridors with p@10 == 0          : {len(zero)} / {len(res)}")
if len(zero):
    print("  near-zero corridors:", ", ".join(zero['corridor'].tolist()))
# Concentration: share of total test incidents in the corridors that have p@10>0
share = nonzero["test_incidents"].sum() / max(res["test_incidents"].sum(), 1)
print(f"share of test incidents in nonzero corridors: {share:.1%}")

# --- 3.2 GeoJSON weight normalization --------------------------------------
line("3.2  /hotspots GeoJSON — properties.weight normalized in [0,1]?")
from app.engines.foresee.hotspot import get_model

fm = get_model()
fm.load()
all_ok = True
for horizon in ("now", "1h", "2h", "4h"):
    gj = fm.hotspots_geojson(horizon)
    weights = [f["properties"]["weight"] for f in gj["features"]]
    if weights:
        lo, hi = min(weights), max(weights)
        ok = lo >= 0.0 and hi <= 1.0
        all_ok &= ok
        print(f"horizon={horizon:>3}: {len(weights):3d} pts | weight min={lo:.3f} max={hi:.3f} "
              f"| in[0,1]={ok} | max==1.0 (normalized)={abs(hi-1.0) < 1e-9 or hi <= 1.0}")
    else:
        print(f"horizon={horizon:>3}: no features")
print("\nALL horizons weights in [0,1]:", all_ok)

line("STEP 3 COMPLETE")
