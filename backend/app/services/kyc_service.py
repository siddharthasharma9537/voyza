"""
app/services/kyc_service.py
────────────────────────────
KYC (Know Your Customer) verification and document management.

Handles:
- Document uploads (Driving License, Aadhar, Selfie, Vehicle RC, Insurance)
- Document verification workflow
- Damage report creation and tracking
- Document expiry checking
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    DamageReport,
    DamageReportStatus,
    DamageType,
    DocumentStatus,
    DocumentType,
    KYCDocument,
    User,
)


# ── Document type requirements ─────────────────────────────────────────────────

DOCUMENT_REQUIREMENTS = {
    DocumentType.DRIVING_LICENSE: {
        "max_size_mb": 10,
        "allowed_types": ["image/jpeg", "image/png", "application/pdf"],
        "required_for": ["customer"],  # Required for customers
        "expiry_required": True,
    },
    DocumentType.AADHAR: {
        "max_size_mb": 10,
        "allowed_types": ["image/jpeg", "image/png", "application/pdf"],
        "required_for": ["customer"],
        "expiry_required": False,
    },
    DocumentType.SELFIE: {
        "max_size_mb": 5,
        "allowed_types": ["image/jpeg", "image/png"],
        "required_for": ["customer"],
        "expiry_required": False,
    },
    DocumentType.VEHICLE_RC: {
        "max_size_mb": 10,
        "allowed_types": ["image/jpeg", "image/png", "application/pdf"],
        "required_for": ["owner"],
        "expiry_required": False,
    },
    DocumentType.VEHICLE_INSURANCE: {
        "max_size_mb": 10,
        "allowed_types": ["image/jpeg", "image/png", "application/pdf"],
        "required_for": ["owner"],
        "expiry_required": True,
    },
}


# ── Create KYC document record ─────────────────────────────────────────────────

async def create_kyc_document(
    user_id: str,
    document_type: DocumentType,
    file_url: str,
    file_name: str,
    mime_type: str,
    file_size: int,
    document_number: str | None = None,
    expiry_date: datetime | None = None,
    db: AsyncSession | None = None,
) -> KYCDocument:
    """
    Create a KYC document record after file upload to S3.

    Called by upload endpoint after file is stored in S3.
    Document starts in PENDING status, awaiting admin verification.
    """
    # Validate document type exists
    if document_type not in DocumentType:
        raise HTTPException(400, f"Invalid document type: {document_type}")

    # Validate file size
    requirements = DOCUMENT_REQUIREMENTS.get(document_type, {})
    max_size = requirements.get("max_size_mb", 10) * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(400, f"File too large. Maximum size is {requirements.get('max_size_mb')}MB")

    # Validate MIME type
    allowed_types = requirements.get("allowed_types", [])
    if mime_type not in allowed_types:
        raise HTTPException(400, f"File type not allowed. Allowed types: {', '.join(allowed_types)}")

    # Create document record
    doc = KYCDocument(
        user_id=user_id,
        document_type=document_type,
        file_url=file_url,
        file_name=file_name,
        mime_type=mime_type,
        file_size=file_size,
        document_number=document_number,
        expiry_date=expiry_date,
        status=DocumentStatus.PENDING,
        uploaded_at=datetime.now(timezone.utc),
    )

    if db:
        db.add(doc)
        await db.flush()

    return doc


# ── Verify document (admin action) ─────────────────────────────────────────────

async def verify_document(
    document_id: str,
    verified_by_id: str,
    notes: str | None = None,
    db: AsyncSession = None,
) -> KYCDocument:
    """
    Approve a document after manual or automated verification.
    Only admins can call this.
    """
    result = await db.execute(
        select(KYCDocument).where(KYCDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(404, "Document not found")

    doc.status = DocumentStatus.VERIFIED
    doc.verified_by = verified_by_id
    doc.verified_at = datetime.now(timezone.utc)
    doc.verification_notes = notes

    return doc


# ── Reject document (admin action) ─────────────────────────────────────────────

async def reject_document(
    document_id: str,
    verified_by_id: str,
    rejection_reason: str,
    db: AsyncSession = None,
) -> KYCDocument:
    """
    Reject a document with reason. User must resubmit.
    Only admins can call this.
    """
    result = await db.execute(
        select(KYCDocument).where(KYCDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(404, "Document not found")

    doc.status = DocumentStatus.REJECTED
    doc.verified_by = verified_by_id
    doc.verified_at = datetime.now(timezone.utc)
    doc.rejection_reason = rejection_reason

    return doc


# ── Get user's documents ───────────────────────────────────────────────────────

async def get_user_documents(user_id: str, db: AsyncSession) -> list[dict]:
    """Fetch all KYC documents for a user."""
    result = await db.execute(
        select(KYCDocument)
        .where(KYCDocument.user_id == user_id)
        .order_by(KYCDocument.uploaded_at.desc())
    )
    docs = result.scalars().all()

    return [
        {
            "id": doc.id,
            "type": doc.document_type.value,
            "status": doc.status.value,
            "file_name": doc.file_name,
            "file_url": doc.file_url,
            "document_number": doc.document_number,
            "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
            "verified_at": doc.verified_at.isoformat() if doc.verified_at else None,
            "rejection_reason": doc.rejection_reason,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in docs
    ]


# ── Get all documents (admin) ──────────────────────────────────────────────────

async def get_all_documents(db: AsyncSession) -> list[dict]:
    """Fetch all KYC documents (admin only)."""
    result = await db.execute(
        select(KYCDocument)
        .order_by(KYCDocument.uploaded_at.desc())
    )
    docs = result.scalars().all()

    return [
        {
            "id": doc.id,
            "user_id": doc.user_id,
            "type": doc.document_type.value,
            "status": doc.status.value,
            "file_name": doc.file_name,
            "file_url": doc.file_url,
            "document_number": doc.document_number,
            "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
            "verified_at": doc.verified_at.isoformat() if doc.verified_at else None,
            "rejection_reason": doc.rejection_reason,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in docs
    ]


# ── Get pending documents (admin) ──────────────────────────────────────────────

async def get_pending_documents(db: AsyncSession) -> list[dict]:
    """Fetch all pending KYC documents (admin only)."""
    result = await db.execute(
        select(KYCDocument)
        .where(KYCDocument.status == DocumentStatus.PENDING)
        .order_by(KYCDocument.uploaded_at.asc())
    )
    docs = result.scalars().all()

    return [
        {
            "id": doc.id,
            "user_id": doc.user_id,
            "type": doc.document_type.value,
            "status": doc.status.value,
            "file_name": doc.file_name,
            "file_url": doc.file_url,
            "document_number": doc.document_number,
            "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in docs
    ]


# ── Check if user is KYC verified ──────────────────────────────────────────────

async def is_user_kyc_verified(user_id: str, db: AsyncSession) -> bool:
    """
    Check if user has verified all required documents.
    For customers: needs DL (or Aadhar) + Selfie
    For owners: needs RC + Insurance + maybe DL
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        return False

    # Get all verified documents (excluding expired ones)
    docs_result = await db.execute(
        select(KYCDocument).where(
            and_(
                KYCDocument.user_id == user_id,
                KYCDocument.status == DocumentStatus.VERIFIED,
            )
        )
    )
    verified_docs = docs_result.scalars().all()

    # Filter out expired documents
    verified_types = set()
    for doc in verified_docs:
        # Check if document has expiry date and if it's expired
        if doc.expiry_date and doc.expiry_date < datetime.now(timezone.utc):
            # Document is expired, don't count it
            continue
        verified_types.add(doc.document_type)

    # Check requirements based on role
    if user.role == UserRole.CUSTOMER:
        # Customers need: DL or Aadhar + Selfie
        has_id = DocumentType.DRIVING_LICENSE in verified_types or DocumentType.AADHAR in verified_types
        has_selfie = DocumentType.SELFIE in verified_types
        return has_id and has_selfie
    elif user.role == UserRole.OWNER:
        # Owners need: RC + Insurance + DL
        has_rc = DocumentType.VEHICLE_RC in verified_types
        has_insurance = DocumentType.VEHICLE_INSURANCE in verified_types
        has_dl = DocumentType.DRIVING_LICENSE in verified_types
        return has_rc and has_insurance and has_dl

    return False


