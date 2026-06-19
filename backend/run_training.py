"""PRAVAH runner — do each step yourself, one command at a time.

A single entrypoint so you don't have to remember every `python -m app...` path.
Run from the backend/ folder with the venv active.

Examples
--------
    python run_training.py db-check     # test the Supabase connection
    python run_training.py db-init      # create tables in Supabase
    python run_training.py seed         # clean CSV -> load events into Supabase
    python run_training.py pipeline     # rebuild the cleaned parquet only
    python run_training.py clearance    # train just the clearance model
    python run_training.py triage       # train just the triage model
    python run_training.py foresee      # train just the foresee model
    python run_training.py all          # pipeline + all three models
    python run_training.py report       # print the accuracy report

Run without arguments to see this list.
"""
from __future__ import annotations

import argparse
import json
import sys


def _print_metrics(title: str, metrics: dict) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(metrics, indent=2))


def db_check() -> None:
    """Open one connection and run SELECT 1 against the configured database."""
    from sqlalchemy import text

    from app.config import settings
    from app.core.database import engine

    # Mask the password before printing the URL.
    url = settings.sqlalchemy_database_url
    safe = url
    if "@" in url and "://" in url:
        head, tail = url.split("://", 1)
        creds, host = tail.split("@", 1)
        if ":" in creds:
            user = creds.split(":", 1)[0]
            safe = f"{head}://{user}:****@{host}"
    print("DATABASE_URL:", safe)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("OK — connection succeeded.")


def db_init() -> None:
    """Create all tables (idempotent)."""
    from app.core.database import init_db

    init_db()
    print("OK — tables created (or already present).")


def seed() -> None:
    """Run the pipeline and (re)load all events into the database."""
    from app.db.seed import seed as _seed

    total = _seed()
    print(f"OK — {total} events in the database.")


def pipeline() -> None:
    """Rebuild the cleaned parquet from the raw CSV."""
    from app.ml.pipeline import run_pipeline

    df = run_pipeline()
    print(f"OK — cleaned {len(df)} rows -> data/interim/events_clean.parquet")


def clearance() -> None:
    from app.ml import train_clearance

    _print_metrics("clearance", train_clearance.train()["metrics"])


def triage() -> None:
    from app.ml import train_triage

    _print_metrics("triage", train_triage.train()["metrics"])


def foresee() -> None:
    from app.ml import train_foresee

    _print_metrics("foresee", train_foresee.train()["metrics"])


def train_all() -> None:
    from app.ml.train_all import train_all as _all

    _print_metrics("all", _all())


def report() -> None:
    from app.ml.accuracy_report import main as _report

    _report()


COMMANDS = {
    "db-check": db_check,
    "db-init": db_init,
    "seed": seed,
    "pipeline": pipeline,
    "clearance": clearance,
    "triage": triage,
    "foresee": foresee,
    "all": train_all,
    "report": report,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="run_training.py",
        description="Run any PRAVAH step on its own.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", choices=list(COMMANDS), help="step to run")
    args = parser.parse_args()
    COMMANDS[args.command]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
