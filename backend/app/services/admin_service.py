"""
app/services/admin_service.py
──────────────────────────────
All admin-level operations:
  • KYC queue: fetch pending cars, approve/reject
  • User management: list, search, suspend/activate
  • Analytics: platform-wide GMV, bookings, ratings
  • Disputes: list disputed bookings, resolve with optional refund

All functions require ADMIN role — enforced at the router level via
`require_role(UserRole.ADMIN)`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    Booking,
    BookingStatus,
    Car,
    CarStatus,
    KYCStatus,
    Payment,
    PaymentStatus,
    Review,
    User,
    UserRole,
)
from app.schemas.admin import (
    AdminUserListItem,
    KYCQueueItem,
    KYCReviewRequest,
    PlatformAnalytics,
    MonthlyMetric,
)

PLATFORM_FEE_RATE = 0.20


# ═══════════════════════════════════════════════════════════════ KYC MANAGEMENT

async def get_kyc_queue(db: AsyncSession) -> list[dict]:
    """All cars in PENDING state awaiting admin KYC review."""
    result = await db.execute(
        select(Car, User)
        .join(User, User.id == Car.owner_id)
        .where(
            Car.status == CarStatus.PENDING,
            Car.deleted_at.is_(None),
        )
        .order_by(Car.created_at.asc())   # oldest first — FIFO queue
    )
    rows = result.all()

    return [
        {
            "car_id":              row.Car.id,
            "owner_name":          row.User.full_name,
            "owner_phone":         row.User.phone,
            "make":                row.Car.make,
            "model":               row.Car.model,
            "variant":             row.Car.variant,
            "registration_number": row.Car.registration_number,
            "city":                row.Car.city,
            "price_per_day":       row.Car.price_per_day,
            "submitted_at":        row.Car.updated_at.isoformat(),
            "rc_document_url":     row.Car.rc_document_url,
            "insurance_url":       row.Car.insurance_url,
            "kyc_notes":           row.Car.kyc_notes,
        }
        for row in rows
    ]


async def review_kyc(data: KYCReviewRequest, admin: User, db: AsyncSession) -> dict:
    """
    Approve or reject a car listing.
    On approval:  status → ACTIVE, kyc_status → APPROVED
    On rejection: status → DRAFT (owner must fix and resubmit),
                  kyc_status → REJECTED, kyc_notes set
    """
    result = await db.execute(
        select(Car).where(Car.id == data.car_id, Car.status == CarStatus.PENDING)
    )
    car = result.scalar_one_or_none()
    if not car:
        raise HTTPException(404, "Car not found in KYC queue")

    if data.decision == "approved":
        car.status     = CarStatus.ACTIVE
        car.kyc_status = KYCStatus.APPROVED
        car.kyc_notes  = data.notes or "Approved by admin"
        msg = f"Car '{car.make} {car.model}' approved and now live."
    else:
        car.status     = CarStatus.DRAFT     # back to draft — owner must fix
        car.kyc_status = KYCStatus.REJECTED
        car.kyc_notes  = data.notes or "Rejected — please resubmit with correct documents"
        msg = f"Car '{car.make} {car.model}' rejected. Owner notified."

    # TODO: send push/SMS notification to owner

    return {
        "car_id":  car.id,
        "decision": data.decision,
        "message": msg,
    }


# ═══════════════════════════════════════════════════════════════ USER MANAGEMENT

async def list_users(
    db: AsyncSession,
    role: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> dict:
    """
    Paginated user list with optional role filter and search.
    search matches full_name, phone, or email (case-insensitive).
    """
    stmt = select(User).where(User.deleted_at.is_(None))

    if role:
        stmt = stmt.where(User.role == role)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(pattern),
                User.phone.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()

    # Get booking counts per user
    user_ids = [u.id for u in users]
    booking_counts = {}
    if user_ids:
        bc_result = await db.execute(
            select(Booking.customer_id, func.count(Booking.id))
            .where(Booking.customer_id.in_(user_ids))
            .group_by(Booking.customer_id)
        )
        booking_counts = dict(bc_result.all())

    return {
        "items": [
            {
                "id":           u.id,
                "full_name":    u.full_name,
                "phone":        u.phone,
                "email":        u.email,
                "role":         u.role,
                "is_active":    u.is_active,
                "is_verified":  u.is_verified,
                "created_at":   u.created_at.isoformat(),
                "booking_count": booking_counts.get(u.id, 0),
            }
            for u in users
        ],
        "total": total,
        "page":  page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


async def toggle_user_status(
    user_id: str,
    is_active: bool,
    reason: str | None,
    db: AsyncSession,
) -> dict:
    """Suspend or reactivate a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    if user.role == UserRole.ADMIN:
        raise HTTPException(403, "Cannot suspend an admin account")

    user.is_active = is_active
    action = "activated" if is_active else "suspended"

    return {
        "user_id": user_id,
        "is_active": is_active,
        "message": f"User {user.full_name} has been {action}.",
    }


# ═══════════════════════════════════════════════════════════════ DISPUTES

async def get_disputed_bookings(db: AsyncSession) -> list[dict]:
    """All bookings in DISPUTED state."""
    result = await db.execute(
        select(Booking, Car, User)
        .join(Car,  Car.id  == Booking.vehicle_id)
        .join(User, User.id == Booking.customer_id)
        .where(Booking.status == BookingStatus.DISPUTED)
        .order_by(Booking.created_at.asc())
    )
    rows = result.all()

    return [
        {
            "booking_id":    row.Booking.id,
            "customer_name": row.User.full_name,
            "customer_phone": row.User.phone,
            "car":           f"{row.Car.make} {row.Car.model}",
            "pickup_time":   row.Booking.pickup_time.isoformat(),
            "dropoff_time":  row.Booking.dropoff_time.isoformat(),
            "total_amount":  row.Booking.total_amount,
            "status":        row.Booking.status,
            "created_at":    row.Booking.created_at.isoformat(),
        }
        for row in rows
    ]


async def resolve_dispute(
    booking_id: str,
    resolution: str,
    refund_amount: int | None,
    admin: User,
    db: AsyncSession,
) -> dict:
    """
    Admin resolves a dispute.
    Optional refund_amount triggers a partial/full refund via payment service.
    """
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")

    booking.status = BookingStatus.COMPLETED  # close the dispute

    response = {
        "booking_id": booking_id,
        "resolution": resolution,
        "refund_initiated": False,
    }

    if refund_amount and refund_amount > 0:
        from app.services.payment_service import process_refund
        try:
            refund = await process_refund(
                booking_id=booking_id,
                actor=admin,
                reason=f"Admin dispute resolution: {resolution[:100]}",
                partial_amount=refund_amount,
                db=db,
            )
            response["refund_initiated"] = True
            response["refund_id"] = refund.refund_id
            response["refund_amount"] = refund.amount
        except HTTPException as e:
            response["refund_error"] = e.detail

    return response


# ═══════════════════════════════════════════════════════════════ ANALYTICS

