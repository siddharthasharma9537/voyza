#!/usr/bin/env python3

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models import User, UserRole


def uid():
    return str(uuid4())


def now_utc():
    return datetime.now(timezone.utc)


async def seed():
    engine = create_async_engine(settings.async_database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        print("🌱 Seeding database...")

        admin = User(
            id=uid(),
            full_name="Admin",
            phone="+919000000001",
            email="admin@test.com",
            hashed_password=hash_password("Admin@1234"),
            role="admin",  # IMPORTANT
            is_active=True,
            is_verified=True,
        )

        owner = User(
            id=uid(),
            full_name="Owner",
            phone="+919876543210",
            email="owner@test.com",
            hashed_password=hash_password("Owner@1234"),
            role="owner",
            is_active=True,
            is_verified=True,
        )

        customer = User(
            id=uid(),
            full_name="Customer",
            phone="+919834567890",
            email="customer@test.com",
            hashed_password=hash_password("Customer@1234"),
            role="customer",
            is_active=True,
            is_verified=True,
        )

        db.add_all([admin, owner, customer])

        await db.commit()

        print("✅ Seeding complete!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
