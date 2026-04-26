from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentGateway(str, enum.Enum):
    RAZORPAY = "razorpay"
    STRIPE = "stripe"


class Payment(Base):
    __allow_unmapped__ = True
    __tablename__ = "payments"

    booking_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
    )

    gateway: Mapped[PaymentGateway] = mapped_column(
        Enum(PaymentGateway, values_callable=lambda x: [e.value for e in x], name="paymentgateway"),
        nullable=False,
    )
    gateway_order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    gateway_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gateway_signature: Mapped[str | None] = mapped_column(String(500), nullable=True)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, values_callable=lambda x: [e.value for e in x], name="paymentstatus"),
        default=PaymentStatus.CREATED,
        nullable=False,
    )

    refund_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_amount: Mapped[int] = mapped_column(Integer, default=0)

    gateway_response: Mapped[dict] = mapped_column(JSONB, default=dict)

    booking: "Booking" = relationship("Booking", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_booking_id", "booking_id"),
        Index("ix_payments_gateway_order_id", "gateway_order_id"),
        UniqueConstraint("gateway_payment_id", name="uq_payments_gateway_payment_id"),
    )