async def get_platform_analytics(db: AsyncSession) -> PlatformAnalytics:
    """
    Full platform analytics snapshot.
    Computed on-demand — for production, cache in Redis with TTL=300s.
    """
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (
        month_start.replace(month=month_start.month - 1)
        if month_start.month > 1
        else month_start.replace(year=month_start.year - 1, month=12)
    )
    day_30_ago = now - timedelta(days=30)

    # ── Users ─────────────────────────────────────────────────────────
    total_users   = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.CUSTOMER))).scalar_one()
    total_owners  = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.OWNER))).scalar_one()
    new_users_30d = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= day_30_ago)
    )).scalar_one()

    # Active users = users who made a booking in last 30 days
    active_users_30d = (await db.execute(
        select(func.count(func.distinct(Booking.customer_id)))
        .where(Booking.created_at >= day_30_ago)
    )).scalar_one()

    # ── Cars ──────────────────────────────────────────────────────────
    total_cars   = (await db.execute(select(func.count(Car.id)).where(Car.deleted_at.is_(None)))).scalar_one()
    active_cars  = (await db.execute(select(func.count(Car.id)).where(Car.status == CarStatus.ACTIVE))).scalar_one()
    pending_kyc  = (await db.execute(select(func.count(Car.id)).where(Car.status == CarStatus.PENDING))).scalar_one()

    # ── Bookings ──────────────────────────────────────────────────────
    total_bookings = (await db.execute(select(func.count(Booking.id)))).scalar_one()

    bookings_this_month = (await db.execute(
        select(func.count(Booking.id)).where(Booking.created_at >= month_start)
    )).scalar_one()

    bookings_last_month = (await db.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.created_at >= last_month_start, Booking.created_at < month_start)
        )
    )).scalar_one()

    completed_bookings = (await db.execute(
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.COMPLETED)
    )).scalar_one()

    cancelled_bookings = (await db.execute(
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.CANCELLED)
    )).scalar_one()

    disputed_bookings = (await db.execute(
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.DISPUTED)
    )).scalar_one()

    cancellation_rate = (cancelled_bookings / total_bookings) if total_bookings else 0.0
    dispute_rate      = (disputed_bookings / completed_bookings) if completed_bookings else 0.0

    # ── Revenue (GMV = sum of all captured payments) ───────────────────
    gmv_result = await db.execute(
        select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.CAPTURED)
    )
    total_gmv = gmv_result.scalar_one() or 0
    platform_revenue = int(total_gmv * PLATFORM_FEE_RATE)

    # GMV this month
    gmv_month_result = await db.execute(
        select(func.sum(Payment.amount))
        .where(Payment.status == PaymentStatus.CAPTURED, Payment.created_at >= month_start)
    )
    gmv_this_month = gmv_month_result.scalar_one() or 0

    # GMV last month
    gmv_last_result = await db.execute(
        select(func.sum(Payment.amount))
        .where(
            Payment.status == PaymentStatus.CAPTURED,
            Payment.created_at >= last_month_start,
            Payment.created_at < month_start,
        )
    )
    gmv_last_month = gmv_last_result.scalar_one() or 0

    # ── Quality ───────────────────────────────────────────────────────
    avg_rating_result = await db.execute(select(func.avg(Review.rating)))
    avg_rating = round(float(avg_rating_result.scalar_one()), 2) if avg_rating_result.scalar_one() else None

    return PlatformAnalytics(
        total_users=total_users,
        total_owners=total_owners,
        active_users_30d=active_users_30d,
        new_users_30d=new_users_30d,
        total_cars=total_cars,
        active_cars=active_cars,
        pending_kyc=pending_kyc,
        total_bookings=total_bookings,
        bookings_this_month=bookings_this_month,
        bookings_last_month=bookings_last_month,
        completed_bookings=completed_bookings,
        cancellation_rate=round(cancellation_rate, 3),
        total_gmv=total_gmv,
        platform_revenue=platform_revenue,
        gmv_this_month=gmv_this_month,
        gmv_last_month=gmv_last_month,
        avg_rating=avg_rating,
        dispute_rate=round(dispute_rate, 3),
    )


async def get_monthly_metrics(db: AsyncSession, months: int = 6) -> list[MonthlyMetric]:
    """Month-by-month platform metrics for the analytics chart."""
    bookings_by_month = await db.execute(
        select(
            func.to_char(Booking.created_at, "YYYY-MM").label("month"),
            func.count(Booking.id).label("bookings"),
        )
        .group_by("month")
        .order_by("month")
        .limit(months)
    )

    payments_by_month = await db.execute(
        select(
            func.to_char(Payment.created_at, "YYYY-MM").label("month"),
            func.sum(Payment.amount).label("gmv"),
        )
        .where(Payment.status == PaymentStatus.CAPTURED)
        .group_by("month")
        .order_by("month")
        .limit(months)
    )

    users_by_month = await db.execute(
        select(
            func.to_char(User.created_at, "YYYY-MM").label("month"),
            func.count(User.id).label("new_users"),
        )
        .group_by("month")
        .order_by("month")
        .limit(months)
    )

    # Merge by month key
    bookings_map = {row.month: row.bookings for row in bookings_by_month}
    payments_map = {row.month: int(row.gmv or 0) for row in payments_by_month}
    users_map    = {row.month: row.new_users for row in users_by_month}

    all_months = sorted(set(list(bookings_map) + list(payments_map) + list(users_map)))

    return [
        MonthlyMetric(
            month=m,
            bookings=bookings_map.get(m, 0),
            gmv=payments_map.get(m, 0),
            revenue=int(payments_map.get(m, 0) * PLATFORM_FEE_RATE),
            new_users=users_map.get(m, 0),
        )
        for m in all_months[-months:]
    ]
