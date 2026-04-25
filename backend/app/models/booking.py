from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class Booking(Base):
    __tablename__ = "bookings"
    __allow_unmapped__ = True

    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vehicles.id"), nullable=False)
    owner_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    pickup_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dropoff_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    pickup_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    pickup_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    pickup_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)

    base_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    tax_amount: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    security_deposit: Mapped[int] = mapped_column(Integer, default=0)
    promo_code: Mapped[str | None] = mapped_column(String(30), nullable=True)

    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)

    odometer_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    odometer_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    cancelled_by: Mapped[str | None] = mapped_column(String(30), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: "User" = relationship("User", back_populates="bookings", foreign_keys=[customer_id])
    vehicle: "Vehicle" = relationship("Vehicle", back_populates="bookings")
    payments: list["Payment"] = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    review: "Review | None" = relationship("Review", back_populates="booking", uselist=False)

    __table_args__ = (
        Index("ix_bookings_customer_id", "customer_id"),
        Index("ix_bookings_vehicle_id", "vehicle_id"),
        Index("ix_bookings_owner_id", "owner_id"),
        Index("ix_bookings_status", "status"),
        Index("ix_bookings_pickup_dropoff", "vehicle_id", "pickup_time", "dropoff_time"),
        CheckConstraint("dropoff_time > pickup_time", name="ck_bookings_time_order"),
        CheckConstraint("total_amount >= 0", name="ck_bookings_total_positive"),
    )


class Review(Base):
    __tablename__ = "reviews"
    __allow_unmapped__ = True

    booking_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("bookings.id"), unique=True, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vehicles.id"), nullable=False)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_reply: Mapped[str | None] = mapped_column(Text, nullable=True)

    booking: "Booking" = relationship("Booking", back_populates="review")
    reviewer: "User" = relationship("User", back_populates="reviews_given", foreign_keys=[reviewer_id])
    vehicle: "Vehicle" = relationship("Vehicle", back_populates="reviews")

    __table_args__ = (
        Index("ix_reviews_vehicle_id", "vehicle_id"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )
