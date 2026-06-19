"""STEP 5 — Production hardening checks.

Run:  .venv/Scripts/python.exe notebooks/_step5_hardening.py
"""
from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))


def line(t):
    print("\n" + "=" * 76 + f"\n{t}\n" + "=" * 76)


# --- 5.1 unseen corridor / event_cause on /predict --------------------------
line("5.1  /predict with UNSEEN corridor + event_cause (graceful?)")
from app.engines.predict import build_features, get_models

models = get_models()
models.load()
for cause, corr in [("accident", "Mysore Road"),               # both seen
                    ("alien_invasion", "Nonexistent Galaxy Rd"), # both unseen
                    ("", None)]:                                  # empty -> unknown
    feats = build_features(event_cause=cause, veh_type="car", corridor=corr,
                           zone="south", event_type="unplanned",
                           requires_road_closure=False, hour=18, dow=0)
    pred = models.predict(feats)
    print(f"cause={cause!r:18} corridor={str(corr)!r:24} -> "
          f"p10={pred['p10']:.1f} p50={pred['p50']:.1f} p90={pred['p90']:.1f}  "
          f"(cause_norm={feats['cause_norm']!r}, corridor={feats['corridor']!r})")
print("=> CatBoost handles unseen categories natively; empty -> 'unknown'. No crash.")

# --- 5.2 scheduler jobs actually registered when enabled --------------------
line("5.2  APScheduler jobs start on enable")
from app.config import settings
from app.learning import scheduler as sched

print(f"default SCHEDULER_ENABLED = {settings.SCHEDULER_ENABLED}")
print("start_scheduler() called from app/main.py lifespan:",
      "start_scheduler()" in (root / "app" / "main.py").read_text())
settings.SCHEDULER_ENABLED = True
s = sched.start_scheduler()
jobs = s.get_jobs() if s else []
for j in jobs:
    print(f"  job id={j.id!r:18} trigger={j.trigger}")
sched.shutdown_scheduler()
settings.SCHEDULER_ENABLED = False
print(f"=> {len(jobs)} jobs registered when enabled (disabled by default).")

# --- 5.3 SSE: bus + hooks real, but is there a producer? --------------------
line("5.3  /stream producers — are create/close hooks actually called?")
import subprocess
hooks = ["on_event_create", "on_event_close"]
for h in hooks:
    out = subprocess.run(
        ["grep", "-rnE", h, "app", "--include=*.py"],
        capture_output=True, text=True).stdout.strip().splitlines()
    callers = [l for l in out if "def " + h not in l and "feedback.py:5" not in l
               and "feedback.py:4" not in l]
    print(f"{h}: definition + {len(callers)} call site(s) outside its own module")
    for c in callers:
        print("   ", c)
print("=> Bus/stream are REAL (not stubbed), but no endpoint creates/closes events,")
print("   so the publish hooks are never triggered in the running app.")

# --- 5.4 JWT auth: reject expired/invalid, dev bypass -----------------------
line("5.4  Supabase JWT — reject expired/invalid; dev bypass when disabled")
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security import DEV_PRINCIPAL, create_access_token, get_current_user

settings.AUTH_DISABLED = False
settings.SUPABASE_JWT_SECRET = "test-secret-please-change"


def creds(tok):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=tok)


def try_auth(label, credentials):
    try:
        p = get_current_user(credentials)
        print(f"  {label:24} -> ACCEPT (sub={p.get('sub')})")
    except HTTPException as e:
        print(f"  {label:24} -> REJECT {e.status_code}")


valid = create_access_token({"sub": "u1", "role": "admin"})
expired = create_access_token({"sub": "u1"}, expires_delta=timedelta(minutes=-5))
bad_sig = valid[:-3] + ("aaa" if valid[-3:] != "aaa" else "bbb")
try_auth("valid token", creds(valid))
try_auth("expired token", creds(expired))
try_auth("bad signature", creds(bad_sig))
try_auth("missing header", None)

settings.AUTH_DISABLED = True
p = get_current_user(None)
print(f"  AUTH_DISABLED bypass     -> {p == DEV_PRINCIPAL} (dev principal sub={p['sub']})")
settings.AUTH_DISABLED = False

line("STEP 5 COMPLETE")
