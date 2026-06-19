# PRAVAH — Backend

Traffic incident intelligence backend. **FastAPI · SQLite · CPU-only · localhost (no Docker).**
Python 3.11+, pydantic v2, type-hinted. All timestamps are stored in **IST (Asia/Kolkata)**.

Four engines (built across 5 parts): **Predict** (clearance time) · **Triage** (prioritisation) ·
**Foresee** (forecasting) · **Respond** (dispatch/routing).

> **Part 1 (this milestone):** project scaffold + database + data pipeline.
> No engine endpoints or ML models yet — those arrive in Parts 2–5.

## Project layout

```
backend/
  app/
    main.py            FastAPI app (health/meta routes only in Part 1)
    config.py          Settings (.env via pydantic-settings)
    deps.py            Shared FastAPI dependencies
    core/              database, security, logging
    db/                models.py (events, feedback), seed.py
    schemas/           Pydantic v2 models
    api/routes/        Engine routers (added in later parts)
    features/          temporal.py (active) · spatial.py, text.py (stubs)
    utils/geo.py       haversine + centroid
    engines/           predict / triage / foresee / respond (stubs)
    ml/                pipeline.py (active) · train_*.py (stubs)
    learning/          feedback.py, scheduler.py (stubs)
  data/{raw,interim,processed}/
  models/{clearance,triage,foresee}/
  tests/
  run.py  requirements.txt  .env.example
```

## Setup

```bash
cd backend
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# bash/macOS/Linux:    source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Place the raw dataset here (filename per RAW_CSV_PATH in .env):
#   data/raw/Astram_event_data_anonymized_-_Astram_event_data_anonymizedb40ac87.csv

python -m app.db.seed     # runs the pipeline + loads SQLite
```

`seed` is idempotent — it truncates and reloads `events` from the freshly cleaned
parquet, so it always mirrors the current pipeline output.

## Data pipeline (`app/ml/pipeline.py`)

Raw CSV → `data/interim/events_clean.parquet`:

- Literal `"NULL"` (and blanks) → missing.
- UTC timestamps parsed with `utc=True`, converted to IST.
- `duration_min = closed − start` (negative/skewed durations dropped to null).
- `cause_norm` = lowercase `event_cause`, with all `debris*` variants merged to `debris`.
- `veh_type` / `zone` nulls → `unknown`; `requires_road_closure` coerced to bool.
- Temporal features from IST start: `hour_ist`, `dow` (0=Mon), `is_weekend`,
  `is_night` (22:00–04:59), `is_rush` (08–10 & 17–20).

**Never used downstream:** `map_file`, `route_path`, `assigned_to_police_id`.

## Database

- **`events`** — raw Astram columns + derived columns. Indexed on `status`,
  `corridor`, `event_cause`, `start_datetime`.
- **`feedback`** — `(id, event_id, predicted_p50, actual_duration_min, closed_at,
  model_version)` for the online-learning loop.

## Run the API

```bash
python run.py            # http://127.0.0.1:8000  (/health, /docs)
```

## Tests

```bash
pytest                   # temporal + geo unit tests (no dataset required)
```

## Done when

`python -m app.db.seed` loads ~8,173 rows into SQLite with IST timestamps and the
derived columns.
