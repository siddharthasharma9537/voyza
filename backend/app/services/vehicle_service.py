"""
app/services/vehicle_service.py
────────────────────────────────
Vehicle browsing, filtering, availability checks.
All DB queries use async SQLAlchemy — no blocking calls.
"""

from __future__ import annotations

import math
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import and_, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.vehicle import Availability, Vehicle, VehicleStatus
from app.models.booking import Review
from app.schemas.vehicles import (
    PaginatedVehicles,
    VehicleBrowseParams,
    VehicleDetail,
    VehicleListItem,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _avg_rating(vehicle_id: str, db: AsyncSession) -> tuple[float | None, int]:
    """Returns (avg_rating, review_count) for a vehicle."""
    result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id))
        .where(Review.vehicle_id == vehicle_id)
    )
    row = result.one()
    avg = round(float(row[0]), 1) if row[0] else None
    return avg, row[1]


def _primary_image(vehicle: Vehicle) -> str | None:
    """Return URL of primary image, or first image, or None."""
    if not vehicle.images:
        return None
    for img in vehicle.images:
        if img.is_primary:
            return img.url
    return vehicle.images[0].url if vehicle.images else None


# ── Browse ────────────────────────────────────────────────────────────────────

async def browse_vehicles(params: VehicleBrowseParams, db: AsyncSession) -> PaginatedVehicles:
    """
    Paginated, filtered vehicle listing.
    Only returns ACTIVE vehicles that are not deleted.

    Availability filter:
    If pickup_time + dropoff_time are provided, exclude vehicles that have
    any overlapping Availability record (blocked OR booked).
    """
    stmt = (
        select(Vehicle)
        .where(Vehicle.status == VehicleStatus.ACTIVE, Vehicle.deleted_at.is_(None))
        .options(selectinload(Vehicle.images))
    )

    if params.city:
        stmt = stmt.where(func.lower(Vehicle.city) == params.city.lower())
    if params.fuel_type:
        stmt = stmt.where(Vehicle.fuel_type == params.fuel_type)
    if params.transmission:
        stmt = stmt.where(Vehicle.transmission == params.transmission)
    if params.min_seating:
        stmt = stmt.where(Vehicle.seating >= params.min_seating)
    if params.min_price_day:
        stmt = stmt.where(Vehicle.price_per_day >= params.min_price_day)
    if params.max_price_day:
        stmt = stmt.where(Vehicle.price_per_day <= params.max_price_day)

    # ── Availability filter ───────────────────────────────────────────────────
    if params.pickup_time and params.dropoff_time:
        try:
            pickup  = datetime.fromisoformat(params.pickup_time)
            dropoff = datetime.fromisoformat(params.dropoff_time)
        except ValueError:
            raise HTTPException(400, "Invalid datetime format. Use ISO 8601.")
        if dropoff <= pickup:
            raise HTTPException(400, "dropoff_time must be after pickup_time")

        overlap_subq = (
            select(Availability.vehicle_id)
            .where(
                and_(
                    Availability.start_time < dropoff,
                    Availability.end_time   > pickup,
                )
            )
            .scalar_subquery()
        )
        stmt = stmt.where(Vehicle.id.not_in(overlap_subq))

    # ── Sorting ───────────────────────────────────────────────────────────────
    sort_map = {
        "price_asc":  Vehicle.price_per_day.asc(),
        "price_desc": Vehicle.price_per_day.desc(),
        "newest":     Vehicle.created_at.desc(),
    }
    if params.sort_by in sort_map:
        stmt = stmt.order_by(sort_map[params.sort_by])

    # ── Pagination ────────────────────────────────────────────────────────────
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (params.page - 1) * params.limit
    result = await db.execute(stmt.offset(offset).limit(params.limit))
    vehicles = result.scalars().all()

    items = []
    for v in vehicles:
        avg, count = await _avg_rating(v.id, db)
        items.append(VehicleListItem(
            id=v.id,
            make=v.make,
            model=v.model,
            variant=v.variant,
            year=v.year,
            city=v.city,
            fuel_type=v.fuel_type,
            transmission=v.transmission,
            seating=v.seating,
            price_per_hour=v.price_per_hour,
            price_per_day=v.price_per_day,
            primary_image=_primary_image(v),
            avg_rating=avg,
            review_count=count,
        ))

    if params.sort_by == "rating":
        items.sort(key=lambda x: x.avg_rating or 0, reverse=True)

    return PaginatedVehicles(
        items=items,
        total=total,
        page=params.page,
        limit=params.limit,
        total_pages=math.ceil(total / params.limit) if total else 0,
    )


