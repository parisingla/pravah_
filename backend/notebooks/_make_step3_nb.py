"""Build 06_foresee_audit.ipynb (STEP 3)."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "06_foresee_audit.ipynb"


def md(t): return {"cell_type": "markdown", "metadata": {}, "source": _l(t)}
def code(t): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _l(t)}
def _l(t):
    t = t.strip("\n"); ls = t.splitlines()
    return [x + "\n" for x in ls[:-1]] + [ls[-1]] if ls else [""]


cells = [
    md("""
# 06 — STEP 3: Foresee verification

Breaks **precision@10 down per corridor** (the aggregate hides concentration) and
confirms the `/hotspots` GeoJSON `properties.weight` is normalized to **[0,1]**.
Mirrors `_step3_foresee_audit.py`.
"""),
    code("""
import os, sys
from pathlib import Path
root = Path.cwd()
while not (root / "app").is_dir() and root != root.parent:
    root = root.parent
os.chdir(root); sys.path.insert(0, str(root))

import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from app.engines.foresee.hotspot import CATEGORICAL, make_features
from app.ml.pipeline import load_clean

TEST_FRACTION, SEED = 0.20, 42
IGNORED = frozenset({"non-corridor", "unknown", "none", ""})
pd.set_option("display.max_rows", 60)
"""),
    md("### Reproduce training (valid rows, time split, aggregate, fit Poisson model)"),
    code("""
df = load_clean()
corr = df["corridor"].astype("string")
mask = (df["start_datetime"].notna() & df["hour_ist"].notna() & df["dow"].notna()
        & corr.notna() & ~corr.str.strip().str.lower().isin(IGNORED))
data = df.loc[mask].copy().sort_values("start_datetime", kind="mergesort")
corridors = sorted(data["corridor"].astype(str).unique())
encoder = {c: i for i, c in enumerate(corridors)}
cut = int(len(data) * (1 - TEST_FRACTION)); train_df, test_df = data.iloc[:cut], data.iloc[cut:]

agg = train_df.groupby(["corridor","hour_ist","dow"], observed=True).size().reset_index(name="count")
x = make_features([encoder[c] for c in agg["corridor"]], agg["hour_ist"].astype(int).tolist(), agg["dow"].astype(int).tolist())
model = HistGradientBoostingRegressor(loss="poisson", categorical_features=CATEGORICAL, max_iter=300,
                                      learning_rate=0.05, max_depth=4, l2_regularization=1.0, random_state=SEED).fit(x, agg["count"].to_numpy(float))
print("trained on", len(agg), "cells across", len(corridors), "corridors")
"""),
    md("### Rank grid + build relevance set (test-tail incident cells)"),
    code("""
grid = [(c,h,d) for c in corridors for h in range(24) for d in range(7)]
gp = model.predict(make_features([encoder[c] for c,_,_ in grid],[h for _,h,_ in grid],[d for _,_,d in grid]))
pred_rank = [k for _,k in sorted(zip(gp,grid), key=lambda t:t[0], reverse=True)]
pred_by_corr = {c: [] for c in corridors}
for _,key in sorted(zip(gp,grid), key=lambda t:t[0], reverse=True): pred_by_corr[key[0]].append((key[1],key[2]))

tagg = test_df.groupby(["corridor","hour_ist","dow"], observed=True).size().reset_index(name="count")
relevant = {(str(r.corridor),int(r.hour_ist),int(r.dow)) for r in tagg.itertuples()}
rel_by_corr = {c:set() for c in corridors}
for (c,h,d) in relevant:
    if c in rel_by_corr: rel_by_corr[c].add((h,d))
"""),
    md("### 3.0 — Global precision@k (sanity vs registry)"),
    code("""
for k in (10,20,50): print(f"precision@{k}: {len(set(pred_rank[:k]) & relevant)/k:.4f}")
"""),
    md("### 3.1 — Per-corridor precision@10 (flag concentration)"),
    code("""
def p_at_k(rank, rel, k): return len(set(rank[:k]) & rel)/float(k) if rel else 0.0
rows = [{"corridor": c,
         "test_incidents": int((test_df['corridor'].astype(str)==c).sum()),
         "relevant_cells": len(rel_by_corr[c]),
         "precision_at_10": round(p_at_k(pred_by_corr[c], rel_by_corr[c], 10), 3)}
        for c in corridors]
res = pd.DataFrame(rows).sort_values("precision_at_10", ascending=False).reset_index(drop=True)
print("GLOBAL p@10 :", round(len(set(pred_rank[:10]) & relevant)/10, 3))
print("MEAN per-corridor p@10:", round(res['precision_at_10'].mean(), 3))
print("corridors p@10==0:", res[res.precision_at_10==0]['corridor'].tolist())
res
"""),
    md("> If MEAN per-corridor << GLOBAL, the aggregate is carried by a few busy corridors."),
    md("### 3.2 — GeoJSON weight normalized to [0,1] across all horizons"),
    code("""
from app.engines.foresee.hotspot import get_model
fm = get_model(); fm.load()
for h in ("now","1h","2h","4h"):
    w = [f["properties"]["weight"] for f in fm.hotspots_geojson(h)["features"]]
    print(f"{h:>3}: {len(w):3d} pts | min={min(w):.3f} max={max(w):.3f} | in[0,1]={min(w)>=0 and max(w)<=1}")
"""),
]

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3 (.venv)", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
OUT.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", OUT)
