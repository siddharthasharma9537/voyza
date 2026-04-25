"""
app/services/driver_service.py
───────────────────────────────
Driver onboarding, status management, and location updates.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver, DriverStatus
from app.schemas.drivers import DriverLocationUpdate, DriverRegisterRequest, DriverStatusUpdate


async def register_driver(
    user_id: str,
    payload: DriverRegisterRequest,
    db: AsyncSession,
) -> Driver:
    """Create a driver profile for an existing user."""
    existing = await db.execute(select(Driver).where(Driver.user_id == user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver profile already exists for this user",
        )

    driver = Driver(
        user_id=user_id,
        license_number=payload.license_number,
        license_class=payload.license_class,
        license_expiry=payload.license_expiry,
        vehicle_id=payload.vehicle_id,
    )
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return driver


async def get_driver(driver_id: str, db: AsyncSession) -> Driver:
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


async def get_driver_by_user(user_id: str, db: AsyncSession) -> Driver:
    result = await db.execute(select(Driver).where(Driver.user_id == user_id))
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    return driver


async def update_status(
    driver_id: str,
    payload: DriverStatusUpdate,
    db: AsyncSession,
) -> Driver:
    """Toggle driver online/offline. Suspended drivers cannot go available."""
    driver = await get_driver(driver_id, db)

    if driver.status == DriverStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Suspended drivers cannot change status",
        )
    if driver.status == DriverStatus.ON_RIDE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change status while on a ride",
        )

    driver.status = DriverStatus(payload.status)
    await db.commit()
    await db.refresh(driver)
    return driver


async def update_location(
    driver_id: str,
    payload: DriverLocationUpdate,
    db: AsyncSession,
) -> Driver:
    """Update driver's last known GPS coordinates."""
    driver = await get_driver(driver_id, db)
    driver.last_latitude = payload.latitude
    driver.last_longitude = payload.longitude
    driver.location_updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(driver)
    return driver


async def list_available_drivers(city_lat: float, city_lng: float, db: AsyncSession) -> list[Driver]:
    """Return all AVAILABLE drivers (rough bounding-box filter — refine with PostGIS later)."""
    result = await db.execute(
        select(Driver).where(
            Driver.status == DriverStatus.AVAILABLE,
            Driver.is_verified == True,          # noqa: E712
            Driver.last_latitude.isnot(None),
        )
    )
    return result.scalars().all()
