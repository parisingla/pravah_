"""Train everything: pipeline -> clearance -> triage -> foresee.

Refreshes the cleaned parquet, trains all three model engines (each writes its
own section of models/registry.json), and stamps a top-level ``trained_at``.

Run:  python -m app.ml.train_all
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app.config import settings
from app.core.logging import get_logger
from app.ml import train_clearance, train_foresee, train_triage
from app.ml.pipeline import run_pipeline

logger = get_logger("pravah.train.all")


def train_all() -> dict:
    """Run the full training pipeline and return all registry metrics."""
    started = datetime.now()
    logger.info("train_all: refreshing cleaned dataset ...")
    run_pipeline()

    logger.info("train_all: training clearance ...")
    clearance = train_clearance.train()
    logger.info("train_all: training triage ...")
    triage = train_triage.train()
    logger.info("train_all: training foresee ...")
    foresee = train_foresee.train()

    # Stamp a top-level trained_at on the merged registry.
    registry_path = settings.models_dir / "registry.json"
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
    registry["trained_at"] = datetime.now(timezone.utc).isoformat()
    registry_path.write_text(json.dumps(registry, indent=2))

    elapsed = (datetime.now() - started).total_seconds()
    logger.info("train_all complete in %.1fs", elapsed)
    return {
        "clearance": clearance["metrics"],
        "triage": triage["metrics"],
        "foresee": foresee["metrics"],
        "elapsed_s": round(elapsed, 1),
    }


if __name__ == "__main__":
    result = train_all()
    print(json.dumps(result, indent=2))
