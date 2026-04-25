"""
app/api/v1/endpoints/drivers.py
─────────────────────────────────
Driver onboarding and status management endpoints.

POST   /drivers/register          — register as a driver (auth required)
GET    /drivers/me                 — get own driver profile
PATCH  /drivers/me/status         — go online / offline
PATCH  /drivers/me/location       — push GPS location update
GET    /drivers/{id}              — public driver profile (admin/ops)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.drivers import DriverLocationUpdate, DriverOut, DriverRegisterRequest, DriverStatusUpdate
from app.services import driver_service

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.post("/register", response_model=DriverOut, status_code=201)
async def register_driver(
    payload: DriverRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register the current user as a Voyza driver."""
    return await driver_service.register_driver(current_user.id, payload, db)


@router.get("/me", response_model=DriverOut)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch the calling driver's profile."""
    return await driver_service.get_driver_by_user(current_user.id, db)


@router.patch("/me/status", response_model=DriverOut)
async def update_status(
    payload: DriverStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle availability: offline ↔ available."""
    driver = await driver_service.get_driver_by_user(current_user.id, db)
    return await driver_service.update_status(driver.id, payload, db)


@router.patch("/me/location", response_model=DriverOut)
async def update_location(
    payload: DriverLocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Push the driver's current GPS coordinates (REST fallback; prefer WebSocket)."""
    driver = await driver_service.get_driver_by_user(current_user.id, db)
    return await driver_service.update_location(driver.id, payload, db)


@router.get("/{driver_id}", response_model=DriverOut)
async def get_driver(
    driver_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a driver's public profile."""
    return await driver_service.get_driver(driver_id, db)
