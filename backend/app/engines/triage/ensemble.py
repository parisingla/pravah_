"""Soft-vote ensemble head for the Triage engine.

Probability-averaged ensemble of fitted classifiers that share the same encoded
``classes_`` (e.g. LightGBM + LogisticRegression over LaBSE embeddings). It
exposes ``predict_proba`` / ``predict`` so it is a drop-in for a single sklearn
head — the serving code (``triage/model.py``) needs no changes.

Averaging the two heads' probabilities beats either alone on this data
(cause macro-F1 0.481 -> 0.494, priority 0.668 -> 0.673).
"""
from __future__ import annotations

from typing import Any

import numpy as np


class SoftVoteEnsemble:
    """Weighted probability average over fitted classifiers with identical classes_."""

    def __init__(self, estimators: list[Any], weights: list[float] | None = None) -> None:
        if not estimators:
            raise ValueError("SoftVoteEnsemble needs at least one estimator.")
        self.estimators = estimators
        n = len(estimators)
        self.weights = weights if weights is not None else [1.0 / n] * n
        if len(self.weights) != n:
            raise ValueError("weights length must match estimators length.")
        # All estimators are trained on the same LabelEncoder output, so classes_
        # match; take the first as the reference ordering.
        self.classes_ = estimators[0].classes_

    def predict_proba(self, X: Any) -> np.ndarray:
        total = sum(w for w in self.weights)
        proba = np.zeros((np.asarray(X).shape[0], len(self.classes_)), dtype=float)
        for w, est in zip(self.weights, self.estimators):
            proba += w * est.predict_proba(X)
        return proba / total

    def predict(self, X: Any) -> np.ndarray:
        return self.classes_[self.predict_proba(X).argmax(axis=1)]
