"""
app/models/refund.py
────────────────────
Refund model for tracking booking cancellations and refund processing.

Refund lifecycle:
  1. Booking cancelled → Refund created (PENDING)
  2. Payment gateway called → Refund status INITIATED
  3. Webhook received → Refund status PROCESSED or FAILED
  4. Completed or dispute resolved
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RefundStatus(str, enum.Enum):
    PENDING = "pending"        # Refund created, awaiting processing
    INITIATED = "initiated"     # API call sent to payment gateway
    PROCESSED = "processed"     # Successfully refunded
    FAILED = "failed"           # Refund failed — may require manual intervention
    DISPUTED = "disputed"       # Under dispute / investigation


class RefundReason(str, enum.Enum):
    CUSTOMER_CANCELLATION = "customer_cancellation"
    OWNER_CANCELLATION = "owner_cancellation"
    ADMIN_CANCELLATION = "admin_cancellation"
    PAYMENT_FAILED = "payment_failed"
    REFUND_REQUEST = "refund_request"
    PARTIAL_REFUND = "partial_refund"
    OTHER = "other"


class Refund(Base):
    __tablename__ = "refunds"
    __allow_unmapped__ = True

    booking_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
    )

    payment_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Who initiated the refund
    initiated_by: Mapped[str] = mapped_column(String(30), nullable=False)  # "customer", "owner", "admin"

    reason: Mapped[RefundReason] = mapped_column(
        Enum(RefundReason, values_callable=lambda x: [e.value for e in x], name="refundreason"),
        nullable=False,
    )

    reason_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Amount to refund (in paise)
    requested_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Initial refund request
    approved_amount: Mapped[int] = mapped_column(Integer, nullable=False)    # Actual amount after policy check

    # Gateway tracking
    status: Mapped[RefundStatus] = mapped_column(
        Enum(RefundStatus, values_callable=lambda x: [e.value for e in x], name="refundstatus"),
        default=RefundStatus.PENDING,
        nullable=False,
    )

    gateway_refund_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timeline
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Additional notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    booking: "Booking" = relationship("Booking", back_populates="refunds")
    payment: "Payment" = relationship("Payment", back_populates="refunds")

    __table_args__ = (
        Index("ix_refunds_booking_id", "booking_id"),
        Index("ix_refunds_payment_id", "payment_id"),
        Index("ix_refunds_status", "status"),
        Index("ix_refunds_requested_at", "requested_at"),
    )
