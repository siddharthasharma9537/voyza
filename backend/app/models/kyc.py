"""
app/models/kyc.py
─────────────────
KYC (Know Your Customer) and identity verification models.

Documents tracked:
- Driving License (customer identity & driving authorization)
- Aadhar (government ID for customer)
- Selfie (live face verification for anti-fraud)
- Vehicle RC (for owners listing vehicles)
- Vehicle Insurance (for owners)
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentType(str, enum.Enum):
    DRIVING_LICENSE = "driving_license"
    AADHAR = "aadhar"
    SELFIE = "selfie"
    VEHICLE_RC = "vehicle_rc"
    VEHICLE_INSURANCE = "vehicle_insurance"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"          # Uploaded, awaiting review
    VERIFIED = "verified"        # Admin approved
    REJECTED = "rejected"        # Did not meet requirements
    EXPIRED = "expired"          # Document expired
    REQUIRES_RESUBMISSION = "requires_resubmission"


class KYCDocument(Base):
    __tablename__ = "kyc_documents"
    __allow_unmapped__ = True

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, values_callable=lambda x: [e.value for e in x], name="documenttype"),
        nullable=False,
    )

    # Document storage
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)  # S3 URL
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)  # in bytes

    # Verification
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, values_callable=lambda x: [e.value for e in x], name="documentstatus"),
        default=DocumentStatus.PENDING,
        nullable=False,
    )

    # For ID documents (DL, Aadhar)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)  # DL number, Aadhar last 4 digits
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Verification details
    verified_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timeline
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user: "User" = relationship("User", back_populates="kyc_documents", foreign_keys=[user_id])
    verified_by_user: "User" = relationship("User", foreign_keys=[verified_by])

    __table_args__ = (
        Index("ix_kyc_documents_user_id", "user_id"),
        Index("ix_kyc_documents_type", "document_type"),
        Index("ix_kyc_documents_status", "status"),
        Index("ix_kyc_documents_user_type", "user_id", "document_type"),
    )


# ── Damage Report ──────────────────────────────────────────────────────────────

class DamageType(str, enum.Enum):
    SCRATCH = "scratch"
    DENT = "dent"
    BROKEN_GLASS = "broken_glass"
    TIRE_DAMAGE = "tire_damage"
    INTERIOR_DAMAGE = "interior_damage"
    ENGINE_DAMAGE = "engine_damage"
    MAJOR_ACCIDENT = "major_accident"
    OTHER = "other"


class DamageReportStatus(str, enum.Enum):
    REPORTED = "reported"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISPUTED = "disputed"
    COMPENSATION_PENDING = "compensation_pending"
    CLOSED = "closed"


class DamageReport(Base):
    __tablename__ = "damage_reports"
    __allow_unmapped__ = True

    booking_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
    )

    reported_by: Mapped[str] = mapped_column(String(30), nullable=False)  # "customer" or "owner"
    damage_type: Mapped[DamageType] = mapped_column(
        Enum(DamageType, values_callable=lambda x: [e.value for e in x], name="damagetype"),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)
    damage_photos: Mapped[list[str]] = mapped_column(default=list)  # JSON array of S3 URLs
    estimated_cost: Mapped[int] = mapped_column(nullable=True)  # in paise

    status: Mapped[DamageReportStatus] = mapped_column(
        Enum(DamageReportStatus, values_callable=lambda x: [e.value for e in x], name="damagereportstatus"),
        default=DamageReportStatus.REPORTED,
        nullable=False,
    )

    # Resolution
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Compensation
    compensation_amount: Mapped[int | None] = mapped_column(nullable=True)  # in paise
    compensation_paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timeline
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    booking: "Booking" = relationship("Booking", back_populates="damage_reports")
    resolved_by_user: "User" = relationship("User", foreign_keys=[resolved_by])

    __table_args__ = (
        Index("ix_damage_reports_booking_id", "booking_id"),
        Index("ix_damage_reports_status", "status"),
        Index("ix_damage_reports_reported_by", "reported_by"),
    )
