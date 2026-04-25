"""
app/api/v1/endpoints/rides.py
───────────────────────────────
Ride request and lifecycle endpoints.

POST  /rides                      — request a new ride
GET   /rides/{id}                 — get ride details
POST  /rides/{id}/accept          — driver accepts ride
POST  /rides/{id}/start           — driver starts ride
POST  /rides/{id}/complete        — driver completes ride
POST  /rides/{id}/cancel          — customer or driver cancels
GET   /rides/{id}/trail           — GPS breadcrumb trail
POST  /rides/fare-estimate        — estimate fare before booking
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.rides import (
    FareEstimate,
    RideCancelRequest,
    RideOut,
    RideRequestCreate,
)
from app.services import driver_service, ride_service

router = APIRouter(prefix="/rides", tags=["Rides"])


@router.post("/fare-estimate", response_model=FareEstimate)
async def fare_estimate(payload: RideRequestCreate):
    """
    Estimate fare for a trip before requesting.
    No auth required — used in the booking preview screen.
    """
    return ride_service.estimate_fare(
        float(payload.pickup_latitude), float(payload.pickup_longitude),
        float(payload.dropoff_latitude), float(payload.dropoff_longitude),
    )


@router.post("", response_model=RideOut, status_code=201)
async def request_ride(
    payload: RideRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request a new ride. Kicks off driver matching."""
    return await ride_service.request_ride(current_user.id, payload, db)


@router.get("/{ride_id}", response_model=RideOut)
async def get_ride(
    ride_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get ride status and details."""
    return await ride_service.get_ride(ride_id, db)


@router.post("/{ride_id}/accept", response_model=RideOut)
async def accept_ride(
    ride_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver accepts a requested ride."""
    driver = await driver_service.get_driver_by_user(current_user.id, db)
    return await ride_service.accept_ride(ride_id, driver.id, db)


@router.post("/{ride_id}/start", response_model=RideOut)
async def start_ride(
    ride_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver marks the ride as started (customer is in the vehicle)."""
    driver = await driver_service.get_driver_by_user(current_user.id, db)
    return await ride_service.start_ride(ride_id, driver.id, db)


@router.post("/{ride_id}/complete", response_model=RideOut)
async def complete_ride(
    ride_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Driver completes the ride at the destination."""
    driver = await driver_service.get_driver_by_user(current_user.id, db)
    return await ride_service.complete_ride(ride_id, driver.id, db)


@router.post("/{ride_id}/cancel", response_model=RideOut)
async def cancel_ride(
    ride_id: str,
    payload: RideCancelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a ride (customer or driver)."""
    return await ride_service.cancel_ride(ride_id, "customer", payload, db)


@router.get("/{ride_id}/trail")
async def get_gps_trail(
    ride_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the full GPS breadcrumb trail for a ride."""
    from app.services.tracking_service import get_trail
    return await get_trail(ride_id, db)
