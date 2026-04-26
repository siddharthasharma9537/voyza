"""
app/models/driver.py
─────────────────────
Driver profile — separate from the base User model.
A User with role DRIVER gets a linked Driver record that holds
license info, live location, and operational status.
"""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DriverStatus(str, enum.Enum):
    OFFLINE = "offline"       # not accepting rides
    AVAILABLE = "available"   # online, waiting for ride
    ON_RIDE = "on_ride"       # currently on a ride
    SUSPENDED = "suspended"   # admin-suspended


class LicenseClass(str, enum.Enum):
    LMV = "LMV"           # Light Motor Vehicle
    MCWOG = "MCWOG"       # Motorcycle Without Gear
    TRANS = "TRANS"       # Transport


class Driver(Base):
    __tablename__ = "drivers"
    __allow_unmapped__ = True

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # License
    license_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    license_class: Mapped[LicenseClass] = mapped_column(
        Enum(LicenseClass, values_callable=lambda x: [e.value for e in x], name="licenseclass"),
        nullable=False,
    )
    license_expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    license_doc_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Linked vehicle (the vehicle the driver currently operates)
    vehicle_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Operational
    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus, values_callable=lambda x: [e.value for e in x], name="driverstatus"),
        default=DriverStatus.OFFLINE,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    kyc_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Live location (updated via WebSocket)
    last_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    last_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    location_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Stats
    total_rides: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)

    # Relationships
    user: "User" = relationship("User", back_populates="driver_profile")
    vehicle: "Vehicle" = relationship("Vehicle")
    rides: list["Ride"] = relationship("Ride", back_populates="driver")

    __table_args__ = (
        Index("ix_drivers_user_id", "user_id"),
        Index("ix_drivers_status", "status"),
        Index("ix_drivers_vehicle_id", "vehicle_id"),
    )
