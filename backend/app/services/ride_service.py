"""
app/services/ride_service.py
─────────────────────────────
Core ride lifecycle: request → accept → start → complete / cancel.
Fare estimation lives here too; move to pricing_service.py if it grows.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver, DriverStatus
from app.models.ride import Ride, RideStatus
from app.schemas.rides import FareEstimate, RideCancelRequest, RideRequestCreate


# ── Fare estimation ────────────────────────────────────────────────────────────

_BASE_FARE_PAISE = 2000        # ₹20
_PER_KM_PAISE = 1200           # ₹12 / km
_PER_MINUTE_PAISE = 150        # ₹1.50 / min


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line distance in km between two GPS points."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_fare(
    pickup_lat: float, pickup_lng: float,
    dropoff_lat: float, dropoff_lng: float,
    surge: Decimal = Decimal("1.0"),
) -> FareEstimate:
    distance_km = round(_haversine_km(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng), 3)
    duration_min = max(1, int(distance_km / 0.4))   # rough avg 24 km/h in city
    fare = int(
        (_BASE_FARE_PAISE + distance_km * _PER_KM_PAISE + duration_min * _PER_MINUTE_PAISE)
        * float(surge)
    )
    return FareEstimate(
        estimated_fare=fare,
        distance_km=Decimal(str(round(distance_km, 3))),
        duration_minutes=duration_min,
        surge_multiplier=surge,
    )


# ── Ride lifecycle ─────────────────────────────────────────────────────────────

async def request_ride(
    customer_id: str,
    payload: RideRequestCreate,
    db: AsyncSession,
) -> Ride:
    fare = estimate_fare(
        float(payload.pickup_latitude), float(payload.pickup_longitude),
        float(payload.dropoff_latitude), float(payload.dropoff_longitude),
    )
    ride = Ride(
        booking_id=payload.booking_id,
        customer_id=customer_id,
        vehicle_id=payload.booking_id or "",   # resolved by dispatcher; placeholder
        pickup_address=payload.pickup_address,
        pickup_latitude=payload.pickup_latitude,
        pickup_longitude=payload.pickup_longitude,
        dropoff_address=payload.dropoff_address,
        dropoff_latitude=payload.dropoff_latitude,
        dropoff_longitude=payload.dropoff_longitude,
        estimated_fare=fare.estimated_fare,
        requested_at=datetime.now(timezone.utc),
        status=RideStatus.REQUESTED,
    )
    db.add(ride)
    await db.commit()
    await db.refresh(ride)
    return ride


async def accept_ride(ride_id: str, driver_id: str, db: AsyncSession) -> Ride:
    ride = await _get_ride(ride_id, db)
    driver = await db.get(Driver, driver_id)

    if ride.status != RideStatus.REQUESTED:
        raise HTTPException(409, "Ride is no longer available")
    if not driver or driver.status != DriverStatus.AVAILABLE:
        raise HTTPException(409, "Driver is not available")

    ride.driver_id = driver_id
    ride.vehicle_id = driver.vehicle_id
    ride.status = RideStatus.ACCEPTED
    ride.accepted_at = datetime.now(timezone.utc)
    driver.status = DriverStatus.ON_RIDE

    await db.commit()
    await db.refresh(ride)
    return ride


async def start_ride(ride_id: str, driver_id: str, db: AsyncSession) -> Ride:
    ride = await _get_ride(ride_id, db)
    _assert_driver(ride, driver_id)
    if ride.status != RideStatus.ACCEPTED:
        raise HTTPException(409, f"Cannot start a ride in '{ride.status}' status")

    ride.status = RideStatus.IN_PROGRESS
    ride.started_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ride)
    return ride


async def complete_ride(ride_id: str, driver_id: str, db: AsyncSession) -> Ride:
    ride = await _get_ride(ride_id, db)
    _assert_driver(ride, driver_id)
    if ride.status != RideStatus.IN_PROGRESS:
        raise HTTPException(409, "Ride is not in progress")

    now = datetime.now(timezone.utc)
    ride.status = RideStatus.COMPLETED
    ride.completed_at = now
    ride.final_fare = ride.estimated_fare   # replace with metered fare if GPS trail available

    driver = await db.get(Driver, driver_id)
    if driver:
        driver.status = DriverStatus.AVAILABLE
        driver.total_rides = (driver.total_rides or 0) + 1

    await db.commit()
    await db.refresh(ride)
    return ride


async def cancel_ride(
    ride_id: str,
    cancelled_by: str,   # "customer" | "driver" | "system"
    payload: RideCancelRequest,
    db: AsyncSession,
) -> Ride:
    ride = await _get_ride(ride_id, db)
    if ride.status in (RideStatus.COMPLETED, RideStatus.CANCELLED):
        raise HTTPException(409, "Ride is already finished")

    ride.status = RideStatus.CANCELLED
    ride.cancelled_at = datetime.now(timezone.utc)
    ride.cancelled_by = cancelled_by
    ride.cancel_reason = payload.reason

    if ride.driver_id:
        driver = await db.get(Driver, ride.driver_id)
        if driver and driver.status == DriverStatus.ON_RIDE:
            driver.status = DriverStatus.AVAILABLE

    await db.commit()
    await db.refresh(ride)
    return ride


async def get_ride(ride_id: str, db: AsyncSession) -> Ride:
    return await _get_ride(ride_id, db)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_ride(ride_id: str, db: AsyncSession) -> Ride:
    result = await db.execute(select(Ride).where(Ride.id == ride_id))
    ride = result.scalar_one_or_none()
    if not ride:
        raise HTTPException(404, "Ride not found")
    return ride


def _assert_driver(ride: Ride, driver_id: str) -> None:
    if ride.driver_id != driver_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not assigned to this ride")
