"""Auth/security helpers.

Two modes, switched by ``AUTH_DISABLED``:

* ``AUTH_DISABLED=true`` (local dev default) — ``get_current_user`` short-circuits
  to a stub dev admin principal so every protected route works without a token.
* ``AUTH_DISABLED=false`` — the ``Authorization: Bearer <jwt>`` header is required
  and the token is verified as a Supabase JWT (HS256, signed with
  ``SUPABASE_JWT_SECRET``). Missing/invalid/expired tokens yield HTTP 401.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

DEV_PRINCIPAL: dict[str, Any] = {"sub": "dev", "role": "admin", "auth_disabled": True}

# auto_error=False so we can return a uniform 401 (and skip auth entirely when
# AUTH_DISABLED) instead of FastAPI's default 403 on a missing header.
_bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Encode a signed Supabase-style JWT (HS256). Used in tests / dev tooling."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.setdefault("aud", settings.SUPABASE_JWT_AUD)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SUPABASE_JWT_SECRET, algorithm=ALGORITHM)


def decode_supabase_jwt(token: str) -> dict[str, Any] | None:
    """Verify a Supabase JWT (HS256, exp + audience). Returns None if invalid."""
    if not settings.SUPABASE_JWT_SECRET:
        # Misconfiguration: auth enabled but no secret to verify against.
        raise RuntimeError(
            "SUPABASE_JWT_SECRET is not set but AUTH_DISABLED is false."
        )
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            audience=settings.SUPABASE_JWT_AUD,
        )
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """FastAPI dependency resolving the current principal.

    Stubbed to a dev admin when ``AUTH_DISABLED``; otherwise verifies the bearer
    token as a Supabase JWT and raises 401 on any failure.
    """
    if settings.AUTH_DISABLED:
        return DEV_PRINCIPAL

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _UNAUTHORIZED

    payload = decode_supabase_jwt(credentials.credentials)
    if payload is None:
        raise _UNAUTHORIZED
    return payload
