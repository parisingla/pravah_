"""Generate rich, friendly per-model training notebooks.

Each notebook mirrors app/ml/train_*.py but decomposed into runnable cells with
emoji status prints, summary stats, and dataframe previews — so running it top to
bottom reads like a guided walkthrough. Run from anywhere:

    python notebooks/_make_notebooks.py
"""
from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": _lines(text)}


def _lines(text: str) -> list[str]:
    text = text.strip("\n")
    lines = text.splitlines()
    return [ln + "\n" for ln in lines[:-1]] + [lines[-1]] if lines else [""]


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3 (.venv)", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


SETUP = """
# 📦 Setup — locate the backend/ root (folder containing app/ and models/)
import os, sys
from pathlib import Path

root = Path.cwd()
while not (root / "app").is_dir() and root != root.parent:
    root = root.parent
os.chdir(root)
sys.path.insert(0, str(root))
print("✅ Environment ready")
print(f"   📂 Working dir : {os.getcwd()}")
print(f"   🐍 Python      : {sys.version.split()[0]}")
"""


# --------------------------------------------------------------------------- #
# 01 — Clearance
# --------------------------------------------------------------------------- #
def clearance_nb() -> dict:
    return notebook([
        md("""
# 🕒 Clearance Model — *how long until this incident clears?*

Three **CatBoost quantile regressors** (P10 / P50 / P90) predict event clearance
time in minutes. Trained CPU-only on a **chronological 80/20 split** (earliest 80%
train, latest 20% test) so the metrics reflect real forward-looking performance.

Run the cells top to bottom. This **retrains and overwrites** `models/clearance/`
and the `clearance` block of `models/registry.json`.
"""),
        code(SETUP),
        md("## 📦 Imports & configuration"),
        code("""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from app.config import settings
from app.engines.predict.clearance import CAT_FEATURES, FEATURES, NUM_FEATURES, QUANTILES
from app.ml import evaluate

TARGET        = "duration_min"
MIN_DURATION  = 1.0
MAX_DURATION  = 2880.0     # 48h cap — drop implausible long-tail / data errors
TEST_FRACTION = 0.20
RANDOM_SEED   = 42
_UNKNOWN      = "unknown"
_MODEL_DIR    = settings.models_dir / "clearance"

CATBOOST_PARAMS = dict(iterations=400, depth=4, learning_rate=0.03,
                       l2_leaf_reg=8, random_seed=RANDOM_SEED, verbose=False)

print("✅ Config loaded")
print(f"   🎯 Target     : {TARGET}")
print(f"   🏷️  Categorical: {list(CAT_FEATURES)}")
print(f"   🔢 Numeric    : {list(NUM_FEATURES)}")
print(f"   📐 Quantiles  : {QUANTILES}")
"""),
        md("## 📥 Step 1 — Load the cleaned events"),
        code("""
from app.ml.pipeline import load_clean

print("📥 Loading cleaned events ...")
df = load_clean()
print(f"✅ Loaded {len(df):,} events  ·  {df.shape[1]} columns")
print(f"   📅 {df['start_datetime'].min():%Y-%m-%d}  →  {df['start_datetime'].max():%Y-%m-%d}")
df.head(3)
"""),
        md("## 🧹 Step 2 — Filter to the trainable range & build features"),
        code("""
print("🧹 Filtering to 1 ≤ duration ≤ 2880 min with a valid start time ...")
before = len(df)
mask = (
    df[TARGET].notna()
    & (df[TARGET] >= MIN_DURATION)
    & (df[TARGET] <= MAX_DURATION)
    & df["start_datetime"].notna()
)
data = df.loc[mask].copy()

for col in CAT_FEATURES:
    data[col] = data[col].astype("string").fillna(_UNKNOWN).replace("", _UNKNOWN).astype(str)
for col in NUM_FEATURES:
    data[col] = data[col].astype("float").fillna(0).astype(int)
data[TARGET] = data[TARGET].astype(float)

print(f"✅ Kept {len(data):,} of {before:,} rows  ({before - len(data):,} dropped)")
print(f"   ⏱️  duration_min →  min={data[TARGET].min():.0f}   "
      f"median={data[TARGET].median():.0f}   max={data[TARGET].max():.0f}")
data[list(FEATURES) + [TARGET]].head(3)
"""),
        md("## ✂️ Step 3 — Chronological 80/20 split (no leakage)"),
        code("""
print("✂️  Sorting by start time and splitting earliest 80% / latest 20% ...")
ordered = data.sort_values("start_datetime", kind="mergesort").reset_index(drop=True)
cut = int(len(ordered) * (1 - TEST_FRACTION))
train_df, test_df = ordered.iloc[:cut], ordered.iloc[cut:]

print(f"   🟦 Train: {len(train_df):>5,} rows  |  "
      f"{train_df['start_datetime'].min():%Y-%m-%d} → {train_df['start_datetime'].max():%Y-%m-%d}")
print(f"   🟧 Test : {len(test_df):>5,} rows  |  "
      f"{test_df['start_datetime'].min():%Y-%m-%d} → {test_df['start_datetime'].max():%Y-%m-%d}")
print(f"   🔒 No leakage: {test_df['start_datetime'].min() >= train_df['start_datetime'].max()}")
"""),
        md("## 🌲 Step 4 — Train the three quantile models"),
        code("""
def make_pool(frame):
    return Pool(frame[list(FEATURES)], label=frame[TARGET], cat_features=list(CAT_FEATURES))

train_pool, test_pool = make_pool(train_df), make_pool(test_df)
y_train, y_test = train_df[TARGET].to_numpy(), test_df[TARGET].to_numpy()

print("🌲 Training CatBoost quantile models ...")
_MODEL_DIR.mkdir(parents=True, exist_ok=True)
preds = {}
for q, alpha in QUANTILES.items():
    print(f"   → {q.upper()} (alpha={alpha}) ...", end=" ")
    model = CatBoostRegressor(loss_function=f"Quantile:alpha={alpha}", **CATBOOST_PARAMS)
    model.fit(train_pool)
    model.save_model(str(_MODEL_DIR / f"{q}.cbm"))
    preds[q] = model.predict(test_pool)
    print("✅")
print("🎉 All three models trained & saved to models/clearance/")
"""),
        md("## 📊 Step 5 — Evaluate (and sanity-check vs a naive baseline)"),
        code("""
# Enforce non-crossing quantiles before scoring.
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

beats = metrics["p50_mae"] < metrics["median_baseline_mae"]
cov_ok = 0.85 <= metrics["p90_coverage"] <= 0.95
print("📊 Held-out test performance")
print(f"   P50 MAE       : {metrics['p50_mae']:.1f} min")
print(f"   P50 RMSE      : {metrics['p50_rmse']:.1f} min")
print(f"   Baseline MAE  : {metrics['median_baseline_mae']:.1f} min  (always predict the median)")
print(f"   {'✅' if beats else '⚠️ '} model {'beats' if beats else 'does NOT beat'} baseline on MAE")
print(f"   P90 coverage  : {metrics['p90_coverage']:.2f}  {'✅ well-calibrated' if cov_ok else '⚠️ out of [0.85, 0.95]'}")
metrics
"""),
        md("## 💾 Step 6 — Persist feature list + registry"),
        code("""
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
registry_path = settings.models_dir / "registry.json"
registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
registry["clearance"] = entry
registry_path.write_text(json.dumps(registry, indent=2))

print("💾 Saved:")
print("   ✅ models/clearance/{p10,p50,p90}.cbm")
print("   ✅ models/clearance/features.json")
print("   ✅ models/registry.json  (clearance block)")
print("\\n🏁 Clearance training complete!")
"""),
    ])


