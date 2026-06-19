"""Dev entrypoint: `python run.py` launches the PRAVAH API on localhost.

Serves the DB-only events/summary API plus /health at http://127.0.0.1:8000
(see /docs). Run `python -m app.db.seed` first to populate the database.
"""
from __future__ import annotations

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
