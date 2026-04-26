"""
app/main.py
───────────
FastAPI application factory.
All middleware, exception handlers, and routers registered here.
"""

import time
import uuid
from contextlib import contextmanager

import structlog
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import create_engine, text

from app.api.v1.endpoints import admin, auth, bookings, drivers, owner, payments, realtime, reviews, rides, vehicles
from app.core.config import settings

# ── Structured logging setup ──────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()


# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


# ── Database migrations ───────────────────────────────────────────────────────
def run_migrations():
    """Run Alembic migrations on startup."""
    try:
        import subprocess
        import os
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd="/app" if os.path.exists("/app") else os.getcwd(),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            logger.warning("Database migration returned non-zero code", stderr=result.stderr)
        else:
            logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.warning("Could not run database migrations", exc_info=e)
        # Don't fail startup if migrations fail, just log the warning


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,       # hide in production
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Convert AnyHttpUrl objects to strings, ensuring proper format
    cors_origins = [str(o).rstrip('/') for o in settings.BACKEND_CORS_ORIGINS] if settings.BACKEND_CORS_ORIGINS else ["http://localhost:3000", "http://localhost:8000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Rate limiting ─────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── Request ID + Access Log middleware ────────────────────────────────────
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", exc_info=exc, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred"},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    prefix = settings.API_V1_PREFIX
    app.include_router(auth.router,      prefix=prefix)
    app.include_router(vehicles.router,  prefix=prefix)
    app.include_router(drivers.router,   prefix=prefix)
    app.include_router(rides.router,     prefix=prefix)
    app.include_router(bookings.router,  prefix=prefix)
    app.include_router(owner.router,     prefix=prefix)
    app.include_router(admin.router,     prefix=prefix)
    app.include_router(reviews.router,   prefix=prefix)
    app.include_router(payments.router,  prefix=prefix)
    app.include_router(realtime.router)  # WS routes: /ws/... (no v1 prefix)

    # Health check — used by load balancers / k8s probes
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    # ── Startup event: Run database migrations ────────────────────────────────
    @app.on_event("startup")
    async def startup_event():
        run_migrations()

    return app


app = create_app()
