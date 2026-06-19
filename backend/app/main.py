"""FastAPI application factory.

Part 5 completes the engine set. All model engines (clearance, triage + LaBSE,
foresee) are loaded fail-fast on startup; spatial caches are warmed; the
Foresee / Respond / analytics / SSE routers are mounted; and the optional
background scheduler (nightly retrain + hourly hotspots) is started.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import analytics, events, foresee, predict, respond, stream, triage
from app.config import settings
from app.core.database import SessionLocal, init_db
from app.core.logging import get_logger
from app.engines.foresee import get_model as get_foresee_model
from app.engines.predict import get_models
from app.engines.triage import get_model as get_triage_model
from app.features.spatial import corridor_centroids, criticality_map
from app.learning.scheduler import shutdown_scheduler, start_scheduler

logger = get_logger("pravah.main")


def models_loaded() -> bool:
    """True only when every startup model engine is loaded."""
    return get_models().loaded and get_triage_model().loaded and get_foresee_model().loaded


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure tables exist, load ML models (fail-fast), warm caches, start jobs."""
    logger.info("PRAVAH starting up - timezone=%s", settings.TIMEZONE)
    init_db()
    # Fail fast if any model artifacts are missing — run `python -m app.ml.train_all`.
    get_models().load()         # clearance
    get_triage_model().load()   # triage + LaBSE
    get_foresee_model().load()  # foresee forecaster + centroids

    # Warm spatial caches (corridor centroids + criticality) once.
    with SessionLocal() as db:
        corridor_centroids(db)
        criticality_map(db)

    start_scheduler()
    yield
    shutdown_scheduler()
    logger.info("PRAVAH shutting down")


app = FastAPI(
    title="PRAVAH API",
    version=__version__,
    description="Traffic incident intelligence backend (Predict · Triage · Foresee · Respond).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, object]:
    """Liveness probe (no auth). `models_loaded` reflects all model engines."""
    return {
        "status": "ok",
        "models_loaded": models_loaded(),
        "version": __version__,
        "timezone": settings.TIMEZONE,
    }


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"name": "PRAVAH", "docs": "/docs", "health": "/health"}


# API routers, auth-guarded under /api.
app.include_router(events.router)
app.include_router(predict.router)
app.include_router(triage.router)
app.include_router(foresee.router)    # /predictions/corridors, /hotspots, /alerts
app.include_router(respond.router)    # /simulate
app.include_router(analytics.router)  # /analytics
app.include_router(stream.router)     # /stream (SSE)
