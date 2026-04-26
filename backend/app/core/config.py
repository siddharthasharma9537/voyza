"""
app/core/config.py
──────────────────
Central configuration loaded from environment variables.
All secrets must be injected via environment — never hard-coded.
"""

from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "Voyza API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    OTP_EXPIRE_MINUTES: int = 10

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = ""  # For Railway, which provides this directly
    POSTGRES_SERVER: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @field_validator("POSTGRES_SERVER", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", mode="before")
    @classmethod
    def parse_database_url_if_needed(cls, v, info):
        """If DATABASE_URL is provided, parse it to extract individual components."""
        if info.data.get("DATABASE_URL"):
            db_url = info.data.get("DATABASE_URL")
            try:
                parsed = urlparse(db_url)
                # Extract components from DATABASE_URL
                if info.field_name == "POSTGRES_SERVER":
                    return parsed.hostname or "localhost"
                elif info.field_name == "POSTGRES_PORT":
                    return parsed.port or 5432
                elif info.field_name == "POSTGRES_USER":
                    return parsed.username or ""
                elif info.field_name == "POSTGRES_PASSWORD":
                    return parsed.password or ""
                elif info.field_name == "POSTGRES_DB":
                    # Remove leading slash from path
                    return (parsed.path or "/").lstrip("/")
            except Exception:
                pass
        return v

    @property
    def async_database_url(self) -> str:
        # If DATABASE_URL is provided, convert it to async version
        if self.DATABASE_URL:
            db_url = self.DATABASE_URL
            # Replace the driver if it's postgresql (sync)
            if "postgresql://" in db_url and "postgresql+asyncpg://" not in db_url:
                return db_url.replace("postgresql://", "postgresql+asyncpg://")
            return db_url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        # If DATABASE_URL is provided, use it directly (or convert from async)
        if self.DATABASE_URL:
            db_url = self.DATABASE_URL
            # Ensure it's the sync version
            if "postgresql+asyncpg://" in db_url:
                return db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
            elif "postgresql://" in db_url:
                return db_url.replace("postgresql://", "postgresql+psycopg2://")
            return db_url
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # ── Storage ──────────────────────────────────────────────────────────────
    S3_BUCKET_NAME: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_ENDPOINT_URL: str | None = None
    S3_REGION: str = "ap-south-1"


    # ── Payments ─────────────────────────────────────────────────────────────
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── OTP / SMS (Twilio) ───────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # ── Email ────────────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
