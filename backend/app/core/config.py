"""
app/core/config.py
──────────────────
Central configuration loaded from environment variables.
All secrets must be injected via environment — never hard-coded.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl
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
    DATABASE_URL: str = ""  # For Railway (takes precedence)
    POSTGRES_SERVER: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @property
    def async_database_url(self) -> str:
        # If DATABASE_URL is provided, use it (Railway provides this)
        if self.DATABASE_URL:
            db_url = self.DATABASE_URL
            # Ensure it uses asyncpg driver
            if "postgresql://" in db_url:
                return db_url.replace("postgresql://", "postgresql+asyncpg://")
            elif "postgresql+psycopg2://" in db_url:
                return db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
            return db_url
        # Fall back to individual connection parameters
        if not all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_SERVER, self.POSTGRES_DB]):
            raise ValueError("Either DATABASE_URL or all POSTGRES_* variables must be set")
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        # If DATABASE_URL is provided, use it (Railway provides this)
        if self.DATABASE_URL:
            db_url = self.DATABASE_URL
            # Ensure it uses psycopg2 driver (for sync operations like Alembic)
            if "postgresql+asyncpg://" in db_url:
                return db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
            elif "postgresql://" in db_url:
                return db_url.replace("postgresql://", "postgresql+psycopg2://")
            return db_url
        # Fall back to individual connection parameters
        if not all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_SERVER, self.POSTGRES_DB]):
            raise ValueError("Either DATABASE_URL or all POSTGRES_* variables must be set")
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
