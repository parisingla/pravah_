"""Tune the Foresee forecaster: compare configs on the SAME time-split by
precision@10/20/50 (global) AND mean per-corridor precision@10 (the honest one)."""
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
from sklearn.ensemble import HistGradientBoostingRegressor

from app.engines.foresee.hotspot import CATEGORICAL, make_features
from app.ml.pipeline import load_clean

SEED, TEST_FRACTION = 42, 0.20
IGNORED = frozenset({"non-corridor", "unknown", "none", ""})

df = load_clean()
corr = df["corridor"].astype("string")
mask = (df["start_datetime"].notna() & df["hour_ist"].notna() & df["dow"].notna()
        & corr.notna() & ~corr.str.strip().str.lower().isin(IGNORED))
data = df.loc[mask].copy().sort_values("start_datetime", kind="mergesort")
corridors = sorted(data["corridor"].astype(str).unique())
enc = {c: i for i, c in enumerate(corridors)}
cut = int(len(data) * (1 - TEST_FRACTION))
train_df, test_df = data.iloc[:cut], data.iloc[cut:]

agg = train_df.groupby(["corridor", "hour_ist", "dow"], observed=True).size().reset_index(name="count")
x_train = make_features([enc[c] for c in agg["corridor"]], agg["hour_ist"].astype(int).tolist(), agg["dow"].astype(int).tolist())
y_train = agg["count"].to_numpy(float)

test_agg = test_df.groupby(["corridor", "hour_ist", "dow"], observed=True).size().reset_index(name="count")
relevant = {(str(r.corridor), int(r.hour_ist), int(r.dow)) for r in test_agg.itertuples()}
rel_by = {c: set() for c in corridors}
for (c, h, d) in relevant:
    rel_by[c].add((h, d))

grid = [(c, h, d) for c in corridors for h in range(24) for d in range(7)]
gx = make_features([enc[c] for c, _, _ in grid], [h for _, h, _ in grid], [d for _, _, d in grid])


def score(model):
    gp = model.predict(gx)
    rank = [k for _, k in sorted(zip(gp, grid), key=lambda t: t[0], reverse=True)]
    by_corr = {c: [] for c in corridors}
    for _, key in sorted(zip(gp, grid), key=lambda t: t[0], reverse=True):
        by_corr[key[0]].append((key[1], key[2]))
    glob = {k: round(len(set(rank[:k]) & relevant) / k, 4) for k in (10, 20, 50)}
    per = [len(set(by_corr[c][:10]) & rel_by[c]) / 10.0 for c in corridors if rel_by[c]]
    return glob, round(float(np.mean(per)), 4)


def hgb(**kw):
    base = dict(loss="poisson", categorical_features=CATEGORICAL, random_state=SEED)
    return HistGradientBoostingRegressor(**{**base, **kw})


CANDS = {
    "CURRENT (300,0.05,d4,l2=1)": hgb(max_iter=300, learning_rate=0.05, max_depth=4, l2_regularization=1.0),
    "(500,0.03,d5,l2=2,mlf30)": hgb(max_iter=500, learning_rate=0.03, max_depth=5, l2_regularization=2.0, min_samples_leaf=30),
    "(800,0.02,d6,l2=3,mlf40)": hgb(max_iter=800, learning_rate=0.02, max_depth=6, l2_regularization=3.0, min_samples_leaf=40),
    "(400,0.05,d3,l2=1,mlf50)": hgb(max_iter=400, learning_rate=0.05, max_depth=3, l2_regularization=1.0, min_samples_leaf=50),
}

print("=" * 78)
print("FORESEE tuning — same time-split.  global p@10/20/50  +  mean per-corridor p@10")
print("=" * 78)
for name, model in CANDS.items():
    model.fit(x_train, y_train)
    glob, per = score(model)
    print(f"{name:30} p@10={glob[10]:.3f} p@20={glob[20]:.3f} p@50={glob[50]:.3f} | per-corr p@10={per:.3f}", flush=True)
print("=" * 78)
