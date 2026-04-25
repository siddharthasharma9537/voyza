"""
tests/conftest.py
──────────────────
Shared pytest fixtures for unit and integration tests.

Unit tests:   use mock_db fixture (no real DB)
Integration:  use async_client fixture (real TestClient + SQLite in-memory)
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.db.base import Base, get_db
from app.main import app
from app.models import User, UserRole


# ── In-memory SQLite for integration tests ────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Fresh DB session per test, rolled back after."""
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI AsyncClient with overridden DB dependency."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()


# ── Mock DB for unit tests ─────────────────────────────────────────────────────
@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


# ── User fixtures ──────────────────────────────────────────────────────────────
@pytest.fixture
def sample_customer() -> User:
    user = User(
        id="customer-uuid-1234",
        full_name="Test Customer",
        phone="+919876543210",
        email="customer@test.com",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
    )
    return user


@pytest.fixture
def sample_owner() -> User:
    user = User(
        id="owner-uuid-5678",
        full_name="Test Owner",
        phone="+919812345678",
        email="owner@test.com",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.OWNER,
        is_active=True,
        is_verified=True,
    )
    return user


@pytest.fixture
def sample_admin() -> User:
    user = User(
        id="admin-uuid-9012",
        full_name="Test Admin",
        phone="+919823456789",
        email="admin@test.com",
        hashed_password=hash_password("Admin@1234"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    return user


# ── Token fixtures ─────────────────────────────────────────────────────────────
@pytest.fixture
def customer_token(sample_customer) -> str:
    return create_access_token(subject=sample_customer.id, role=sample_customer.role)


@pytest.fixture
def owner_token(sample_owner) -> str:
    return create_access_token(subject=sample_owner.id, role=sample_owner.role)


@pytest.fixture
def admin_token(sample_admin) -> str:
    return create_access_token(subject=sample_admin.id, role=sample_admin.role)


# ── Time helpers ──────────────────────────────────────────────────────────────
@pytest.fixture
def future_pickup():
    return datetime.now(timezone.utc) + timedelta(hours=48)


@pytest.fixture
def future_dropoff():
    return datetime.now(timezone.utc) + timedelta(hours=72)
