"""
app/api/v1/endpoints/admin.py
──────────────────────────────
All admin-only endpoints. Every route requires UserRole.ADMIN.

/admin/kyc                      GET  — KYC queue
/admin/kyc/review               POST — approve / reject car
/admin/users                    GET  — paginated user list
/admin/users/{id}/toggle-status POST — suspend / reactivate
/admin/bookings                 GET  — all bookings (paginated)
/admin/bookings/{id}            GET  — single booking detail
/admin/bookings/{id}/dispute    POST — mark booking as disputed
/admin/disputes                 GET  — disputed bookings
/admin/disputes/resolve         POST — resolve dispute + optional refund
/admin/analytics                GET  — platform analytics snapshot
/admin/analytics/monthly        GET  — monthly breakdown
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin
from app.db.base import get_db
from app.models.models import User
from app.schemas.admin import (
    DisputeResolveRequest,
    KYCReviewRequest,
    PlatformAnalytics,
    ToggleUserRequest,
)
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])
AdminUser = Depends(get_current_admin)


# ═══════════════════════════════════════════════════════════════ KYC

@router.get("/kyc")
async def kyc_queue(
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """All cars pending KYC review, oldest first (FIFO)."""
    return await admin_service.get_kyc_queue(db)


@router.post("/kyc/review")
async def review_kyc(
    data: KYCReviewRequest,
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a car's KYC submission."""
    return await admin_service.review_kyc(data, admin, db)


# ═══════════════════════════════════════════════════════════════ USERS

@router.get("/users")
async def list_users(
    role:   str | None = Query(None, pattern="^(customer|owner|admin)$"),
    search: str | None = Query(None, min_length=2),
    page:   int        = Query(1, ge=1),
    limit:  int        = Query(50, ge=1, le=200),
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Paginated user list with optional role filter and search."""
    return await admin_service.list_users(db, role=role, search=search, page=page, limit=limit)


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    data: ToggleUserRequest,
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Suspend or reactivate a user. Cannot suspend other admins."""
    return await admin_service.toggle_user_status(user_id, data.is_active, data.reason, db)


# ═══════════════════════════════════════════════════════════════ BOOKINGS

@router.get("/bookings")
async def list_all_bookings(
    status: str | None = Query(None),
    city:   str | None = Query(None),
    page:   int        = Query(1, ge=1),
    limit:  int        = Query(50, ge=1, le=200),
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """All platform bookings with optional filters."""
    from sqlalchemy import select
    from app.models.models import Booking, Car, User as UserModel

    stmt = (
        select(Booking, Car, UserModel)
        .join(Car, Car.id == Booking.vehicle_id)
        .join(UserModel, UserModel.id == Booking.customer_id)
    )
    if status:
        stmt = stmt.where(Booking.status == status)
    if city:
        from sqlalchemy import func
        stmt = stmt.where(func.lower(Car.city) == city.lower())

    from sqlalchemy import func
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt  = stmt.order_by(Booking.created_at.desc()).offset((page-1)*limit).limit(limit)
    rows  = (await db.execute(stmt)).all()

    return {
        "items": [
            {
                "id":           r.Booking.id,
                "car":          f"{r.Car.make} {r.Car.model}",
                "city":         r.Car.city,
                "customer":     r.User.full_name,
                "customer_phone": r.User.phone,
                "pickup_time":  r.Booking.pickup_time.isoformat(),
                "dropoff_time": r.Booking.dropoff_time.isoformat(),
                "status":       r.Booking.status,
                "total_amount": r.Booking.total_amount,
                "created_at":   r.Booking.created_at.isoformat(),
            }
            for r in rows
        ],
        "total": total,
        "page":  page,
        "limit": limit,
    }


@router.post("/bookings/{booking_id}/dispute")
async def mark_disputed(
    booking_id: str,
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Mark a booking as disputed for admin investigation."""
    from sqlalchemy import select
    from app.models.models import Booking, BookingStatus
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        from fastapi import HTTPException
        raise HTTPException(404, "Booking not found")
    booking.status = BookingStatus.DISPUTED
    return {"booking_id": booking_id, "status": "disputed"}


# ═══════════════════════════════════════════════════════════════ DISPUTES

@router.get("/disputes")
async def list_disputes(
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """All bookings in DISPUTED state awaiting admin resolution."""
    return await admin_service.get_disputed_bookings(db)


@router.post("/disputes/resolve")
async def resolve_dispute(
    data: DisputeResolveRequest,
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve a dispute with a written resolution.
    Optionally issue a partial/full admin-override refund.
    """
    return await admin_service.resolve_dispute(
        booking_id=data.booking_id,
        resolution=data.resolution,
        refund_amount=data.refund_amount,
        admin=admin,
        db=db,
    )


# ═══════════════════════════════════════════════════════════════ ANALYTICS

@router.get("/analytics", response_model=PlatformAnalytics)
async def platform_analytics(
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Full platform analytics snapshot.
    Production note: cache this in Redis with TTL=300s.
    """
    return await admin_service.get_platform_analytics(db)


@router.get("/analytics/monthly")
async def monthly_metrics(
    months: int = Query(6, ge=1, le=24),
    admin: User = AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Month-by-month GMV, bookings, revenue, new users."""
    return await admin_service.get_monthly_metrics(db, months=months)
