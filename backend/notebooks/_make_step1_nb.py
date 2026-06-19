"""Build 04_triage_audit.ipynb (STEP 1) — runnable cell by cell with the kernel."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "04_triage_audit.ipynb"


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": _l(t)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _l(t)}


def _l(t):
    t = t.strip("\n")
    ls = t.splitlines()
    return [x + "\n" for x in ls[:-1]] + [ls[-1]] if ls else [""]


cells = [
    md("""
# 04 — STEP 1: Triage audit & fix

Audits the cause + priority heads and shows the class-weight / **LightGBM** decision
with real numbers. Mirrors `notebooks/_step1_triage_audit.py`. Uses the cached
LaBSE embeddings (`data/interim/triage_embeddings.npz`) so it runs in seconds.

**Outcome already applied to production:** `train_triage.py` now uses a
`LGBMClassifier(class_weight="balanced")` head (cause macro-F1 0.38 → 0.48,
priority 0.63 → 0.67). Re-run this notebook to reproduce the comparison.
"""),
    code("""
# --- Setup: cd to backend/ root ---
import os, sys
from pathlib import Path
root = Path.cwd()
while not (root / "app").is_dir() and root != root.parent:
    root = root.parent
os.chdir(root); sys.path.insert(0, str(root))

import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from app.features.text import LABSE_MODEL, TextEmbedder, clean_text, detect_lang
from app.ml.pipeline import load_clean

RANDOM_SEED, TEST_FRACTION = 42, 0.20
CACHE = Path("data/interim/triage_embeddings.npz")
"""),
    md("### Load rows + cached LaBSE embeddings, encode labels, stratified split"),
    code("""
df = load_clean().assign(_text=lambda d: d["description"].map(clean_text))
mask = (df["_text"].str.len() > 0) & df["cause_norm"].notna() & df["priority"].notna()
rows = (df.loc[mask, ["id", "_text", "cause_norm", "priority"]]
          .sort_values("id", kind="mergesort").reset_index(drop=True))
ids = rows["id"].to_numpy()

cached = np.load(CACHE, allow_pickle=True) if CACHE.exists() else None
if cached is not None and np.array_equal(cached["ids"], ids):
    emb = cached["emb"].astype(np.float32)
else:
    e = TextEmbedder(LABSE_MODEL); e.load()
    emb = e.encode(rows["_text"].tolist()); np.savez(CACHE, ids=ids, emb=emb)

cause_le = LabelEncoder().fit(rows["cause_norm"]); priority_le = LabelEncoder().fit(rows["priority"])
y_cause = cause_le.transform(rows["cause_norm"]); y_priority = priority_le.transform(rows["priority"])
is_indic = rows["_text"].map(lambda t: detect_lang(t) == "indic").to_numpy()
train_idx, test_idx = train_test_split(np.arange(len(rows)), test_size=TEST_FRACTION,
                                       random_state=RANDOM_SEED, stratify=y_cause)
print("emb", emb.shape, "| train", len(train_idx), "| test", len(test_idx))
"""),
    md("### 1.1 — Priority class distribution (train)"),
    code("""
tp = pd.Series(priority_le.inverse_transform(y_priority[train_idx]))
d = tp.value_counts(); pd.DataFrame({"count": d, "pct": (d/d.sum()*100).round(1)})
"""),
    md("### 1.3 — Is the head class-weighted? Train BEFORE (none) vs AFTER (balanced)"),
    code("""
import inspect
from app.ml import train_triage
print("current _fit_head class_weight='balanced':",
      "class_weight=\\"balanced\\"" in inspect.getsource(train_triage._fit_head))

def fit(x, y, **kw):
    return LogisticRegression(max_iter=2000, C=1.0, random_state=RANDOM_SEED, **kw).fit(x, y)
def mf1(yt, yp):
    return round(float(f1_score(yt, yp, average="macro", zero_division=0)), 4)

prio_b = fit(emb[train_idx], y_priority[train_idx])
prio_a = fit(emb[train_idx], y_priority[train_idx], class_weight="balanced")
cause_b = fit(emb[train_idx], y_cause[train_idx])
cause_a = fit(emb[train_idx], y_cause[train_idx], class_weight="balanced")
pb, pa = prio_b.predict(emb[test_idx]), prio_a.predict(emb[test_idx])
cb, ca = cause_b.predict(emb[test_idx]), cause_a.predict(emb[test_idx])
yt_p, yt_c = y_priority[test_idx], y_cause[test_idx]
"""),
    md("### 1.2 — Priority confusion matrix (test, balanced head)"),
    code("""
cm = confusion_matrix(yt_p, pa, labels=list(range(len(priority_le.classes_))))
pd.DataFrame(cm, index=[f"true_{c}" for c in priority_le.classes_],
             columns=[f"pred_{c}" for c in priority_le.classes_])
"""),
    md("### 1.4 — Macro-F1 (and accuracy) BEFORE vs AFTER class weights"),
    code("""
pd.DataFrame({
    "macro_f1_before": [mf1(yt_c, cb), mf1(yt_p, pb)],
    "macro_f1_after":  [mf1(yt_c, ca), mf1(yt_p, pa)],
    "acc_before": [round(accuracy_score(yt_c, cb), 4), round(accuracy_score(yt_p, pb), 4)],
    "acc_after":  [round(accuracy_score(yt_c, ca), 4), round(accuracy_score(yt_p, pa), 4)],
}, index=["cause (16-class)", "priority (binary)"])
"""),
    md("> Note: balancing **helps priority** but **hurts cause** — which is why class weights alone aren't the answer."),
    md("### 1.5 — Indic subset (Kannada/Hindi) macro-F1"),
    code("""
it = is_indic[test_idx]
print("Indic rows in test:", int(it.sum()), "/", len(test_idx))
pd.DataFrame({
    "macro_f1_all":   [mf1(yt_c, ca), mf1(yt_p, pa)],
    "macro_f1_indic": [mf1(yt_c[it], ca[it]), mf1(yt_p[it], pa[it])],
}, index=["cause", "priority"])
"""),
    md("### 1.6 — LightGBM vs LogReg (both balanced) on the same embeddings"),
    code("""
from lightgbm import LGBMClassifier
def lgb(y):
    return LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                          class_weight="balanced", random_state=RANDOM_SEED,
                          n_jobs=-1, verbose=-1).fit(emb[train_idx], y)
lp = lgb(y_priority[train_idx]).predict(emb[test_idx])
lc = lgb(y_cause[train_idx]).predict(emb[test_idx])
pd.DataFrame({
    "logreg_balanced":  [mf1(yt_c, ca), mf1(yt_p, pa)],
    "lightgbm_balanced": [mf1(yt_c, lc), mf1(yt_p, lp)],
}, index=["cause", "priority"])
"""),
    md("""
### Conclusion (applied to production)

| head | before (LogReg balanced) | after (LightGBM balanced) |
|------|--------------------------|---------------------------|
| cause macro-F1    | 0.383 | **0.481** |
| priority macro-F1 | 0.631 | **0.668** |

`app/ml/train_triage.py` now fits `LGBMClassifier(class_weight="balanced")` and the
serving path (`app/engines/triage/model.py`) is unchanged (LightGBM is a drop-in
for `predict`/`predict_proba`). Re-run training with:

```
python run_training.py triage      # or: python -m app.ml.train_triage
python run_training.py report      # macro-F1 + Indic breakout
```
"""),
]

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3 (.venv)", "language": "python", "name": "python3"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
OUT.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", OUT)
