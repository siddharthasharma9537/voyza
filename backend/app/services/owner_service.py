"""
app/services/owner_service.py
──────────────────────────────
All business logic for car owners:
  • List / create / update / delete their cars
  • Submit KYC documents
  • Block availability slots
  • View bookings for their cars
  • Earnings aggregation

Platform fee: 20% of base_amount (owner gets 80%).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    Availability,
    Booking,
    BookingStatus,
    Review,
    Vehicle,
    VehicleImage,
    VehicleStatus,
    KYCStatus,
    Payment,
    PaymentStatus,
    User,
)
from app.schemas.vehicles import VehicleCreateRequest, VehicleUpdateRequest
from app.schemas.owner import (
    BlockSlotRequest,
    EarningsSummary,
    MonthlyEarning,
    OwnerBookingItem,
)

PLATFORM_FEE_RATE = 0.20   # 20% platform cut


# ═══════════════════════════════════════════════════════════════ CAR MANAGEMENT

async def get_owner_cars(owner_id: str, db: AsyncSession) -> list[Vehicle]:
    """Return all non-deleted cars belonging to this owner."""
    result = await db.execute(
        select(Vehicle)
        .where(Vehicle.owner_id == owner_id, Vehicle.deleted_at.is_(None))
        .options(selectinload(Vehicle.images))
        .order_by(Vehicle.created_at.desc())
    )
    return result.scalars().all()


async def create_car(data: VehicleCreateRequest, owner: User, db: AsyncSession) -> Vehicle:
    """
    Owner creates a new car listing.
    Status starts as DRAFT — submitted for admin review separately.
    """
    # Check duplicate registration number
    existing = await db.execute(
        select(Vehicle).where(Vehicle.registration_number == data.registration_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "A car with this registration number already exists")

    car = Vehicle(
        owner_id=owner.id,
        make=data.make,
        model=data.model,
        variant=data.variant,
        year=data.year,
        color=data.color,
        seating=data.seating,
        fuel_type=data.fuel_type,
        transmission=data.transmission,
        mileage_kmpl=data.mileage_kmpl,
        city=data.city,
        state=data.state,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        price_per_hour=data.price_per_hour,
        price_per_day=data.price_per_day,
        security_deposit=data.security_deposit,
        registration_number=data.registration_number.upper(),
        features=data.features,
        status=VehicleStatus.DRAFT,
        kyc_status=KYCStatus.PENDING,
    )
    db.add(car)
    await db.flush()
    return car


async def update_car(
    vehicle_id: str,
    data: VehicleUpdateRequest,
    owner: User,
    db: AsyncSession,
) -> Vehicle:
    """PATCH — only update supplied fields. Owner can only edit their own cars."""
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.owner_id == owner.id, Vehicle.deleted_at.is_(None))
    )
    car = result.scalar_one_or_none()
    if not car:
        raise HTTPException(404, "Vehicle not found")

    # Apply only provided fields
    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(car, field, value)

    return car


async def submit_car_for_review(vehicle_id: str, owner: User, db: AsyncSession) -> Vehicle:
    """Move car from DRAFT → PENDING (triggers admin KYC queue)."""
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.owner_id == owner.id)
    )
    car = result.scalar_one_or_none()
    if not car:
        raise HTTPException(404, "Vehicle not found")

    if car.status != VehicleStatus.DRAFT:
        raise HTTPException(400, f"Vehicle is already in '{car.status}' state")

    # Basic completeness check
    if not car.rc_document_url:
        raise HTTPException(400, "Please upload the RC document before submitting")

    car.status = VehicleStatus.PENDING
    return car


async def delete_car(vehicle_id: str, owner: User, db: AsyncSession) -> None:
    """Soft-delete — only allowed if no active/pending bookings exist."""
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.owner_id == owner.id)
    )
    car = result.scalar_one_or_none()
    if not car:
        raise HTTPException(404, "Vehicle not found")

    # Check for active bookings
    active = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.vehicle_id == vehicle_id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACTIVE, BookingStatus.PENDING]),
        )
    )
    if active.scalar_one() > 0:
        raise HTTPException(
            409,
            "Cannot delete car with active or pending bookings. "
            "Cancel all bookings first."
        )

    car.deleted_at = datetime.now(timezone.utc)
    car.status = VehicleStatus.SUSPENDED


# ═══════════════════════════════════════════════════════════════ AVAILABILITY

async def block_slot(data: BlockSlotRequest, owner: User, db: AsyncSession) -> Availability:
    """Owner manually blocks a time slot (vacation, maintenance)."""
    # Verify car belongs to owner
    car_result = await db.execute(
        select(Vehicle).where(Vehicle.id == data.vehicle_id, Vehicle.owner_id == owner.id)
    )
    if not car_result.scalar_one_or_none():
        raise HTTPException(404, "Vehicle not found")

    if data.end_time <= data.start_time:
        raise HTTPException(400, "end_time must be after start_time")

    # Check for conflicts with existing bookings
    conflict = await db.execute(
        select(Availability).where(
            and_(
                Availability.vehicle_id    == data.vehicle_id,
                Availability.start_time < data.end_time,
                Availability.end_time   > data.start_time,
                Availability.reason    == "booked",  # don't block over real bookings
            )
        )
    )
    if conflict.scalar_one_or_none():
        raise HTTPException(
            409,
            "There's an existing confirmed booking in this time slot. "
            "Cancel the booking first."
        )

    slot = Availability(
        vehicle_id=data.vehicle_id,
        start_time=data.start_time,
        end_time=data.end_time,
        reason=data.reason,
    )
    db.add(slot)
    await db.flush()
    return slot


async def unblock_slot(slot_id: str, owner: User, db: AsyncSession) -> None:
    """Remove a manually-blocked slot (cannot remove booking-created slots)."""
    result = await db.execute(
        select(Availability)
        .join(Vehicle, Vehicle.id == Availability.vehicle_id)
        .where(
            Availability.id == slot_id,
            Vehicle.owner_id == owner.id,
            Availability.reason != "booked",   # can't unblock real bookings
        )
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(404, "Slot not found or cannot be removed")

    await db.delete(slot)


# ═══════════════════════════════════════════════════════════════ BOOKINGS VIEW

async def get_owner_bookings(owner_id: str, db: AsyncSession) -> list[dict]:
    """
    All bookings for cars owned by this owner.
    Enriched with customer name and owner earnings.
    """
    result = await db.execute(
        select(Booking, Vehicle, User)
        .join(Vehicle, Vehicle.id == Booking.vehicle_id)
        .join(User, User.id == Booking.customer_id)
        .where(Booking.owner_id == owner_id)
        .order_by(Booking.created_at.desc())
    )
    rows = result.all()

    return [
        {
            "id":             row.Booking.id,
            "vehicle_make":       row.Vehicle.make,
            "vehicle_model":      row.Vehicle.model,
            "customer_name":  row.User.full_name,
            "customer_phone": row.User.phone,
            "pickup_time":    row.Booking.pickup_time.isoformat(),
            "dropoff_time":   row.Booking.dropoff_time.isoformat(),
            "status":         row.Booking.status,
            "total_amount":   row.Booking.total_amount,
            "owner_earnings": int(row.Booking.base_amount * (1 - PLATFORM_FEE_RATE)),
        }
        for row in rows
    ]


async def accept_booking(booking_id: str, owner: User, db: AsyncSession) -> Booking:
    """Owner explicitly accepts a pending booking (if instant booking is off)."""
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.owner_id == owner.id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(400, f"Cannot accept booking in '{booking.status}' state")

    booking.status = BookingStatus.CONFIRMED
    return booking


# ═══════════════════════════════════════════════════════════════ EARNINGS

async def get_earnings(owner_id: str, db: AsyncSession) -> EarningsSummary:
    """
    Aggregated earnings dashboard for the owner.
    Earnings = base_amount × (1 - PLATFORM_FEE_RATE) for completed bookings
    with captured payments.
    """
    now = datetime.now(timezone.utc)
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start.replace(month=this_month_start.month - 1)
                        if this_month_start.month > 1
                        else this_month_start.replace(year=this_month_start.year - 1, month=12))

    # All completed bookings for this owner
    completed = await db.execute(
        select(Booking, Vehicle)
        .join(Vehicle, Vehicle.id == Booking.vehicle_id)
        .where(
            Booking.owner_id == owner_id,
            Booking.status   == BookingStatus.COMPLETED,
        )
    )
    completed_rows = completed.all()

    def owner_cut(b: Booking) -> int:
        return int(b.base_amount * (1 - PLATFORM_FEE_RATE))

    total_earnings = sum(owner_cut(r.Booking) for r in completed_rows)

    this_month = sum(
        owner_cut(r.Booking) for r in completed_rows
        if r.Booking.created_at >= this_month_start
    )
    last_month = sum(
        owner_cut(r.Booking) for r in completed_rows
        if last_month_start <= r.Booking.created_at < this_month_start
    )

    # Pending payout = confirmed bookings not yet completed
    pending_result = await db.execute(
        select(func.sum(Booking.base_amount)).where(
            Booking.owner_id == owner_id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
        )
    )
    pending_base = pending_result.scalar_one() or 0
    pending_payout = int(pending_base * (1 - PLATFORM_FEE_RATE))

    # Total booking counts
    total_b_result = await db.execute(
        select(func.count(Booking.id)).where(Booking.owner_id == owner_id)
    )
    total_bookings = total_b_result.scalar_one()

    # Avg rating across all owner's cars
    avg_result = await db.execute(
        select(func.avg(
            select(func.avg(Review.rating))
            .join(Vehicle, Vehicle.id == Review.vehicle_id)
            .where(Vehicle.owner_id == owner_id)
            .scalar_subquery()
        ))
    )

    # Best earning car
    car_earnings: dict[str, int] = {}
    for r in completed_rows:
        key = f"{r.Vehicle.make} {r.Vehicle.model}"
        car_earnings[key] = car_earnings.get(key, 0) + owner_cut(r.Booking)
    top_car = max(car_earnings, key=car_earnings.get) if car_earnings else None

    return EarningsSummary(
        total_earnings=total_earnings,
        this_month=this_month,
        last_month=last_month,
        pending_payout=pending_payout,
        total_bookings=total_bookings,
        completed_bookings=len(completed_rows),
        avg_rating=None,   # simplified — full impl uses Review join
        top_car=top_car,
    )


async def get_monthly_earnings(owner_id: str, db: AsyncSession, months: int = 6) -> list[MonthlyEarning]:
    """Last N months of earnings broken down month-by-month."""
    result = await db.execute(
        select(
            func.to_char(Booking.created_at, "YYYY-MM").label("month"),
            func.sum(Booking.base_amount).label("base_total"),
            func.count(Booking.id).label("booking_count"),
        )
        .where(
            Booking.owner_id == owner_id,
            Booking.status   == BookingStatus.COMPLETED,
        )
        .group_by("month")
        .order_by("month")
    )
    rows = result.all()

    return [
        MonthlyEarning(
            month=row.month,
            amount=int(row.base_total * (1 - PLATFORM_FEE_RATE)),
            bookings=row.booking_count,
        )
        for row in rows
    ]