# ── Vehicle Detail ─────────────────────────────────────────────────────────────

async def get_vehicle_detail(vehicle_id: str, db: AsyncSession) -> VehicleDetail:
    """Full vehicle detail including images and computed ratings."""
    result = await db.execute(
        select(Vehicle)
        .where(Vehicle.id == vehicle_id, Vehicle.deleted_at.is_(None))
        .options(selectinload(Vehicle.images))
    )
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.status not in (VehicleStatus.ACTIVE,):
        raise HTTPException(status_code=404, detail="Vehicle is not available")

    avg, count = await _avg_rating(vehicle.id, db)

    return VehicleDetail(
        id=vehicle.id,
        owner_id=vehicle.owner_id,
        make=vehicle.make,
        model=vehicle.model,
        variant=vehicle.variant,
        year=vehicle.year,
        color=vehicle.color,
        seating=vehicle.seating,
        fuel_type=vehicle.fuel_type,
        transmission=vehicle.transmission,
        mileage_kmpl=vehicle.mileage_kmpl,
        city=vehicle.city,
        state=vehicle.state,
        latitude=vehicle.latitude,
        longitude=vehicle.longitude,
        address=vehicle.address,
        price_per_hour=vehicle.price_per_hour,
        price_per_day=vehicle.price_per_day,
        security_deposit=vehicle.security_deposit,
        features=vehicle.features or {},
        images=[
            {"id": img.id, "url": img.url, "is_primary": img.is_primary, "sort_order": img.sort_order}
            for img in sorted(vehicle.images, key=lambda i: (not i.is_primary, i.sort_order))
        ],
        avg_rating=avg,
        review_count=count,
        status=vehicle.status,
    )


# ── Availability check (used by booking engine) ───────────────────────────────

async def check_availability(
    vehicle_id: str,
    pickup: datetime,
    dropoff: datetime,
    db: AsyncSession,
    exclude_booking_id: str | None = None,
) -> bool:
    """
    Returns True if the vehicle is available for the given slot.
    Used both in browse AND at booking creation time (double-check).
    """
    conditions = [
        Availability.vehicle_id  == vehicle_id,
        Availability.start_time  < dropoff,
        Availability.end_time    > pickup,
    ]
    if exclude_booking_id:
        conditions.append(Availability.booking_id != exclude_booking_id)

    result = await db.execute(select(exists().where(and_(*conditions))))
    return not result.scalar()


# ── Reviews for a vehicle ─────────────────────────────────────────────────────

async def get_vehicle_reviews(
    vehicle_id: str,
    db: AsyncSession,
    limit: int = 20,
    offset: int = 0,
):
    """Fetch paginated reviews for a vehicle with reviewer names."""
    from app.models.user import User

    result = await db.execute(
        select(Review, User.full_name)
        .join(User, User.id == Review.reviewer_id)
        .where(Review.vehicle_id == vehicle_id)
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [
        {
            "id":          r.Review.id,
            "rating":      r.Review.rating,
            "comment":     r.Review.comment,
            "owner_reply": r.Review.owner_reply,
            "reviewer":    r.full_name,
            "created_at":  r.Review.created_at.isoformat(),
        }
        for r in result.all()
    ]
