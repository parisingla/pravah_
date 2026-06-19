"""Application settings, loaded from environment / .env via pydantic-settings v2."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Project root = backend/  (this file is backend/app/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Typed runtime configuration.

    Values come from environment variables or the `.env` file. Field names are
    case-insensitive so `DATABASE_URL` maps to `database_url`.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Supabase Postgres. Set the real connection string in .env (see .env.example).
    # The session pooler host (port 5432) is recommended — IPv4-friendly and
    # supports prepared statements.
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    )
    RAW_CSV_PATH: str = (
        "data/raw/Astram_event_data_anonymized_-_"
        "Astram_event_data_anonymizedb40ac87.csv"
    )
    TIMEZONE: str = "Asia/Kolkata"
    AUTH_DISABLED: bool = True
    # Supabase JWT verification — only used when AUTH_DISABLED=false.
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_JWT_AUD: str = "authenticated"
    # NoDecode: skip pydantic-settings' JSON decode so `_split_cors` can accept a
    # plain comma-separated string from .env.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    LOG_LEVEL: str = "INFO"

    # Respond engine: total dispatchable fleet size (units).
    RESPOND_FLEET_SIZE: int = 45
    # Background scheduler (nightly retrain + hourly hotspot precompute).
    SCHEDULER_ENABLED: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        """Allow CORS_ORIGINS to be a comma-separated string in .env."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def tz(self) -> ZoneInfo:
        """The configured timezone as a ZoneInfo (Asia/Kolkata / IST)."""
        return ZoneInfo(self.TIMEZONE)

    @property
    def raw_csv_path(self) -> Path:
        """Absolute path to the raw events CSV."""
        path = Path(self.RAW_CSV_PATH)
        return path if path.is_absolute() else BASE_DIR / path

    @property
    def interim_dir(self) -> Path:
        return BASE_DIR / "data" / "interim"

    @property
    def processed_dir(self) -> Path:
        return BASE_DIR / "data" / "processed"

    @property
    def models_dir(self) -> Path:
        return BASE_DIR / "models"

    @property
    def sqlalchemy_database_url(self) -> str:
        """Normalized DATABASE_URL ready for SQLAlchemy's create_engine.

        * Postgres (Supabase): bare ``postgres://`` / ``postgresql://`` URLs are
          rewritten to the explicit ``postgresql+psycopg`` driver so we always use
          psycopg v3. URLs that already name a driver are left untouched.
        * SQLite (used by the test suite): relative paths are resolved against
          BASE_DIR so the same file is used regardless of CWD.
        """
        url = self.DATABASE_URL

        # Postgres / Supabase -> pin the psycopg v3 driver.
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://"):]

        # SQLite -> resolve relative file paths against BASE_DIR.
        prefix = "sqlite:///"
        if url.startswith(prefix):
            raw = url[len(prefix):]
            if raw.startswith(("/", "\\")) or (len(raw) > 1 and raw[1] == ":"):
                return url  # already absolute
            return f"{prefix}{(BASE_DIR / raw).as_posix()}"

        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