# --------------------------------------------------------------------------- #
# 02 — Triage
# --------------------------------------------------------------------------- #
def triage_nb() -> dict:
    return notebook([
        md("""
# 🗂️ Triage Model — *what is this, and how urgent?*

Free-text incident descriptions are embedded with **LaBSE** (multilingual, so
English *and* Kannada/Hindi share one space), then a **soft-vote ensemble**
(LightGBM + LogisticRegression, both class-weighted) predicts two heads:

* 🏷️ **cause** — 16-class (accident, water_logging, …)
* 🚦 **priority** — binary (High / Low)

> The ensemble averages the two classifiers' probabilities — it beats either
> alone (cause macro-F1 0.481 → 0.494, priority 0.668 → 0.673).

This **retrains and overwrites** `models/triage/`. First run downloads LaBSE
(~1.8 GB) and embeds all rows; later runs reuse the cached embeddings.
"""),
        code(SETUP),
        md("## 📦 Imports & configuration"),
        code("""
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

from app.config import settings
from app.engines.triage.ensemble import SoftVoteEnsemble
from app.features.text import LABSE_MODEL, TextEmbedder, clean_text, detect_lang

TEST_FRACTION = 0.20
RANDOM_SEED   = 42
_MODEL_DIR    = settings.models_dir / "triage"
_CACHE_FILE   = settings.interim_dir / "triage_embeddings.npz"

print("✅ Config loaded")
print(f"   🌐 Embedder: {LABSE_MODEL}")
print(f"   🤖 Heads   : SoftVote(LightGBM + LogReg, 0.5/0.5, class_weight='balanced')")
"""),
        md("## 📥 Step 1 — Rows with usable text + labels"),
        code("""
from app.ml.pipeline import load_clean

print("📥 Loading events and selecting rows with description + labels ...")
df = load_clean().assign(_text=lambda d: d["description"].map(clean_text))
mask = (df["_text"].str.len() > 0) & df["cause_norm"].notna() & df["priority"].notna()
rows = (df.loc[mask, ["id", "_text", "cause_norm", "priority"]]
          .sort_values("id", kind="mergesort").reset_index(drop=True))

print(f"✅ {len(rows):,} usable rows")
print(f"   🏷️  {rows['cause_norm'].nunique()} cause classes  ·  🚦 priority split:")
print(rows["priority"].value_counts().to_string())
rows.head(3)
"""),
        md("## 🌐 Step 2 — Embed descriptions with LaBSE (cached)"),
        code("""
ids = rows["id"].to_numpy()
emb = None
if _CACHE_FILE.exists():
    cached = np.load(_CACHE_FILE, allow_pickle=True)
    if np.array_equal(cached["ids"], ids):
        emb = cached["emb"].astype(np.float32)
        print(f"♻️  Reusing cached embeddings  ({_CACHE_FILE.name})")

if emb is None:
    print("🌐 Encoding with LaBSE (first run downloads the model) ...")
    embedder = TextEmbedder(LABSE_MODEL); embedder.load()
    emb = embedder.encode(rows["_text"].tolist())
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    np.savez(_CACHE_FILE, ids=ids, emb=emb)
    print("💾 Cached embeddings for next time")

print(f"✅ Embedding matrix: {emb.shape[0]:,} × {emb.shape[1]}")
"""),
        md("## 🔀 Step 3 — Encode labels & stratified split"),
        code("""
cause_le    = LabelEncoder().fit(rows["cause_norm"])
priority_le = LabelEncoder().fit(rows["priority"])
y_cause     = cause_le.transform(rows["cause_norm"])
y_priority  = priority_le.transform(rows["priority"])
is_indic    = rows["_text"].map(lambda t: detect_lang(t) == "indic").to_numpy()

train_idx, test_idx = train_test_split(
    np.arange(len(rows)), test_size=TEST_FRACTION, random_state=RANDOM_SEED, stratify=y_cause)

print("🔀 Stratified 80/20 split")
print(f"   🟦 train: {len(train_idx):,}   🟧 test: {len(test_idx):,}")
print(f"   🌏 Indic (Kannada/Hindi) rows in test: {int(is_indic[test_idx].sum())}")
print(f"   🏷️  classes: {list(cause_le.classes_)}")
"""),
        md("## 🤖 Step 4 — Train the soft-vote ensemble heads"),
        code("""
def fit_head(x, y):
    \"\"\"Fit LightGBM + LogReg and average their probabilities (50/50).\"\"\"
    lgb = LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                         class_weight="balanced", random_state=RANDOM_SEED,
                         n_jobs=-1, verbose=-1).fit(x, y)
    lr = LogisticRegression(max_iter=2000, class_weight="balanced",
                            C=1.0, random_state=RANDOM_SEED).fit(x, y)
    return SoftVoteEnsemble([lgb, lr], weights=[0.5, 0.5])

print("🤖 Training soft-vote ensemble heads (LightGBM + LogReg) ...")
print("   → cause head (16-class) ...", end=" ")
cause_head = fit_head(emb[train_idx], y_cause[train_idx]); print("✅")
print("   → priority head (binary) ...", end=" ")
priority_head = fit_head(emb[train_idx], y_priority[train_idx]); print("✅")
print("🎉 Both ensemble heads trained")
"""),
        md("## 📊 Step 5 — Evaluate with macro-F1 (overall + Indic subset)"),
        code("""
def macro_f1(yt, yp):
    return round(float(f1_score(yt, yp, average="macro", zero_division=0)), 4)

cause_pred    = cause_head.predict(emb[test_idx])
priority_pred = priority_head.predict(emb[test_idx])
yt_c, yt_p    = y_cause[test_idx], y_priority[test_idx]
it            = is_indic[test_idx]

metrics = {
    "cause_macro_f1": macro_f1(yt_c, cause_pred),
    "cause_accuracy": round(float(accuracy_score(yt_c, cause_pred)), 4),
    "priority_macro_f1": macro_f1(yt_p, priority_pred),
    "priority_accuracy": round(float(accuracy_score(yt_p, priority_pred)), 4),
    "test_n": int(len(test_idx)),
    "indic_test_n": int(it.sum()),
}
if it.any():
    metrics["cause_macro_f1_indic"] = macro_f1(yt_c[it], cause_pred[it])
    metrics["priority_macro_f1_indic"] = macro_f1(yt_p[it], priority_pred[it])

print("📊 Held-out performance (macro-F1 is the honest metric under imbalance)")
print(f"   🏷️  cause    macro-F1 {metrics['cause_macro_f1']:.3f}  ·  acc {metrics['cause_accuracy']:.3f}")
print(f"   🚦 priority macro-F1 {metrics['priority_macro_f1']:.3f}  ·  acc {metrics['priority_accuracy']:.3f}")
print(f"   🌏 Indic   cause {metrics.get('cause_macro_f1_indic','-')}  ·  "
      f"priority {metrics.get('priority_macro_f1_indic','-')}")
metrics
"""),
        md("## 💾 Step 6 — Persist heads, encoders & registry"),
        code("""
_MODEL_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(cause_head, _MODEL_DIR / "cause_head.joblib")
joblib.dump(priority_head, _MODEL_DIR / "priority_head.joblib")
joblib.dump({"cause": cause_le, "priority": priority_le}, _MODEL_DIR / "label_encoders.joblib")

entry = {
    "model": "triage",
    "trained_at": datetime.now(timezone.utc).isoformat(),
    "embedder": LABSE_MODEL,
    "embedding_dim": int(emb.shape[1]),
    "head_estimator": "SoftVote(LGBM+LogReg, 0.5/0.5, class_weight=balanced)",
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
registry_path = settings.models_dir / "registry.json"
registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
registry["triage"] = entry
registry_path.write_text(json.dumps(registry, indent=2))

print("💾 Saved heads + encoders + registry")
print("🏁 Triage training complete!")
"""),
    ])


