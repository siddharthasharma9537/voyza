"""
app/services/booking_service.py
────────────────────────────────
Booking engine:
  • Double-booking prevention via DB-level overlap query
  • Pricing calculation (hourly vs daily rate, tax)
  • Promo code validation (stub — Phase 2+)
  • Booking creation + availability slot insertion (atomic)
  • Cancellation with refund trigger

CRITICAL: availability check + booking insert MUST be in the same
DB transaction to prevent race conditions under concurrent requests.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Availability,
    Booking,
    BookingStatus,
    Vehicle,
    VehicleStatus,
    User,
)
from app.schemas.bookings import (
    BookingCreateRequest,
    BookingResponse,
    PricingBreakdown,
)
from app.services.vehicle_service import check_availability

# ── Constants ─────────────────────────────────────────────────────────────────
TAX_RATE = 0.18          # 18% GST
PLATFORM_FEE_RATE = 0.05  # 5% platform fee (included in price)


# ── Pricing engine ────────────────────────────────────────────────────────────

def calculate_pricing(
    car: Vehicle,
    pickup: datetime,
    dropoff: datetime,
    promo_discount_paise: int = 0,
) -> PricingBreakdown:
    """
    Rate logic:
    - If booking >= 20 hours → charge daily rate per day
    - If booking < 20 hours  → charge hourly rate per hour

    This mirrors Zoomcar/Myles pricing patterns.
    All amounts in paise.
    """
    duration_seconds = (dropoff - pickup).total_seconds()
    duration_hours   = duration_seconds / 3600
    duration_days    = math.ceil(duration_hours / 24)

    if duration_hours >= 20:
        # Daily rate
        base_amount = car.price_per_day * duration_days
    else:
        # Hourly rate — ceil to nearest hour
        hours_ceil  = math.ceil(duration_hours)
        base_amount = car.price_per_hour * hours_ceil

    # Apply promo discount (capped at base_amount)
    discount = min(promo_discount_paise, base_amount)
    after_discount = base_amount - discount

    # GST on (base - discount)
    tax_amount = int(after_discount * TAX_RATE)

    total_amount = after_discount + tax_amount + car.security_deposit

    return PricingBreakdown(
        duration_hours=round(duration_hours, 2),
        duration_days=duration_days,
        base_amount=base_amount,
        discount_amount=discount,
        tax_amount=tax_amount,
        security_deposit=car.security_deposit,
        total_amount=total_amount,
    )


# ── Promo codes (stub — full implementation Phase 2+) ─────────────────────────

async def resolve_promo(code: str, vehicle_id: str, db: AsyncSession) -> int:
    """
    Returns discount in paise for the given promo code.
    Returns 0 if code is invalid/expired.
    TODO: implement PromoCode model + validation in Phase 2+
    """
    # Stub: WELCOME10 → flat ₹100 off
    if code and code.upper() == "WELCOME10":
        return 10000  # ₹100 in paise
    return 0


# ── Get price preview (called before payment, no booking created) ─────────────

async def get_price_preview(
    vehicle_id: str,
    pickup: datetime,
    dropoff: datetime,
    promo_code: str | None,
    db: AsyncSession,
) -> PricingBreakdown:
    """Returns pricing breakdown without creating a booking."""
    car_result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.status == VehicleStatus.ACTIVE)
    )
    car = car_result.scalar_one_or_none()
    if not car:
        raise HTTPException(404, "Vehicle not found or unavailable")

    discount = await resolve_promo(promo_code or "", vehicle_id, db) if promo_code else 0
    return calculate_pricing(car, pickup, dropoff, discount)


# ── Create booking (ATOMIC — conflict check + insert in same transaction) ──────

async def create_booking(
    data: BookingCreateRequest,
    customer: User,
    db: AsyncSession,
) -> Booking:
    """
    Steps:
    1. Validate car exists and is active
    2. Check availability (overlap query) — inside this transaction
    3. Calculate price
    4. Insert Booking row
    5. Insert Availability row to block the slot
    6. Commit (done by get_db dependency)

    Any failure rolls back both inserts atomically.
    """
    # ── 1. Load car ───────────────────────────────────────────────────────────
    car_result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == data.vehicle_id,
            Vehicle.status == VehicleStatus.ACTIVE,
            Vehicle.deleted_at.is_(None),
        )
    )
    car = car_result.scalar_one_or_none()
    if not car:
        raise HTTPException(404, "Vehicle not found or unavailable")

    # ── 2. Conflict check (WITHIN this transaction) ────────────────────────────
    # We use SELECT FOR UPDATE on related rows to serialize concurrent requests
    # for the same car. This prevents the TOCTOU race condition.
    overlap = await db.execute(
        select(Availability).where(
            and_(
                Availability.vehicle_id    == data.vehicle_id,
                Availability.start_time < data.dropoff_time,
                Availability.end_time   > data.pickup_time,
            )
        ).with_for_update()
    )
    if overlap.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Vehicle is not available for the selected time slot. Please choose different dates.",
        )

    # ── 3. Calculate price ─────────────────────────────────────────────────────
    discount = await resolve_promo(data.promo_code or "", car.id, db) if data.promo_code else 0
    pricing  = calculate_pricing(car, data.pickup_time, data.dropoff_time, discount)

    # ── 4. Create booking ──────────────────────────────────────────────────────
    booking = Booking(
        customer_id=customer.id,
        vehicle_id=car.id,
        owner_id=car.owner_id,
        pickup_time=data.pickup_time,
        dropoff_time=data.dropoff_time,
        pickup_address=data.pickup_address,
        pickup_latitude=data.pickup_latitude,
        pickup_longitude=data.pickup_longitude,
        base_amount=pricing.base_amount,
        discount_amount=pricing.discount_amount,
        tax_amount=pricing.tax_amount,
        total_amount=pricing.total_amount,
        security_deposit=pricing.security_deposit,
        promo_code=data.promo_code,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    await db.flush()   # get booking.id without committing

    # ── 5. Block slot in availability table ────────────────────────────────────
    slot = Availability(
        vehicle_id=car.id,
        start_time=data.pickup_time,
        end_time=data.dropoff_time,
        reason="booked",
        booking_id=booking.id,
    )
    db.add(slot)
    # Transaction commits in get_db after the endpoint returns

    return booking


# ── Cancel booking ─────────────────────────────────────────────────────────────

async def cancel_booking(
    booking_id: str,
    cancelled_by: str,
    reason: str,
    actor: User,
    db: AsyncSession,
) -> Booking:
    """
    Cancels a booking and frees the availability slot.
    Only the customer, the car owner, or an admin can cancel.
    """
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(404, "Booking not found")

    # Authorization
    from app.models.models import UserRole
    is_customer = actor.id == booking.customer_id
    is_owner    = actor.id == booking.owner_id
    is_admin    = actor.role == UserRole.ADMIN

    if not (is_customer or is_owner or is_admin):
        raise HTTPException(403, "Not authorized to cancel this booking")

    # State check
    if booking.status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
        raise HTTPException(400, f"Cannot cancel a booking in '{booking.status}' state")

    # Update booking
    booking.status       = BookingStatus.CANCELLED
    booking.cancelled_by = cancelled_by
    booking.cancel_reason = reason
    booking.cancelled_at = datetime.now(timezone.utc)

    # Free the availability slot
    avail_result = await db.execute(
        select(Availability).where(Availability.booking_id == booking_id)
    )
    slot = avail_result.scalar_one_or_none()
    if slot:
        await db.delete(slot)

    # TODO: Trigger refund via payment_service in Phase 5

    return booking


# ── Customer booking history ───────────────────────────────────────────────────

async def get_customer_bookings(customer_id: str, db: AsyncSession) -> list[dict]:
    """Returns enriched booking list for the customer's history page."""
    from app.models.models import VehicleImage

    result = await db.execute(
        select(Booking, Vehicle, VehicleImage)
        .join(Vehicle, Vehicle.id == Booking.vehicle_id)
        .outerjoin(VehicleImage, and_(VehicleImage.vehicle_id == Vehicle.id, VehicleImage.is_primary.is_(True)))
        .where(Booking.customer_id == customer_id)
        .order_by(Booking.created_at.desc())
    )
    rows = result.all()

    return [
        {
            "id":           row.Booking.id,
            "vehicle_make":     row.Vehicle.make,
            "vehicle_model":    row.Vehicle.model,
            "car_image":    row.VehicleImage.url if row.VehicleImage else None,
            "pickup_time":  row.Booking.pickup_time.isoformat(),
            "dropoff_time": row.Booking.dropoff_time.isoformat(),
            "status":       row.Booking.status,
            "total_amount": row.Booking.total_amount,
        }
        for row in rows
    ]
