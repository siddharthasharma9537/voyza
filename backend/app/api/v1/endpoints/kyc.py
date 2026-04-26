"""
app/api/v1/endpoints/kyc.py
──────────────────────────
KYC (Know Your Customer) verification endpoints.

POST /kyc/documents               — Upload document (customer/owner)
GET  /kyc/documents               — List user's documents
GET  /kyc/documents/{id}          — Get document details
POST /kyc/verify-status           — Check if user is KYC verified

POST /damage-reports              — Report vehicle damage
GET  /damage-reports/{booking_id} — Get damage reports for booking
POST /damage-reports/{id}/resolve — Resolve damage report (admin)
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.models import DamageType, DocumentType, User, UserRole
from app.services import kyc_service
from app.services.s3_service import get_s3_service

router = APIRouter(prefix="/kyc", tags=["KYC"])


# ═══════════════════════════════════════════════════════════════ DOCUMENTS

@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    document_number: str | None = Form(None),
    expiry_date: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a KYC document (DL, Aadhar, Selfie, etc).
    File is uploaded to S3, then KYCDocument record created.
    """
    # Validate document type
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(400, f"Invalid document type: {document_type}")

    # Read file
    contents = await file.read()
    file_size = len(contents)

    # Upload to S3
    s3_service = get_s3_service()
    try:
        s3_url = await s3_service.upload_file(
            file_content=contents,
            file_name=file.filename or "document",
            user_id=current_user.id,
            document_type=doc_type.value,
            content_type=file.content_type or "application/octet-stream",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, f"Failed to upload document: {str(e)}")

    # Parse expiry date if provided
    from datetime import datetime
    expiry = None
    if expiry_date:
        try:
            expiry = datetime.fromisoformat(expiry_date)
        except ValueError:
            raise HTTPException(400, "Invalid expiry_date format. Use ISO 8601.")

    # Create document record
    doc = await kyc_service.create_kyc_document(
        user_id=current_user.id,
        document_type=doc_type,
        file_url=s3_url,
        file_name=file.filename or "document",
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        document_number=document_number,
        expiry_date=expiry,
        db=db,
    )

    await db.commit()

    return {
        "id": doc.id,
        "type": doc.document_type.value,
        "status": "pending",
        "message": "Document uploaded. Awaiting verification.",
    }


@router.get("/documents")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all KYC documents for the current user, or all documents if admin."""
    # Admins can view all documents
    if current_user.role == UserRole.ADMIN:
        return await kyc_service.get_all_documents(db)

    # Regular users see only their own
    return await kyc_service.get_user_documents(current_user.id, db)


@router.get("/documents/pending")
async def list_pending_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all pending KYC documents (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(403, "Only admins can view pending documents")

    return await kyc_service.get_pending_documents(db)


@router.get("/verify-status")
async def check_verification_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if user is KYC verified."""
    is_verified = await kyc_service.is_user_kyc_verified(current_user.id, db)
    return {
        "verified": is_verified,
        "user_id": current_user.id,
        "role": current_user.role,
    }


@router.post("/documents/{document_id}/verify", status_code=status.HTTP_200_OK)
async def verify_kyc_document(
    document_id: str,
    body: dict,  # {notes: str (optional)}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify a KYC document (admin only)."""
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(403, "Only admins can verify documents")

    doc = await kyc_service.verify_document(
        document_id=document_id,
        verified_by_id=current_user.id,
        notes=body.get("notes"),
        db=db,
    )

    await db.commit()
    return {
        "id": doc.id,
        "type": doc.document_type.value,
        "status": "verified",
        "message": "Document verified successfully.",
    }


@router.post("/documents/{document_id}/reject", status_code=status.HTTP_200_OK)
async def reject_kyc_document(
    document_id: str,
    body: dict,  # {rejection_reason: str}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a KYC document with reason (admin only)."""
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(403, "Only admins can reject documents")

    rejection_reason = body.get("rejection_reason")
    if not rejection_reason:
        raise HTTPException(400, "rejection_reason is required")

    doc = await kyc_service.reject_document(
        document_id=document_id,
        verified_by_id=current_user.id,
        rejection_reason=rejection_reason,
        db=db,
    )

    await db.commit()
    return {
        "id": doc.id,
        "type": doc.document_type.value,
        "status": "rejected",
        "message": "Document rejected. User will be notified to resubmit.",
    }


# ═══════════════════════════════════════════════════════════════ DAMAGE REPORTS

@router.post("/damage-reports", status_code=status.HTTP_201_CREATED)
async def create_damage_report(
    body: dict,  # {booking_id, damage_type, description, damage_photos, estimated_cost}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Report vehicle damage after a rental."""
    from app.models.models import Booking, BookingStatus

    booking_id = body.get("booking_id")
    if not booking_id:
        raise HTTPException(400, "booking_id is required")

    # Get booking
    from sqlalchemy import select
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise HTTPException(404, "Booking not found")

    # Verify authorization (customer or owner only)
    is_customer = booking.customer_id == current_user.id
    is_owner = booking.owner_id == current_user.id

    if not (is_customer or is_owner):
        raise HTTPException(403, "Not authorized to report damage on this booking")

    # Validate damage type
    try:
        damage_type = DamageType(body.get("damage_type", "other"))
    except ValueError:
        raise HTTPException(400, f"Invalid damage_type: {body.get('damage_type')}")

    # Create report
    report = await kyc_service.create_damage_report(
        booking_id=booking_id,
        reported_by="customer" if is_customer else "owner",
        damage_type=damage_type,
        description=body.get("description", ""),
        damage_photos=body.get("damage_photos", []),
        estimated_cost=body.get("estimated_cost"),
        db=db,
    )

    await db.commit()

    return {
        "id": report.id,
        "booking_id": report.booking_id,
        "status": report.status.value,
        "message": "Damage report submitted. Admin will review shortly.",
    }


@router.get("/damage-reports/{booking_id}")
async def get_damage_reports(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get damage reports for a booking (authorized parties only)."""
    from sqlalchemy import select
    from app.models.models import Booking

    # Verify authorization
    booking_result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise HTTPException(404, "Booking not found")

    is_customer = booking.customer_id == current_user.id
    is_owner = booking.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    if not (is_customer or is_owner or is_admin):
        raise HTTPException(403, "Not authorized to view damage reports")

    return await kyc_service.get_booking_damage_reports(booking_id, db)
