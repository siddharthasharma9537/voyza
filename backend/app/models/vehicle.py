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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class KYCStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class VehicleStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class FuelType(str, enum.Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    CNG = "cng"


class Transmission(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"


class Vehicle(Base):
    __tablename__ = "vehicles"
    __allow_unmapped__ = True

    owner_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    make: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    variant: Mapped[str | None] = mapped_column(String(80), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(String(40), nullable=False)
    seating: Mapped[int] = mapped_column(Integer, nullable=False)
    fuel_type: Mapped[FuelType] = mapped_column(
        Enum(FuelType, values_callable=lambda x: [e.value for e in x], name="fueltype"),
        nullable=False,
    )
    transmission: Mapped[Transmission] = mapped_column(
        Enum(Transmission, values_callable=lambda x: [e.value for e in x], name="transmissiontype"),
        nullable=False,
    )
    mileage_kmpl: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    price_per_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    security_deposit: Mapped[int] = mapped_column(Integer, default=0)

    registration_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    rc_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    insurance_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    insurance_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, values_callable=lambda x: [e.value for e in x], name="vehiclestatus"),
        default=VehicleStatus.DRAFT,
        nullable=False,
    )
    kyc_status: Mapped[KYCStatus] = mapped_column(
        Enum(KYCStatus, values_callable=lambda x: [e.value for e in x], name="kycstatus"),
        default=KYCStatus.PENDING,
        nullable=False,
    )
    kyc_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    features: Mapped[dict] = mapped_column(JSONB, default=dict)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: "User" = relationship("User", back_populates="cars")
    images: list["VehicleImage"] = relationship("VehicleImage", back_populates="vehicle", cascade="all, delete-orphan")
    bookings: list["Booking"] = relationship("Booking", back_populates="vehicle")
    availability: list["Availability"] = relationship(
        "Availability",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )
    reviews: list["Review"] = relationship("Review", back_populates="vehicle")

    __table_args__ = (
        Index("ix_vehicles_owner_id", "owner_id"),
        Index("ix_vehicles_city_status", "city", "status"),
        Index("ix_vehicles_fuel_transmission", "fuel_type", "transmission"),
        CheckConstraint("price_per_hour > 0", name="ck_vehicles_price_per_hour_positive"),
        CheckConstraint("price_per_day > 0", name="ck_vehicles_price_per_day_positive"),
        CheckConstraint("year >= 2000 AND year <= 2035", name="ck_vehicles_year_range"),
    )


class VehicleImage(Base):
    __allow_unmapped__ = True
    __tablename__ = "vehicle_images"

    vehicle_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    vehicle: "Vehicle" = relationship("Vehicle", back_populates="images")

    __table_args__ = (
        Index("ix_vehicle_images_vehicle_id", "vehicle_id"),
    )


class Availability(Base):
    __allow_unmapped__ = True
    __tablename__ = "availability"

    vehicle_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(30), default="blocked")
    booking_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("bookings.id"),
        nullable=True,
    )

    vehicle: "Vehicle" = relationship("Vehicle", back_populates="availability")

    __table_args__ = (
        Index("ix_availability_vehicle_time", "vehicle_id", "start_time", "end_time"),
        CheckConstraint("end_time > start_time", name="ck_availability_time_order"),
    )
