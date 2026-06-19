"""Evaluation metric functions for the clearance quantile models.

Pure numpy, no I/O — imported by the trainer and reusable in tests. All inputs
are 1-D array-likes of equal length (minutes).
"""
from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def _arr(x: ArrayLike) -> np.ndarray:
    return np.asarray(x, dtype=float)


def mae(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Mean absolute error."""
    return float(np.mean(np.abs(_arr(y_true) - _arr(y_pred))))


def rmse(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Root mean squared error."""
    return float(np.sqrt(np.mean((_arr(y_true) - _arr(y_pred)) ** 2)))


def pinball_loss(y_true: ArrayLike, y_pred: ArrayLike, alpha: float) -> float:
    """Quantile (pinball) loss at quantile ``alpha`` (lower is better)."""
    y, p = _arr(y_true), _arr(y_pred)
    diff = y - p
    return float(np.mean(np.maximum(alpha * diff, (alpha - 1.0) * diff)))


def coverage(y_true: ArrayLike, y_upper: ArrayLike) -> float:
    """Fraction of actuals at/below the upper-quantile prediction.

    For the P90 model this should land near 0.90 — the share of events that
    actually clear within the predicted P90 time.
    """
    return float(np.mean(_arr(y_true) <= _arr(y_upper)))


def median_baseline_mae(y_train: ArrayLike, y_test: ArrayLike) -> float:
    """MAE of a constant predictor that always returns the train median."""
    baseline = float(np.median(_arr(y_train)))
    return mae(y_test, np.full(len(_arr(y_test)), baseline))
