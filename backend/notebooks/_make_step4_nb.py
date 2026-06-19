"""Build 07_endpoint_smoke.ipynb (STEP 4)."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "07_endpoint_smoke.ipynb"


def md(t): return {"cell_type": "markdown", "metadata": {}, "source": _l(t)}
def code(t): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _l(t)}
def _l(t):
    t = t.strip("\n"); ls = t.splitlines()
    return [x + "\n" for x in ls[:-1]] + [ls[-1]] if ls else [""]


cells = [
    md("""
# 07 — STEP 4: Endpoint smoke test (no mocks)

Hits every endpoint in the API contract against a **running server** and shows the
real JSON. Uses `urllib` (stdlib) so UTF-8 (Kannada) is handled cleanly.

**Start the server first** in a terminal (seeded local DB):

```
DATABASE_URL=sqlite:///./pravah.db AUTH_DISABLED=true \\
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Wait until `/health` shows `models_loaded: true` (LaBSE load takes ~30s), then run
the cells below.
"""),
    code("""
import json, urllib.request, urllib.error
B = "http://127.0.0.1:8000"

def get(path):
    return json.load(urllib.request.urlopen(B + path, timeout=30))

def post(path, body):
    req = urllib.request.Request(B + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=60))

def show(title, obj):
    print(title)
    print(json.dumps(obj, ensure_ascii=False, indent=2)[:1200])
    print()
"""),
    md("### /health"),
    code('show("/health", get("/health"))'),
    md("### /api/summary"),
    code('show("/api/summary", get("/api/summary"))'),
    md("### /api/events + /api/events/{id}"),
    code("""
events = get("/api/events?limit=2")
show("/api/events?limit=2", events)
eid = events[0]["id"]
show(f"/api/events/{eid}", get(f"/api/events/{eid}"))
"""),
    md("### /api/triage — English AND Kannada"),
    code("""
show("/api/triage (EN)", post("/api/triage",
     {"text": "Major accident with overturned truck blocking two lanes on Hosur Road"}))
show("/api/triage (KN)", post("/api/triage",
     {"text": "ಮೈಸೂರು ರಸ್ತೆಯಲ್ಲಿ ಭಾರಿ ಅಪಘಾತ, ಎರಡು ಲೇನ್ ಬಂದ್ ಆಗಿದೆ"}))
"""),
    md("### /api/predict"),
    code("""
show("/api/predict", post("/api/predict", {
    "event_cause": "accident", "veh_type": "car", "corridor": "Hosur Road",
    "zone": "south", "event_type": "unplanned", "requires_road_closure": True,
    "hour": 18, "dow": 0}))
"""),
    md("### /api/predictions/corridors · /api/hotspots · /api/alerts"),
    code("""
show("/api/predictions/corridors?horizon=1h (top3)", get("/api/predictions/corridors?horizon=1h")[:3])
hs = get("/api/hotspots?horizon=now")
print("hotspots: type", hs["type"], "| n_features", len(hs["features"]))
show("hotspots feature[0]", hs["features"][0])
show("/api/alerts (first 2)", get("/api/alerts")[:2])
"""),
    md("### /api/simulate · /api/analytics"),
    code("""
sim = post("/api/simulate", {"trigger": "accident", "corridor": "Hosur Road", "duration_hours": 2})
sim["routes_geojson"] = f"<FeatureCollection {len(sim['routes_geojson'].get('features', []))} features>"
show("/api/simulate", sim)
show("/api/analytics", get("/api/analytics"))
"""),
    md("### /api/stream (SSE) — read the first event"),
    code("""
import urllib.request
with urllib.request.urlopen(B + "/api/stream", timeout=5) as r:
    print("first SSE line:", r.readline().decode().strip())
"""),
]

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3 (.venv)", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
OUT.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", OUT)
