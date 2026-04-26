"""
app/schemas/refunds.py
──────────────────────
Request/response schemas for refund operations.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.models import RefundReason, RefundStatus


class RefundResponse(BaseModel):
    """Response schema for a single refund."""

    id: str
    booking_id: str
    payment_id: str | None = None

    initiated_by: str
    reason: RefundReason
    reason_text: str | None = None

    requested_amount: int
    approved_amount: int

    status: RefundStatus
    gateway_refund_id: str | None = None

    requested_at: datetime
    processed_at: datetime | None = None
    refunded_at: datetime | None = None

    notes: str | None = None
    failure_reason: str | None = None

    class Config:
        from_attributes = True


class RefundListResponse(BaseModel):
    """Response schema for customer's refund list."""

    id: str
    booking_id: str
    booking_reference: str
    vehicle_name: str
    cancellation_date: datetime
    refund_amount: int
    status: RefundStatus
    expected_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class CreateRefundRequest(BaseModel):
    """Request to create a refund for a cancelled booking."""

    booking_id: str
    reason: str = Field(..., min_length=5, max_length=500)
    initiated_by: str = "customer"  # customer, owner, admin


class RefundWebhookPayload(BaseModel):
    """Webhook payload from payment gateway for refund status updates."""

    refund_id: str
    payment_id: str
    amount: int
    status: str  # "processed" or "failed"
    error_message: str | None = None
    timestamp: datetime
