"""Shared FastAPI dependencies (re-exported for convenience in routes)."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]

__all__ = ["DbSession", "CurrentUser", "get_db", "get_current_user"]
