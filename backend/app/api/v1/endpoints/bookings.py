"""
app/api/v1/endpoints/bookings.py
──────────────────────────────────
Customer booking endpoints. All require JWT auth.

POST /bookings/preview          — price preview before booking
POST /bookings                  — create booking (holds slot, awaits payment)
GET  /bookings                  — customer booking history
GET  /bookings/{id}             — single booking detail
POST /bookings/{id}/cancel      — cancel booking
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, desc, join, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.models import Booking, Refund, User, UserRole, Vehicle
from app.schemas.bookings import (
    BookingCreateRequest,
    BookingResponse,
    CancelBookingRequest,
    PricingBreakdown,
)
from app.schemas.payments import PaymentStatusResponse
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/preview", response_model=PricingBreakdown)
async def price_preview(
    body: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a full price breakdown for the selected car + time slot.
    Does NOT create a booking. Called when user is on the checkout screen.
    """
    return await booking_service.get_price_preview(
        vehicle_id=body.vehicle_id,
        pickup=body.pickup_time,
        dropoff=body.dropoff_time,
        promo_code=body.promo_code,
        db=db,
    )


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    body: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a booking in PENDING state and blocks the availability slot.
    The booking is only confirmed after payment is captured (Phase 5).

    Returns 409 Conflict if the slot is already taken.
    """
    booking = await booking_service.create_booking(
        data=body,
        customer=current_user,
        db=db,
    )
    return BookingResponse.model_validate(booking)


@router.get("", response_model=list[dict])
async def list_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Customer's booking history (most recent first)."""
    return await booking_service.get_customer_bookings(current_user.id, db)


@router.get("/{booking_id}", response_model=dict)
async def get_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single booking with full details. Only the customer, owner, or admin can view."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(404, "Booking not found")

    is_authorized = (
        current_user.id == booking.customer_id
        or current_user.id == booking.owner_id
        or current_user.role == UserRole.ADMIN
    )
    if not is_authorized:
        raise HTTPException(403, "Not authorized")

    return await booking_service.get_booking_detail(booking_id, db)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: str,
    body: CancelBookingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a booking. Triggers refund processing if payment was captured."""
    booking = await booking_service.cancel_booking(
        booking_id=booking_id,
        cancelled_by=current_user.role,
        reason=body.reason,
        actor=current_user,
        db=db,
    )
    return BookingResponse.model_validate(booking)


@router.get("/refunds", tags=["Refunds"])
async def list_refunds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all refunds for the current customer."""
    result = await db.execute(
        select(Refund, Booking, Vehicle)
        .join(Booking, Booking.id == Refund.booking_id)
        .join(Vehicle, Vehicle.id == Booking.vehicle_id)
        .where(Booking.customer_id == current_user.id)
        .order_by(desc(Refund.requested_at))
    )
    rows = result.all()

    return [
        {
            "id": row.Refund.id,
            "booking_id": row.Booking.id,
            "booking_reference": f"VOY-{row.Booking.created_at.strftime('%Y%m%d')}-{row.Booking.id[:8].upper()}",
            "vehicle_name": f"{row.Vehicle.make} {row.Vehicle.model}",
            "cancellation_date": row.Booking.cancelled_at.isoformat() if row.Booking.cancelled_at else None,
            "refund_amount": row.Refund.approved_amount,
            "status": row.Refund.status.value,
            "expected_date": row.Refund.refunded_at.isoformat() if row.Refund.refunded_at else None,
            "created_at": row.Refund.requested_at.isoformat(),
        }
        for row in rows
    ]


@router.get("/reminders", tags=["Reminders"])
async def get_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming reminders for the current customer's bookings."""
    from app.services.reminder_service import get_upcoming_reminders

    return await get_upcoming_reminders(current_user.id, db)
