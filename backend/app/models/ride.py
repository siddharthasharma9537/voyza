"""
app/models/ride.py
───────────────────
Ride / trip model — represents a real-time ride in progress.
Distinct from a Booking (which is the reservation); a Ride is created
when the driver starts the trip and closed when it ends.
"""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RideStatus(str, enum.Enum):
    REQUESTED = "requested"     # customer requested, looking for driver
    ACCEPTED = "accepted"       # driver accepted, en route to pickup
    DRIVER_ARRIVED = "driver_arrived"  # driver at pickup point
    IN_PROGRESS = "in_progress" # ride started
    COMPLETED = "completed"     # ride finished
    CANCELLED = "cancelled"     # cancelled before start


class Ride(Base):
    __tablename__ = "rides"
    __allow_unmapped__ = True

    # Linked booking (optional — ride can exist without pre-booking for instant rides)
    booking_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
    )

    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    driver_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
    )
    vehicle_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vehicles.id"),
        nullable=False,
    )

    # Route
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    pickup_longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)

    dropoff_address: Mapped[str] = mapped_column(Text, nullable=False)
    dropoff_latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    dropoff_longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)

    # Timing
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Fare
    estimated_fare: Mapped[int] = mapped_column(Integer, nullable=False)   # paise
    final_fare: Mapped[int | None] = mapped_column(Integer, nullable=True)  # paise
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[RideStatus] = mapped_column(
        Enum(RideStatus),
        default=RideStatus.REQUESTED,
        nullable=False,
    )

    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[str | None] = mapped_column(String(30), nullable=True)  # "customer" | "driver" | "system"

    # GPS breadcrumb trail stored as JSONB list of {lat, lng, ts}
    gps_trail: Mapped[list] = mapped_column(JSONB, default=list)

    # Relationships
    customer: "User" = relationship("User", foreign_keys=[customer_id])
    driver: "Driver" = relationship("Driver", back_populates="rides")
    vehicle: "Vehicle" = relationship("Vehicle")

    __table_args__ = (
        Index("ix_rides_customer_id", "customer_id"),
        Index("ix_rides_driver_id", "driver_id"),
        Index("ix_rides_vehicle_id", "vehicle_id"),
        Index("ix_rides_status", "status"),
        Index("ix_rides_booking_id", "booking_id"),
        CheckConstraint("estimated_fare > 0", name="ck_rides_fare_positive"),
    )
