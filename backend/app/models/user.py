from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    OWNER = "owner"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    __allow_unmapped__ = True

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            values_callable=lambda x: [e.value for e in x],
            name="userrole",
        ),
        default=UserRole.CUSTOMER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    licence_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    licence_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cars: list["Vehicle"] = relationship("Vehicle", back_populates="owner")
    bookings: list["Booking"] = relationship(
        "Booking",
        back_populates="customer",
        foreign_keys="Booking.customer_id",
    )
    reviews_given: list["Review"] = relationship(
        "Review",
        back_populates="reviewer",
        foreign_keys="Review.reviewer_id",
    )
    refresh_tokens: list["RefreshToken"] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notifications: list["Notification"] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    kyc_documents: list["KYCDocument"] = relationship(
        "KYCDocument",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    driver_profile: "Driver" = relationship("Driver", back_populates="user", uselist=False)

    __table_args__ = (
        Index("ix_users_phone", "phone"),
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
    )


class RefreshToken(Base):
    __allow_unmapped__ = True
    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    device_info: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: "User" = relationship("User", back_populates="refresh_tokens")


class OTPCode(Base):
    __allow_unmapped__ = True
    __tablename__ = "otp_codes"

    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)

    __table_args__ = (
        Index("ix_otp_phone_expires", "phone", "expires_at"),
    )
