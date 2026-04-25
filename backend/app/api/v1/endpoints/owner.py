"""
app/api/v1/endpoints/owner.py
──────────────────────────────
All owner-facing API endpoints. Requires OWNER or ADMIN role.

/owner/cars              GET   — list own cars
/owner/cars              POST  — create car listing
/owner/cars/{id}         PATCH — update car
/owner/cars/{id}         DELETE
/owner/cars/{id}/submit  POST  — submit for admin review
/owner/cars/{id}/images  POST  — upload images
/owner/availability      POST  — block a slot
/owner/availability/{id} DELETE — unblock a slot
/owner/bookings          GET   — all bookings for owner's cars
/owner/bookings/{id}/accept POST
/owner/earnings          GET   — earnings summary
/owner/earnings/monthly  GET   — monthly breakdown
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_owner, get_current_user
from app.db.base import get_db
from app.models.models import User
from app.schemas.vehicles import VehicleCreateRequest, VehicleUpdateRequest
from app.schemas.owner import BlockSlotRequest, EarningsSummary
from app.services import owner_service

router = APIRouter(prefix="/owner", tags=["Owner"])

# Shorthand dep — must be OWNER or ADMIN
OwnerUser = Depends(get_current_owner)


# ═══════════════════════════════════════════════════════════════ CARS

@router.get("/cars")
async def list_my_cars(
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """List all cars belonging to the authenticated owner."""
    cars = await owner_service.get_owner_cars(owner.id, db)
    return [
        {
            "id":           c.id,
            "make":         c.make,
            "model":        c.model,
            "variant":      c.variant,
            "year":         c.year,
            "city":         c.city,
            "status":       c.status,
            "kyc_status":   c.kyc_status,
            "price_per_day": c.price_per_day,
            "price_per_hour": c.price_per_hour,
            "registration_number": c.registration_number,
            "images":       [{"url": img.url, "is_primary": img.is_primary} for img in c.images],
        }
        for c in cars
    ]


@router.post("/cars", status_code=status.HTTP_201_CREATED)
async def create_car(
    data: VehicleCreateRequest,
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """Create a new car listing (starts in DRAFT state)."""
    car = await owner_service.create_car(data, owner, db)
    return {"id": car.id, "status": car.status, "message": "Car created. Upload documents then submit for review."}


@router.patch("/cars/{car_id}")
async def update_car(
    car_id: str,
    data: VehicleUpdateRequest,
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """Update editable fields on a car listing."""
    car = await owner_service.update_car(car_id, data, owner, db)
    return {"id": car.id, "message": "Car updated successfully"}


@router.delete("/cars/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car(
    car_id: str,
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a car. Fails if active bookings exist."""
    await owner_service.delete_car(car_id, owner, db)


@router.post("/cars/{car_id}/submit")
async def submit_for_review(
    car_id: str,
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """Submit car DRAFT → PENDING for admin KYC/document review."""
    car = await owner_service.submit_car_for_review(car_id, owner, db)
    return {"id": car.id, "status": car.status, "message": "Submitted for review. Approval takes 24–48 hours."}


@router.post("/cars/{car_id}/images")
async def upload_car_image(
    car_id: str,
    file: UploadFile = File(...),
    is_primary: bool = False,
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a car image to S3 and store URL in CarImage table.
    Accepts: JPEG, PNG, WebP. Max 10MB.
    """
    # Validate content type
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(400, f"File type '{file.content_type}' not allowed. Use JPEG, PNG, or WebP.")

    # Validate file size (10MB max)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum size is 10MB.")

    # Verify car ownership
    from sqlalchemy import select
    from app.models.vehicle import Vehicle, VehicleImage
    car_result = await db.execute(
        select(Vehicle).where(Vehicle.id == car_id, Vehicle.owner_id == owner.id)
    )
    car = car_result.scalar_one_or_none()
    if not car:
        raise HTTPException(404, "Vehicle not found")

    # Upload to S3
    image_url = await _upload_to_s3(contents, file.filename, car_id)

    # If marking as primary, unset existing primary
    if is_primary:
        existing = await db.execute(
            select(VehicleImage).where(VehicleImage.vehicle_id == car_id, VehicleImage.is_primary.is_(True))
        )
        for img in existing.scalars().all():
            img.is_primary = False

    # Count existing images for sort_order
    count_result = await db.execute(
        select(VehicleImage).where(VehicleImage.vehicle_id == car_id)
    )
    sort_order = len(count_result.scalars().all())

    image = VehicleImage(vehicle_id=car_id, url=image_url, is_primary=is_primary, sort_order=sort_order)
    db.add(image)
    await db.flush()

    return {"id": image.id, "url": image_url, "is_primary": is_primary}


async def _upload_to_s3(contents: bytes, filename: str, car_id: str) -> str:
    """
    Upload file to S3-compatible storage and return public URL.
    Uses boto3 with settings from config.
    """
    import io
    import uuid
    import boto3
    from botocore.exceptions import ClientError
    from app.core.config import settings

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    key = f"cars/{car_id}/{uuid.uuid4()}.{ext}"

    s3_kwargs = dict(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
    )
    if settings.S3_ENDPOINT_URL:
        s3_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

    s3 = boto3.client("s3", **s3_kwargs)
    try:
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=io.BytesIO(contents),
            ContentType="image/jpeg",
            ACL="public-read",
        )
    except ClientError as e:
        raise HTTPException(500, f"Storage error: {e.response['Error']['Message']}")

    if settings.S3_ENDPOINT_URL:
        return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{key}"
    return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.S3_REGION}.amazonaws.com/{key}"


# ═══════════════════════════════════════════════════════════════ AVAILABILITY

@router.post("/availability", status_code=status.HTTP_201_CREATED)
async def block_slot(
    data: BlockSlotRequest,
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """Block a time slot on a car (vacation, maintenance, personal use)."""
    slot = await owner_service.block_slot(data, owner, db)
    return {
        "id":         slot.id,
        "vehicle_id": slot.vehicle_id,
        "start_time": slot.start_time.isoformat(),
        "end_time":   slot.end_time.isoformat(),
        "reason":     slot.reason,
    }


@router.delete("/availability/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_slot(
    slot_id: str,
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """Remove a manually-blocked slot."""
    await owner_service.unblock_slot(slot_id, owner, db)


# ═══════════════════════════════════════════════════════════════ BOOKINGS

@router.get("/bookings")
async def get_bookings(
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """All bookings across all owner's cars, newest first."""
    return await owner_service.get_owner_bookings(owner.id, db)


@router.post("/bookings/{booking_id}/accept")
async def accept_booking(
    booking_id: str,
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """Accept a pending booking (for non-instant-booking mode)."""
    booking = await owner_service.accept_booking(booking_id, owner, db)
    return {"id": booking.id, "status": booking.status}


# ═══════════════════════════════════════════════════════════════ EARNINGS

@router.get("/earnings", response_model=EarningsSummary)
async def get_earnings(
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """Full earnings summary — lifetime, this month, last month, pending."""
    return await owner_service.get_earnings(owner.id, db)


@router.get("/earnings/monthly")
async def get_monthly_earnings(
    months: int = 6,
    owner: User = OwnerUser,
    db: AsyncSession = Depends(get_db),
):
    """Month-by-month earnings breakdown (for the earnings chart)."""
    return await owner_service.get_monthly_earnings(owner.id, db, months=months)
