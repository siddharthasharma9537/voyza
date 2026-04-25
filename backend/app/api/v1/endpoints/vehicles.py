"""
app/api/v1/endpoints/vehicles.py
──────────────────────────────────
Public vehicle browsing endpoints (no auth required for reads).

GET  /vehicles                       — browse + filter + availability check
GET  /vehicles/{id}                  — full detail
GET  /vehicles/{id}/reviews          — paginated reviews
GET  /vehicles/{id}/availability     — blocked slots for calendar UI
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.vehicle import Availability
from app.schemas.vehicles import VehicleBrowseParams, VehicleDetail, PaginatedVehicles
from app.services import vehicle_service

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", response_model=PaginatedVehicles)
async def browse_vehicles(
    city:          str | None = Query(None),
    fuel_type:     str | None = Query(None, pattern="^(petrol|diesel|electric|hybrid|cng)$"),
    transmission:  str | None = Query(None, pattern="^(manual|automatic)$"),
    min_seating:   int | None = Query(None, ge=2, le=9),
    min_price_day: int | None = Query(None, ge=0),
    max_price_day: int | None = Query(None, ge=0),
    pickup_time:   str | None = Query(None, description="ISO 8601 datetime"),
    dropoff_time:  str | None = Query(None, description="ISO 8601 datetime"),
    sort_by:       str        = Query("price_asc", pattern="^(price_asc|price_desc|rating|newest)$"),
    page:          int        = Query(1, ge=1),
    limit:         int        = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Browse available vehicles with optional filters.
    If pickup_time + dropoff_time are supplied, only returns vehicles
    with no conflicting availability blocks for that window.
    """
    params = VehicleBrowseParams(
        city=city,
        fuel_type=fuel_type,
        transmission=transmission,
        min_seating=min_seating,
        min_price_day=min_price_day,
        max_price_day=max_price_day,
        pickup_time=pickup_time,
        dropoff_time=dropoff_time,
        sort_by=sort_by,
        page=page,
        limit=limit,
    )
    return await vehicle_service.browse_vehicles(params, db)


@router.get("/{vehicle_id}", response_model=VehicleDetail)
async def get_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    """Full vehicle detail — images, specs, pricing, features, rating."""
    return await vehicle_service.get_vehicle_detail(vehicle_id, db)


@router.get("/{vehicle_id}/reviews")
async def get_reviews(
    vehicle_id: str,
    limit:  int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Paginated reviews for a specific vehicle."""
    return await vehicle_service.get_vehicle_reviews(vehicle_id, db, limit=limit, offset=offset)


@router.get("/{vehicle_id}/availability")
async def get_availability(
    vehicle_id: str,
    from_date: str = Query(..., description="ISO 8601 date (YYYY-MM-DD)"),
    to_date:   str = Query(..., description="ISO 8601 date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns blocked/booked time slots for the vehicle in the given date range.
    Used by the frontend calendar picker to grey out unavailable slots.
    """
    try:
        start = datetime.fromisoformat(from_date)
        end   = datetime.fromisoformat(to_date)
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")

    result = await db.execute(
        select(Availability)
        .where(
            and_(
                Availability.vehicle_id  == vehicle_id,
                Availability.start_time  >= start,
                Availability.end_time    <= end,
            )
        )
        .order_by(Availability.start_time)
    )
    slots = result.scalars().all()

    return [
        {"start": s.start_time.isoformat(), "end": s.end_time.isoformat(), "reason": s.reason}
        for s in slots
    ]