# ── Damage Report ──────────────────────────────────────────────────────────────

async def create_damage_report(
    booking_id: str,
    reported_by: str,  # "customer" or "owner"
    damage_type: DamageType,
    description: str,
    damage_photos: list[str],  # S3 URLs
    estimated_cost: int | None,
    db: AsyncSession,
) -> DamageReport:
    """
    Create a damage report for a booking.
    Can be reported by customer (after return) or owner (after customer returns).
    """
    report = DamageReport(
        booking_id=booking_id,
        reported_by=reported_by,
        damage_type=damage_type,
        description=description,
        damage_photos=damage_photos,
        estimated_cost=estimated_cost,
        status=DamageReportStatus.REPORTED,
        reported_at=datetime.now(timezone.utc),
    )
    db.add(report)
    await db.flush()

    return report


# ── Resolve damage report ──────────────────────────────────────────────────────

async def resolve_damage_report(
    report_id: str,
    resolved_by_id: str,
    resolution_notes: str,
    compensation_amount: int | None = None,
    db: AsyncSession = None,
) -> DamageReport:
    """
    Resolve a damage report with compensation if applicable.
    Admin action only.
    """
    result = await db.execute(
        select(DamageReport).where(DamageReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(404, "Damage report not found")

    report.status = DamageReportStatus.RESOLVED
    report.resolved_by = resolved_by_id
    report.resolved_at = datetime.now(timezone.utc)
    report.resolution_notes = resolution_notes
    report.compensation_amount = compensation_amount

    return report


# ── Get damage reports for booking ─────────────────────────────────────────────

async def get_booking_damage_reports(booking_id: str, db: AsyncSession) -> list[dict]:
    """Get all damage reports for a booking."""
    result = await db.execute(
        select(DamageReport)
        .where(DamageReport.booking_id == booking_id)
        .order_by(DamageReport.reported_at.desc())
    )
    reports = result.scalars().all()

    return [
        {
            "id": report.id,
            "reported_by": report.reported_by,
            "damage_type": report.damage_type.value,
            "description": report.description,
            "damage_photos": report.damage_photos,
            "estimated_cost": report.estimated_cost,
            "status": report.status.value,
            "resolution_notes": report.resolution_notes,
            "compensation_amount": report.compensation_amount,
            "reported_at": report.reported_at.isoformat(),
            "resolved_at": report.resolved_at.isoformat() if report.resolved_at else None,
        }
        for report in reports
    ]