# --------------------------------------------------------------------------- #
# 03 — Foresee
# --------------------------------------------------------------------------- #
def foresee_nb() -> dict:
    return notebook([
        md("""
# 🔮 Foresee Model — *where will incidents happen next?*

Events are aggregated to **(corridor, hour, day-of-week)** cells, then a
**Poisson `HistGradientBoostingRegressor`** forecasts the expected count per cell.
Quality is **precision@k**: of the top-k predicted hotspots, how many actually saw
an incident in the held-out tail.

This **retrains and overwrites** `models/foresee/`.
"""),
        code(SETUP),
        md("## 📦 Imports & configuration"),
        code("""
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from app.config import settings
from app.engines.foresee.hotspot import CATEGORICAL, make_features

TEST_FRACTION = 0.20
RANDOM_SEED   = 42
PRECISION_KS  = (10, 20, 50)
IGNORED       = frozenset({"non-corridor", "unknown", "none", ""})
_MODEL_DIR    = settings.models_dir / "foresee"

print("✅ Config loaded  ·  🗺️  categorical features:", CATEGORICAL)
"""),
        md("## 📥 Step 1 — Keep rows with a real corridor + temporal features"),
        code("""
from app.ml.pipeline import load_clean

print("📥 Loading events and filtering to mapped corridors ...")
df = load_clean()
corridor = df["corridor"].astype("string")
mask = (
    df["start_datetime"].notna() & df["hour_ist"].notna() & df["dow"].notna()
    & corridor.notna() & ~corridor.str.strip().str.lower().isin(IGNORED)
)
data = df.loc[mask].copy().sort_values("start_datetime", kind="mergesort")
corridors = sorted(data["corridor"].astype(str).unique())
encoder = {c: i for i, c in enumerate(corridors)}

print(f"✅ {len(data):,} events across {len(corridors)} corridors")
print("   🛣️ ", ", ".join(corridors[:6]), "…")
"""),
        md("## ✂️ Step 2 — Time split & aggregate to (corridor, hour, dow) cells"),
        code("""
cut = int(len(data) * (1 - TEST_FRACTION))
train_df, test_df = data.iloc[:cut], data.iloc[cut:]

def aggregate(frame):
    agg = (frame.groupby(["corridor", "hour_ist", "dow"], observed=True)
                .size().reset_index(name="count"))
    feats = make_features([encoder[c] for c in agg["corridor"]],
                          agg["hour_ist"].astype(int).tolist(),
                          agg["dow"].astype(int).tolist())
    return feats, agg["count"].to_numpy(dtype=float)

x_train, y_train = aggregate(train_df)
print(f"✂️  Train cells: {len(y_train):,}   ·   busiest cell saw {int(y_train.max())} incidents")
x_train.head(3)
"""),
        md("## 🌲 Step 3 — Fit the Poisson gradient-boosting forecaster"),
        code("""
print("🌲 Training HistGradientBoostingRegressor (Poisson loss) ...")
# Tuned config (see _tune_foresee.py): lifts precision@10/20/50 0.80/0.75/0.74 → 0.90/0.80/0.76
model = HistGradientBoostingRegressor(
    loss="poisson", categorical_features=CATEGORICAL,
    max_iter=500, learning_rate=0.03, max_depth=5,
    l2_regularization=2.0, min_samples_leaf=30, random_state=RANDOM_SEED,
)
model.fit(x_train, y_train)
print(f"✅ Trained on {len(y_train):,} corridor·hour·dow cells")
"""),
        md("## 📊 Step 4 — Rank the full grid & score precision@k"),
        code("""
grid = [(c, h, d) for c in corridors for h in range(24) for d in range(7)]
gp = model.predict(make_features([encoder[c] for c, _, _ in grid],
                                 [h for _, h, _ in grid], [d for _, _, d in grid]))
pred_rank = [k for _, k in sorted(zip(gp, grid), key=lambda t: t[0], reverse=True)]

test_agg = (test_df.groupby(["corridor", "hour_ist", "dow"], observed=True)
                   .size().reset_index(name="count"))
relevant = {(str(r.corridor), int(r.hour_ist), int(r.dow)) for r in test_agg.itertuples()}

metrics = {f"precision_at_{k}": round(len(set(pred_rank[:k]) & relevant) / k, 4) for k in PRECISION_KS}
metrics["test_cells"] = int(len(test_agg))

print("📊 Hotspot ranking quality")
for k in PRECISION_KS:
    bar = "█" * int(metrics[f'precision_at_{k}'] * 20)
    print(f"   precision@{k:<2}: {metrics[f'precision_at_{k}']:.2f}  {bar}")
metrics
"""),
        md("## 💾 Step 5 — Centroids, artifacts & registry"),
        code("""
cent = (data[(data["latitude"].notna()) & (data["latitude"] != 0)]
        .groupby("corridor", observed=True)[["latitude", "longitude"]].mean())
centroids = {c: [round(float(r.latitude), 6), round(float(r.longitude), 6)] for c, r in cent.iterrows()}

_MODEL_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(model, _MODEL_DIR / "forecaster.joblib")
(_MODEL_DIR / "corridor_encoder.json").write_text(json.dumps(encoder, indent=2))
(_MODEL_DIR / "centroids.json").write_text(json.dumps(centroids, indent=2))

entry = {
    "model": "foresee",
    "trained_at": datetime.now(timezone.utc).isoformat(),
    "estimator": "HistGradientBoostingRegressor(loss=poisson)",
    "target": "incident_count_per_cell",
    "split": {"type": "time-based", "test_fraction": TEST_FRACTION},
    "n_corridors": len(corridors),
    "n_train_cells": int(len(y_train)),
    "metrics": metrics,
    "artifacts": {
        "forecaster": "foresee/forecaster.joblib",
        "corridor_encoder": "foresee/corridor_encoder.json",
        "centroids": "foresee/centroids.json",
    },
}
registry_path = settings.models_dir / "registry.json"
registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
registry["foresee"] = entry
registry_path.write_text(json.dumps(registry, indent=2))

print(f"💾 Saved forecaster + {len(centroids)} corridor centroids + registry")
print("🏁 Foresee training complete!")
"""),
    ])


def main() -> None:
    for name, nb in {
        "01_clearance.ipynb": clearance_nb(),
        "02_triage.ipynb": triage_nb(),
        "03_foresee.ipynb": foresee_nb(),
    }.items():
        (OUT_DIR / name).write_text(json.dumps(nb, indent=1), encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
