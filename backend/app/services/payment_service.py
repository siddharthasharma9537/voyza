"""
app/services/payment_service.py
────────────────────────────────
Complete Razorpay payment lifecycle:

  1. create_order()      — create Razorpay order, store Payment row (CREATED)
  2. verify_payment()    — verify HMAC signature, confirm booking (CAPTURED)
  3. handle_webhook()    — async event handler for Razorpay webhooks
  4. process_refund()    — initiate refund via Razorpay API

Security notes:
  • Signature verification uses HMAC-SHA256 — never trust payment_id alone
  • Webhook secret verified via X-Razorpay-Signature header
  • Payment IDs have a UNIQUE constraint — duplicate webhook events are idempotent
  • All monetary values stored and processed as INTEGER paise
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone

import razorpay
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import (
    Booking,
    BookingStatus,
    Payment,
    PaymentGateway,
    PaymentStatus,
    User,
)
from app.schemas.payments import (
    CreateOrderResponse,
    RefundResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)

# ── Razorpay client (lazy singleton) ──────────────────────────────────────────
_rz_client: razorpay.Client | None = None


def _razorpay() -> razorpay.Client:
    """Return cached Razorpay client. Thread-safe for async context."""
    global _rz_client
    if _rz_client is None:
        _rz_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    return _rz_client


# ═══════════════════════════════════════════════════════════════════════
#  1. CREATE ORDER
# ═══════════════════════════════════════════════════════════════════════

async def create_order(
    booking_id: str,
    customer: User,
    db: AsyncSession,
) -> CreateOrderResponse:
    """
    Creates a Razorpay order for a PENDING booking.
    Stores a Payment record in CREATED state.

    Called by: POST /payments/create-order
    """
    # ── Load and validate booking ─────────────────────────────────────
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.customer_id == customer.id,
        )
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(404, "Booking not found")

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            400,
            f"Cannot create payment for booking in '{booking.status}' state. "
            "Only PENDING bookings can be paid."
        )

    # ── Check if a payment order already exists ───────────────────────
    existing_payment = await db.execute(
        select(Payment).where(
            Payment.booking_id == booking_id,
            Payment.status     == PaymentStatus.CREATED,
        )
    )
    existing = existing_payment.scalar_one_or_none()
    if existing:
        # Reuse the existing order (idempotent — user may have refreshed)
        return CreateOrderResponse(
            razorpay_order_id=existing.gateway_order_id,
            amount=existing.amount,
            currency=existing.currency,
            booking_id=booking_id,
            key_id=settings.RAZORPAY_KEY_ID,
        )

    # ── Create Razorpay order ─────────────────────────────────────────
    rz = _razorpay()
    try:
        order = rz.order.create({
            "amount":   booking.total_amount,     # already in paise
            "currency": "INR",
            "receipt":  f"booking_{booking_id[:8]}",
            "notes": {
                "booking_id":   booking_id,
                "customer_id":  customer.id,
                "customer_name": customer.full_name,
            },
        })
    except Exception as e:
        raise HTTPException(502, f"Payment gateway error: {str(e)}")

    # ── Store Payment record ───────────────────────────────────────────
    payment = Payment(
        booking_id=booking_id,
        gateway=PaymentGateway.RAZORPAY,
        gateway_order_id=order["id"],
        amount=booking.total_amount,
        currency="INR",
        status=PaymentStatus.CREATED,
        gateway_response=order,
    )
    db.add(payment)
    await db.flush()

    return CreateOrderResponse(
        razorpay_order_id=order["id"],
        amount=booking.total_amount,
        currency="INR",
        booking_id=booking_id,
        key_id=settings.RAZORPAY_KEY_ID,
    )


# ═══════════════════════════════════════════════════════════════════════
#  2. VERIFY PAYMENT (client callback after checkout)
# ═══════════════════════════════════════════════════════════════════════

async def verify_payment(
    data: VerifyPaymentRequest,
    db: AsyncSession,
) -> VerifyPaymentResponse:
    """
    Verifies the HMAC-SHA256 signature from Razorpay checkout callback.

    Razorpay signature = HMAC_SHA256(
        key    = razorpay_key_secret,
        message= f"{order_id}|{payment_id}"
    )

    Only after successful verification do we:
      • Mark Payment as CAPTURED
      • Mark Booking as CONFIRMED
    """
    # ── 1. Verify signature ───────────────────────────────────────────
    message  = f"{data.razorpay_order_id}|{data.razorpay_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, data.razorpay_signature):
        # Log the attempt — potential fraud
        raise HTTPException(
            status_code=400,
            detail="Payment signature verification failed. Do not retry — contact support."
        )

    # ── 2. Load payment record ────────────────────────────────────────
    payment_result = await db.execute(
        select(Payment).where(
            Payment.gateway_order_id == data.razorpay_order_id,
            Payment.booking_id       == data.booking_id,
        )
    )
    payment = payment_result.scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment record not found")

    # Idempotency — already captured (duplicate callback)
    if payment.status == PaymentStatus.CAPTURED:
        return VerifyPaymentResponse(
            success=True,
            booking_id=data.booking_id,
            status="confirmed",
            message="Payment already confirmed",
        )

    # ── 3. Update payment record ──────────────────────────────────────
    payment.status             = PaymentStatus.CAPTURED
    payment.gateway_payment_id = data.razorpay_payment_id
    payment.gateway_signature  = data.razorpay_signature

    # Fetch full payment details from Razorpay for our records
    try:
        rz      = _razorpay()
        details = rz.payment.fetch(data.razorpay_payment_id)
        payment.gateway_response = details
    except Exception:
        pass  # Non-fatal — we have signature proof; log and continue

    # ── 4. Confirm booking ────────────────────────────────────────────
    booking_result = await db.execute(
        select(Booking).where(Booking.id == data.booking_id)
    )
    booking = booking_result.scalar_one_or_none()
    if booking:
        booking.status = BookingStatus.CONFIRMED

    # ── 5. TODO: Send confirmation SMS/email (Phase 6 notifications) ──

    return VerifyPaymentResponse(
        success=True,
        booking_id=data.booking_id,
        status="confirmed",
        message="Payment captured. Booking confirmed!",
    )


# ═══════════════════════════════════════════════════════════════════════
#  3. WEBHOOK HANDLER
# ═══════════════════════════════════════════════════════════════════════

async def handle_webhook(
    raw_body: bytes,
    signature_header: str,
    db: AsyncSession,
) -> dict:
    """
    Verifies Razorpay webhook signature and dispatches event.

    Razorpay sends X-Razorpay-Signature = HMAC_SHA256(
        key     = webhook_secret,
        message = raw_body_bytes
    )

    Events handled:
      payment.captured   → confirm booking (backup for client verify)
      payment.failed     → mark payment failed, free booking slot
      refund.processed   → update refund status
    """
    # ── Verify webhook signature ──────────────────────────────────────
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(400, "Invalid webhook signature")

    # ── Parse event ───────────────────────────────────────────────────
    try:
        event_data = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON payload")

    event = event_data.get("event", "")

    if event == "payment.captured":
        await _webhook_payment_captured(event_data, db)
    elif event == "payment.failed":
        await _webhook_payment_failed(event_data, db)
    elif event == "refund.processed":
        await _webhook_refund_processed(event_data, db)
    # Other events are acknowledged but not acted on

    return {"status": "ok", "event": event}


async def _webhook_payment_captured(event_data: dict, db: AsyncSession) -> None:
    """Backup handler — client verify() should have already done this."""
    payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
    order_id   = payment_entity.get("order_id")
    payment_id = payment_entity.get("id")

    if not order_id:
        return

    result = await db.execute(
        select(Payment).where(Payment.gateway_order_id == order_id)
    )
    payment = result.scalar_one_or_none()

    if payment and payment.status != PaymentStatus.CAPTURED:
        payment.status             = PaymentStatus.CAPTURED
        payment.gateway_payment_id = payment_id
        payment.gateway_response   = payment_entity

        # Confirm booking
        booking_result = await db.execute(
            select(Booking).where(Booking.id == payment.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        if booking and booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CONFIRMED


async def _webhook_payment_failed(event_data: dict, db: AsyncSession) -> None:
    """
    Mark payment as FAILED.
    Free the availability slot so the car can be rebooked.
    """
    from app.models.models import Availability

    payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id")
    if not order_id:
        return

    result = await db.execute(
        select(Payment).where(Payment.gateway_order_id == order_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        return

    payment.status           = PaymentStatus.FAILED
    payment.gateway_response = payment_entity

    # Mark booking as cancelled and free the slot
    booking_result = await db.execute(
        select(Booking).where(Booking.id == payment.booking_id)
    )
    booking = booking_result.scalar_one_or_none()
    if booking and booking.status == BookingStatus.PENDING:
        booking.status        = BookingStatus.CANCELLED
        booking.cancelled_by  = "system"
        booking.cancel_reason = "Payment failed"
        booking.cancelled_at  = datetime.now(timezone.utc)

        # Free availability slot
        avail_result = await db.execute(
            select(Availability).where(Availability.booking_id == payment.booking_id)
        )
        slot = avail_result.scalar_one_or_none()
        if slot:
            await db.delete(slot)


async def _webhook_refund_processed(event_data: dict, db: AsyncSession) -> None:
    """Update refund status when Razorpay confirms the refund is processed."""
    refund_entity = event_data.get("payload", {}).get("refund", {}).get("entity", {})
    payment_id    = refund_entity.get("payment_id")
    refund_id     = refund_entity.get("id")
    refund_amount = refund_entity.get("amount", 0)

    if not payment_id:
        return

    result = await db.execute(
        select(Payment).where(Payment.gateway_payment_id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if payment:
        payment.status        = PaymentStatus.REFUNDED
        payment.refund_id     = refund_id
        payment.refund_amount = refund_amount
        payment.refunded_at   = datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════
#  4. REFUND
# ═══════════════════════════════════════════════════════════════════════

async def process_refund(
    booking_id: str,
    actor: User,
    reason: str,
    partial_amount: int | None,
    db: AsyncSession,
) -> RefundResponse:
    """
    Initiates a refund via Razorpay.

    Refund policy (stored in booking cancellation logic):
      • Cancelled > 24h before pickup → 100% refund (base + tax, not deposit)
      • Cancelled 6–24h before pickup → 50% refund
      • Cancelled < 6h before pickup  → 0% refund (deposit retained)

    Admin can override and issue any amount.
    """
    from app.models.models import UserRole

    # ── Load booking ──────────────────────────────────────────────────
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")

    # Authorization check
    is_customer = actor.id == booking.customer_id
    is_admin    = actor.role == UserRole.ADMIN
    if not (is_customer or is_admin):
        raise HTTPException(403, "Not authorized to refund this booking")

    # ── Load captured payment ─────────────────────────────────────────
    payment_result = await db.execute(
        select(Payment).where(
            Payment.booking_id == booking_id,
            Payment.status     == PaymentStatus.CAPTURED,
        )
    )
    payment = payment_result.scalar_one_or_none()
    if not payment:
        raise HTTPException(400, "No captured payment found for this booking")

    if payment.status == PaymentStatus.REFUNDED:
        raise HTTPException(400, "Payment has already been refunded")

    # ── Calculate refund amount ───────────────────────────────────────
    now = datetime.now(timezone.utc)
    hours_until_pickup = (booking.pickup_time - now).total_seconds() / 3600

    if partial_amount is not None and is_admin:
        # Admin override — refund exactly the requested amount
        refund_amount = min(partial_amount, payment.amount)
    elif hours_until_pickup > 24:
        # Full refund (base + tax — deposit NOT refunded per policy)
        refund_amount = booking.base_amount + booking.tax_amount - booking.discount_amount
    elif hours_until_pickup > 6:
        refund_amount = (booking.base_amount + booking.tax_amount - booking.discount_amount) // 2
    else:
        raise HTTPException(
            400,
            "Cancellation within 6 hours of pickup. No refund applicable per policy."
        )

    # Cap at actual payment amount
    refund_amount = min(refund_amount, payment.amount)

    # ── Initiate Razorpay refund ──────────────────────────────────────
    rz = _razorpay()
    try:
        refund = rz.payment.refund(
            payment.gateway_payment_id,
            {
                "amount": refund_amount,
                "notes": {
                    "reason":     reason,
                    "booking_id": booking_id,
                    "initiated_by": actor.id,
                },
            },
        )
    except Exception as e:
        raise HTTPException(502, f"Refund gateway error: {str(e)}")

    # ── Update payment record ─────────────────────────────────────────
    payment.refund_id     = refund["id"]
    payment.refund_amount = refund_amount
    payment.refunded_at   = now
    # Status updated to REFUNDED via webhook (refund.processed)
    # Set optimistically here; webhook will confirm
    payment.status = PaymentStatus.REFUNDED

    return RefundResponse(
        refund_id=refund["id"],
        amount=refund_amount,
        status="processed",
        booking_id=booking_id,
    )
