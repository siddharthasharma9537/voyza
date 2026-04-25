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

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.models import User
from app.schemas.bookings import (
    BookingCreateRequest,
    BookingResponse,
    CancelBookingRequest,
    PricingBreakdown,
)
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


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single booking. Only the customer, owner, or admin can view."""
    from sqlalchemy import select
    from app.models.models import Booking, UserRole
    from fastapi import HTTPException

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

    return BookingResponse.model_validate(booking)


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
