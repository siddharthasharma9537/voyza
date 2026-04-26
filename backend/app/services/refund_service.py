"""
app/services/refund_service.py
──────────────────────────────
Refund processing service.

Handles:
- Refund creation when booking is cancelled
- Refund amount calculation based on cancellation policy
- Refund processing via payment gateway
- Refund status tracking
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Booking,
    BookingStatus,
    Payment,
    PaymentStatus,
    Refund,
    RefundReason,
    RefundStatus,
    User,
)


# ── Refund policy constants ────────────────────────────────────────────────────

REFUND_POLICY = {
    "full_refund_hours": 24,      # 100% refund if cancelled > 24h before pickup
    "partial_refund_hours": 6,    # 50% refund if cancelled 6-24h before pickup
    "no_refund_hours": 6,         # 0% refund if cancelled < 6h before pickup
    "partial_refund_percent": 0.5,  # 50% of (base + tax)
}


# ── Calculate refund amount based on policy ────────────────────────────────────

def calculate_refund_amount(
    booking: Booking,
    pickup_time: datetime,
    cancelled_at: datetime,
) -> int:
    """
    Calculate refund amount based on cancellation time and policy.

    Returns the amount to refund (in paise).
    Does NOT include security deposit.
    """
    now = cancelled_at or datetime.now(timezone.utc)
    hours_until_pickup = (pickup_time - now).total_seconds() / 3600

    refundable_amount = booking.base_amount + booking.tax_amount - booking.discount_amount

    if hours_until_pickup > REFUND_POLICY["full_refund_hours"]:
        # Full refund (base + tax, not deposit)
        return refundable_amount
    elif hours_until_pickup > REFUND_POLICY["no_refund_hours"]:
        # 50% refund
        return int(refundable_amount * REFUND_POLICY["partial_refund_percent"])
    else:
        # No refund — deposit is retained
        return 0


# ── Create refund for cancelled booking ────────────────────────────────────────

async def create_refund_for_cancellation(
    booking: Booking,
    initiated_by: str,  # "customer", "owner", "admin"
    reason_text: str,
    db: AsyncSession,
) -> Refund:
    """
    Create a Refund record when a booking is cancelled.

    Steps:
    1. Calculate refund amount based on policy
    2. Create Refund record in PENDING status
    3. Return refund object (caller will process via payment gateway)
    """
    if booking.status != BookingStatus.CANCELLED:
        raise HTTPException(400, "Booking must be cancelled before creating refund")

    # Calculate refund amount
    refund_amount = calculate_refund_amount(booking, booking.pickup_time, booking.cancelled_at)

    # Find associated payment (if exists)
    payment_result = await db.execute(
        select(Payment).where(
            Payment.booking_id == booking.id,
            Payment.status == PaymentStatus.CAPTURED,
        )
    )
    payment = payment_result.scalar_one_or_none()

    # Determine refund reason
    if initiated_by == "customer":
        reason = RefundReason.CUSTOMER_CANCELLATION
    elif initiated_by == "owner":
        reason = RefundReason.OWNER_CANCELLATION
    elif initiated_by == "admin":
        reason = RefundReason.ADMIN_CANCELLATION
    else:
        reason = RefundReason.OTHER

    # Create refund record
    refund = Refund(
        booking_id=booking.id,
        payment_id=payment.id if payment else None,
        initiated_by=initiated_by,
        reason=reason,
        reason_text=reason_text,
        requested_amount=refund_amount,
        approved_amount=refund_amount,
        status=RefundStatus.PENDING,
        requested_at=datetime.now(timezone.utc),
    )
    db.add(refund)
    await db.flush()

    return refund


# ── Process refund via payment gateway ────────────────────────────────────────

async def process_refund(
    refund_id: str,
    actor: User,
    db: AsyncSession,
) -> Refund:
    """
    Initiate refund via Razorpay payment gateway.
    Only processes if refund status is PENDING.
    """
    # Load refund
    result = await db.execute(
        select(Refund).where(Refund.id == refund_id)
    )
    refund = result.scalar_one_or_none()

    if not refund:
        raise HTTPException(404, "Refund not found")

    # Check authorization
    from app.models.models import UserRole
    is_admin = actor.role == UserRole.ADMIN

    # For customer, they can only process refunds for their own bookings
    if not is_admin:
        booking_result = await db.execute(
            select(Booking).where(Booking.id == refund.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        if booking and booking.customer_id != actor.id:
            raise HTTPException(403, "Not authorized to process this refund")

    # Check refund status
    if refund.status != RefundStatus.PENDING:
        raise HTTPException(400, f"Cannot process refund in '{refund.status}' state")

    if not refund.payment_id:
        raise HTTPException(400, "No payment found for this refund")

    # Load payment
    payment_result = await db.execute(
        select(Payment).where(Payment.id == refund.payment_id)
    )
    payment = payment_result.scalar_one_or_none()

    if not payment or payment.status != PaymentStatus.CAPTURED:
        raise HTTPException(400, "No captured payment found for this refund")

    # Initiate Razorpay refund
    from app.services.payment_service import _razorpay

    rz = _razorpay()
    try:
        refund_response = rz.payment.refund(
            payment.gateway_payment_id,
            {
                "amount": refund.approved_amount,
                "notes": {
                    "refund_id": refund_id,
                    "reason": refund.reason.value,
                },
            },
        )
    except Exception as e:
        # Mark refund as failed
        refund.status = RefundStatus.FAILED
        refund.failure_reason = str(e)
        refund.processed_at = datetime.now(timezone.utc)
        raise HTTPException(502, f"Failed to process refund: {str(e)}")

    # Update refund status
    refund.status = RefundStatus.INITIATED
    refund.gateway_refund_id = refund_response.get("id")
    refund.processed_at = datetime.now(timezone.utc)
    refund.notes = f"Razorpay refund initiated: {refund_response.get('id')}"

    return refund


# ── Get refund by ID ───────────────────────────────────────────────────────────

async def get_refund(refund_id: str, db: AsyncSession) -> Refund:
    """Fetch a refund by ID."""
    result = await db.execute(
        select(Refund).where(Refund.id == refund_id)
    )
    refund = result.scalar_one_or_none()

    if not refund:
        raise HTTPException(404, "Refund not found")

    return refund


# ── List refunds for customer ──────────────────────────────────────────────────

async def get_customer_refunds(customer_id: str, db: AsyncSession) -> list[dict]:
    """Get all refunds for a customer's bookings."""
    result = await db.execute(
        select(Refund, Booking)
        .join(Booking, Booking.id == Refund.booking_id)
        .where(Booking.customer_id == customer_id)
        .order_by(Refund.requested_at.desc())
    )
    rows = result.all()

    return [
        {
            "id": row.Refund.id,
            "booking_id": row.Booking.id,
            "status": row.Refund.status.value,
            "refund_amount": row.Refund.approved_amount,
            "requested_at": row.Refund.requested_at.isoformat(),
            "processed_at": row.Refund.processed_at.isoformat() if row.Refund.processed_at else None,
            "refunded_at": row.Refund.refunded_at.isoformat() if row.Refund.refunded_at else None,
        }
        for row in rows
    ]
