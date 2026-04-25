"""
app/schemas/payments.py
────────────────────────
Pydantic v2 schemas for the full payment lifecycle:
  create order → client pays → verify → webhook → refund
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ── Order creation ─────────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    """Customer requests a Razorpay order for a pending booking."""
    booking_id: str


class CreateOrderResponse(BaseModel):
    """Returned to the client — used to open Razorpay checkout."""
    razorpay_order_id: str
    amount:            int     # paise
    currency:          str     # "INR"
    booking_id:        str
    key_id:            str     # Razorpay public key — safe to expose


# ── Payment verification (client-side callback) ────────────────────────────────

class VerifyPaymentRequest(BaseModel):
    """
    After Razorpay checkout succeeds, the client receives these three values
    and POSTs them here. We verify the HMAC signature before confirming.
    """
    razorpay_order_id:   str
    razorpay_payment_id: str
    razorpay_signature:  str
    booking_id:          str


class VerifyPaymentResponse(BaseModel):
    success:    bool
    booking_id: str
    status:     str   # "confirmed" | "failed"
    message:    str


# ── Webhook ────────────────────────────────────────────────────────────────────

class RazorpayWebhookEvent(BaseModel):
    """
    Razorpay sends signed webhook events for async payment state changes.
    We handle: payment.captured, payment.failed, refund.processed
    Raw payload stored in Payment.gateway_response for auditability.
    """
    event:  str
    payload: dict


# ── Refund ─────────────────────────────────────────────────────────────────────

class RefundRequest(BaseModel):
    booking_id: str
    reason:     str = Field(default="customer_request", max_length=200)
    amount:     int | None = Field(
        default=None, gt=0,
        description="Partial refund amount in paise. If None, full refund."
    )


class RefundResponse(BaseModel):
    refund_id:  str
    amount:     int     # paise refunded
    status:     str
    booking_id: str


# ── Payment status ─────────────────────────────────────────────────────────────

class PaymentStatusResponse(BaseModel):
    id:                  str
    booking_id:          str
    gateway:             str
    gateway_order_id:    str
    gateway_payment_id:  str | None
    amount:              int
    currency:            str
    status:              str
    refund_amount:       int
    created_at:          datetime

    model_config = {"from_attributes": True}
