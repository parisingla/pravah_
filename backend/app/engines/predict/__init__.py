"""Predict engine — clearance time, severity, ripple, and SHAP explanations.

Public surface:
- ``get_models()`` / ``ClearanceModels`` — p10/p50/p90 quantile model singleton.
- ``build_features`` — shared train/serve feature builder.
- ``compute_severity`` — p50 + closure + corridor volume -> severity + PSI.
- ``estimate_ripple`` — p50 -> spillback footprint.
- ``explain_p50`` — SHAP contributions for a prediction.
"""
from app.engines.predict.clearance import (
    ClearanceModels,
    build_features,
    get_models,
)
from app.engines.predict.explain import explain_p50
from app.engines.predict.ripple import RippleResult, estimate_ripple
from app.engines.predict.severity import SeverityResult, compute_severity

__all__ = [
    "ClearanceModels",
    "get_models",
    "build_features",
    "compute_severity",
    "SeverityResult",
    "estimate_ripple",
    "RippleResult",
    "explain_p50",
]
