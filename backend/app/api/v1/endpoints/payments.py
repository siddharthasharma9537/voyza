"""
app/api/v1/endpoints/payments.py
──────────────────────────────────
Payment endpoints.

POST /payments/create-order   — create Razorpay order (🔒 customer)
POST /payments/verify         — verify signature, confirm booking (🔒 customer)
POST /payments/webhook        — Razorpay webhook (no auth — signature verified)
POST /payments/refund         — initiate refund (🔒 customer or admin)
GET  /payments/{booking_id}   — payment status for a booking (🔒 auth)

Webhook endpoint MUST be excluded from CSRF protection and rate limiting
(Razorpay's servers make the requests).
"""

import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.models import User
from app.schemas.payments import (
    CreateOrderRequest,
    CreateOrderResponse,
    RefundRequest,
    RefundResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    body: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1 of payment flow.
    Creates a Razorpay order and returns credentials for the checkout widget.

    Flow:
        Client calls this → gets razorpay_order_id + key_id
        Client opens Razorpay checkout modal
        User pays → Razorpay calls /verify
    """
    return await payment_service.create_order(
        booking_id=body.booking_id,
        customer=current_user,
        db=db,
    )


@router.post("/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    body: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2 of payment flow.
    Called by the client after Razorpay checkout success callback.
    Verifies HMAC-SHA256 signature — NEVER trust this without verification.

    On success: Payment → CAPTURED, Booking → CONFIRMED.
    """
    return await payment_service.verify_payment(data=body, db=db)


@router.post("/webhook", include_in_schema=False)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Razorpay webhook endpoint.
    ⚠️  This endpoint has NO auth — Razorpay's servers call it directly.
    Security is provided entirely by HMAC signature verification inside the handler.

    Register this URL in Razorpay dashboard:
        https://your-domain.com/api/v1/payments/webhook

    Events handled:
        payment.captured  — backup confirmation
        payment.failed    — auto-cancel booking + free slot
        refund.processed  — update refund status
    """
    raw_body = await request.body()
    return await payment_service.handle_webhook(
        raw_body=raw_body,
        signature_header=x_razorpay_signature,
        db=db,
    )


@router.post("/refund", response_model=RefundResponse)
async def refund_payment(
    body: RefundRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate a refund for a booking.
    Refund amount is auto-calculated based on cancellation policy
    (unless admin provides explicit partial_amount override).
    """
    return await payment_service.process_refund(
        booking_id=body.booking_id,
        actor=current_user,
        reason=body.reason,
        partial_amount=body.amount,
        db=db,
    )


@router.get("/{booking_id}", response_model=list)
async def get_payment_status(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all payment records for a booking."""
    from sqlalchemy import select
    from app.models.models import Booking, Payment, UserRole
    from app.schemas.payments import PaymentStatusResponse

    # Authorization
    booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")

    is_authorized = (
        current_user.id == booking.customer_id
        or current_user.id == booking.owner_id
        or current_user.role == UserRole.ADMIN
    )
    if not is_authorized:
        raise HTTPException(403, "Not authorized")

    result = await db.execute(
        select(Payment)
        .where(Payment.booking_id == booking_id)
        .order_by(Payment.created_at.desc())
    )
    payments = result.scalars().all()
    return [PaymentStatusResponse.model_validate(p) for p in payments]
