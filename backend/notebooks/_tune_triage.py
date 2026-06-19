"""Tune the triage heads with CROSS-VALIDATION (no test-set peeking for selection).

3-fold stratified CV on the train split picks the config by macro-F1; the held-out
test set is scored ONCE at the end for each candidate so we can see the honest gain.
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
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder

from app.features.text import clean_text, detect_lang
from app.ml.pipeline import load_clean

SEED, TEST_FRACTION = 42, 0.20
CACHE = Path("data/interim/triage_embeddings.npz")


def line(t): print("\n" + "=" * 76 + f"\n{t}\n" + "=" * 76)


# Load rows + cached embeddings
df = load_clean().assign(_text=lambda d: d["description"].map(clean_text))
m = (df["_text"].str.len() > 0) & df["cause_norm"].notna() & df["priority"].notna()
rows = df.loc[m, ["id", "_text", "cause_norm", "priority"]].sort_values("id", kind="mergesort").reset_index(drop=True)
ids = rows["id"].to_numpy()
cached = np.load(CACHE, allow_pickle=True)
assert np.array_equal(cached["ids"], ids), "cache mismatch — run training once first"
emb = cached["emb"].astype(np.float32)

y_cause = LabelEncoder().fit_transform(rows["cause_norm"])
y_prio = LabelEncoder().fit_transform(rows["priority"])
is_indic = rows["_text"].map(lambda t: detect_lang(t) == "indic").to_numpy()
tr, te = train_test_split(np.arange(len(rows)), test_size=TEST_FRACTION, random_state=SEED, stratify=y_cause)


def mf1(yt, yp): return f1_score(yt, yp, average="macro", zero_division=0)


def cv_macro_f1(make, X, y, folds=3):
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=SEED)
    scores = []
    for a, b in skf.split(X, y):
        clf = make().fit(X[a], y[a])
        scores.append(mf1(y[b], clf.predict(X[b])))
    return float(np.mean(scores))


# Candidate factories
def lgb(**kw):
    base = dict(class_weight="balanced", random_state=SEED, n_jobs=-1, verbose=-1)
    return lambda: LGBMClassifier(**{**base, **kw})


def logreg(**kw):
    return lambda: LogisticRegression(max_iter=3000, class_weight="balanced", random_state=SEED, **kw)


CANDIDATES = {
    "CURRENT lgb(400,0.05,31)": lgb(n_estimators=400, learning_rate=0.05, num_leaves=31),
    "lgb(300,0.06,31,mcs50,reg1)": lgb(n_estimators=300, learning_rate=0.06, num_leaves=31,
                                       min_child_samples=50, reg_lambda=1.0),
    "logreg(C=3)": logreg(C=3.0),
    "logreg(C=8)": logreg(C=8.0),
    "SVC-linear(C=1)": (lambda: __import__("sklearn.svm", fromlist=["LinearSVC"]).LinearSVC(
        class_weight="balanced", C=1.0, random_state=SEED, max_iter=5000)),
}

for head_name, y in [("CAUSE (16-class)", y_cause), ("PRIORITY (binary)", y_prio)]:
    line(f"{head_name} — 3-fold CV macro-F1 on train, then held-out test")
    results = []
    for name, make in CANDIDATES.items():
        cv = cv_macro_f1(make, emb[tr], y[tr])
        test = mf1(y[te], make().fit(emb[tr], y[tr]).predict(emb[te]))
        results.append((name, cv, test))
        print(f"   {name:34} CV={cv:.4f}   test={test:.4f}", flush=True)
    best = max(results, key=lambda r: r[1])
    cur = next(r for r in results if r[0].startswith("CURRENT"))
    print(f"\n   ⭐ best by CV: {best[0]}  (CV {best[1]:.4f}, test {best[2]:.4f})")
    print(f"   📍 current   : CV {cur[1]:.4f}, test {cur[2]:.4f}   ->  "
          f"Δtest {best[2]-cur[2]:+.4f}")

line("DONE")
