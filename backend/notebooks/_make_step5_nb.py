"""Build 08_hardening.ipynb (STEP 5)."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "08_hardening.ipynb"


def md(t): return {"cell_type": "markdown", "metadata": {}, "source": _l(t)}
def code(t): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _l(t)}
def _l(t):
    t = t.strip("\n"); ls = t.splitlines()
    return [x + "\n" for x in ls[:-1]] + [ls[-1]] if ls else [""]


cells = [
    md("""
# 08 — STEP 5: Production hardening

Checks: (5.1) `/predict` on unseen corridor/cause, (5.2) APScheduler jobs start,
(5.3) `/stream` producers, (5.4) Supabase JWT accept/reject + dev bypass.
Mirrors `_step5_hardening.py`.
"""),
    code("""
import os, sys
from pathlib import Path
from datetime import timedelta
root = Path.cwd()
while not (root / "app").is_dir() and root != root.parent:
    root = root.parent
os.chdir(root); sys.path.insert(0, str(root))
"""),
    md("### 5.1 — `/predict` with unseen corridor + event_cause (no crash?)"),
    code("""
from app.engines.predict import build_features, get_models
m = get_models(); m.load()
for cause, corr in [("accident","Mysore Road"), ("alien_invasion","Nonexistent Galaxy Rd"), ("", None)]:
    f = build_features(event_cause=cause, veh_type="car", corridor=corr, zone="south",
                       event_type="unplanned", requires_road_closure=False, hour=18, dow=0)
    p = m.predict(f)
    print(f"cause={cause!r:16} corr={str(corr)!r:22} -> p50={p['p50']:.1f}  (norm={f['cause_norm']!r}/{f['corridor']!r})")
"""),
    md("### 5.2 — APScheduler jobs register when enabled"),
    code("""
from app.config import settings
from app.learning import scheduler as sched
print("default SCHEDULER_ENABLED:", settings.SCHEDULER_ENABLED)
settings.SCHEDULER_ENABLED = True
s = sched.start_scheduler()
for j in (s.get_jobs() if s else []): print("  job:", j.id, "|", j.trigger)
sched.shutdown_scheduler(); settings.SCHEDULER_ENABLED = False
"""),
    md("### 5.3 — `/stream` producers: are the create/close hooks called anywhere?"),
    code("""
import subprocess
for h in ("on_event_create", "on_event_close"):
    out = subprocess.run(["grep","-rnE",h,"app","--include=*.py"], capture_output=True, text=True).stdout
    calls = [l for l in out.splitlines() if "def "+h not in l and "feedback.py:" not in l]
    print(f"{h}: {len(calls)} call site(s) ->", calls or "NONE (no endpoint triggers it)")
"""),
    md("### 5.4 — Supabase JWT: reject expired/invalid; dev bypass"),
    code("""
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security import DEV_PRINCIPAL, create_access_token, get_current_user
settings.AUTH_DISABLED = False; settings.SUPABASE_JWT_SECRET = "test-secret"
c = lambda t: HTTPAuthorizationCredentials(scheme="Bearer", credentials=t)
def chk(label, cr):
    try: print(f"  {label:16} -> ACCEPT", get_current_user(cr).get("sub"))
    except HTTPException as e: print(f"  {label:16} -> REJECT {e.status_code}")
v = create_access_token({"sub":"u1"}); x = create_access_token({"sub":"u1"}, expires_delta=timedelta(minutes=-5))
chk("valid", c(v)); chk("expired", c(x)); chk("bad sig", c(v[:-3]+"zzz")); chk("missing", None)
settings.AUTH_DISABLED = True
print("  bypass           ->", get_current_user(None) == DEV_PRINCIPAL)
settings.AUTH_DISABLED = False
"""),
    md("""
### Findings
| check | result |
|-------|--------|
| 5.1 unseen corridor/cause | **OK** — CatBoost handles unseen categories; empty → `unknown`; no crash |
| 5.2 scheduler | **OK** — wired in lifespan; 2 jobs register when `SCHEDULER_ENABLED=true` (off by default) |
| 5.3 `/stream` | **GAP** — bus/stream are real, but **no endpoint** calls the create/close hooks, so nothing is ever published live |
| 5.4 JWT | **OK** — expired/invalid/missing → 401; dev bypass works |
"""),
]

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3 (.venv)", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
OUT.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", OUT)
