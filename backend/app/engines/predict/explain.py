"""SHAP explanations for clearance predictions (Predict engine).

Uses CatBoost's native SHAP (``get_feature_importance(type="ShapValues")``) on
the p50 model — exact tree SHAP, fast on CPU, no extra explainer to fit. Returns
the feature contributions (minutes added/removed vs. the base value) sorted by
magnitude.
"""
from __future__ import annotations

from typing import Any

from catboost import EFstrType

from app.engines.predict.clearance import ClearanceModels


def explain_p50(
    models: ClearanceModels,
    features: dict[str, Any],
    top_k: int = 6,
) -> list[dict[str, float]]:
    """Return ``[{feature, value}]`` SHAP contributions for the p50 model.

    `value` is the signed contribution in minutes; the last SHAP column (base
    value) is dropped. Sorted by absolute contribution, truncated to `top_k`.
    """
    if not models.loaded:
        raise RuntimeError("Clearance models not loaded.")

    from app.engines.predict.clearance import to_frame  # local import: avoid cycle at import time

    pool = models._pool(to_frame([features]))
    shap_values = models.model("p50").get_feature_importance(pool, type=EFstrType.ShapValues)
    row = shap_values[0]  # (n_features + 1,) — trailing entry is the base value
    contributions = [
        {"feature": name, "value": round(float(val), 2)}
        for name, val in zip(models.features, row[:-1])
    ]
    contributions.sort(key=lambda item: abs(item["value"]), reverse=True)
    return contributions[:top_k]
