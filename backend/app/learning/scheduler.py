"""Background scheduler — nightly retrain + hourly hotspot precompute.

Disabled by default (``SCHEDULER_ENABLED=false``); started from the app lifespan
when enabled. Jobs are best-effort and never crash the app.
"""
from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("pravah.learning.scheduler")

_scheduler: BackgroundScheduler | None = None


def _nightly_retrain() -> None:
    """Re-run the full training pipeline and refresh model singletons."""
    try:
        from app.ml.train_all import train_all

        logger.info("Scheduler: starting nightly train_all ...")
        train_all()
        # Reload model singletons so the running app serves fresh models.
        from app.engines.foresee import get_model as foresee_model
        from app.engines.predict import get_models as clearance_models
        from app.engines.triage import get_model as triage_model

        clearance_models().load()
        triage_model().load()
        foresee_model().load()
        logger.info("Scheduler: nightly train_all complete; models reloaded.")
    except Exception:  # pragma: no cover - background best-effort
        logger.exception("Scheduler: nightly train_all failed")


def _hourly_hotspots() -> None:
    """Warm the hotspot cache for all horizons."""
    try:
        from app.services.foresee import precompute_hotspots

        precompute_hotspots()
        logger.info("Scheduler: hourly hotspot precompute complete.")
    except Exception:  # pragma: no cover - background best-effort
        logger.exception("Scheduler: hourly hotspot precompute failed")


def start_scheduler() -> BackgroundScheduler | None:
    """Start the scheduler if enabled in settings (idempotent)."""
    global _scheduler
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler disabled (SCHEDULER_ENABLED=false).")
        return None
    if _scheduler is not None:
        return _scheduler

    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
    scheduler.add_job(_nightly_retrain, "cron", hour=2, minute=0, id="nightly_retrain")
    scheduler.add_job(_hourly_hotspots, "interval", hours=1, id="hourly_hotspots")
    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduler started: nightly retrain (02:00 IST) + hourly hotspots.")
    return scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped.")
