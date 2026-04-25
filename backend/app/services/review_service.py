"""
app/services/review_service.py
───────────────────────────────
Post-trip reviews and ratings:
  • Customer submits review after COMPLETED booking
  • One review per booking (enforced by UNIQUE constraint)
  • Owner can reply once
  • Aggregate rating computed per car
  • Platform-wide rating stats for admin
"""

from __future__ import annotations

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Booking, BookingStatus, Car, Review, User


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateReviewRequest(BaseModel):
    booking_id: str
    rating:     int = Field(..., ge=1, le=5)
    comment:    str | None = Field(default=None, max_length=1000)


class OwnerReplyRequest(BaseModel):
    review_id: str
    reply:     str = Field(..., min_length=5, max_length=500)


class ReviewOut(BaseModel):
    id:          str
    booking_id:  str
    car_id:      str
    reviewer:    str
    rating:      int
    comment:     str | None
    owner_reply: str | None
    created_at:  str

    model_config = {"from_attributes": True}


# ── Service ───────────────────────────────────────────────────────────────────

async def create_review(
    data: CreateReviewRequest,
    customer: User,
    db: AsyncSession,
) -> Review:
    """
    Customer submits review after completing a booking.
    Validates: booking exists, is COMPLETED, belongs to customer, not already reviewed.
    """
    # Load booking
    result = await db.execute(
        select(Booking).where(
            Booking.id == data.booking_id,
            Booking.customer_id == customer.id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")

    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(400, "You can only review completed bookings")

    # Check for existing review
    existing = await db.execute(
        select(Review).where(Review.booking_id == data.booking_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "You have already reviewed this booking")

    review = Review(
        booking_id=data.booking_id,
        reviewer_id=customer.id,
        vehicle_id=booking.vehicle_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    await db.flush()
    return review


async def add_owner_reply(
    data: OwnerReplyRequest,
    owner: User,
    db: AsyncSession,
) -> Review:
    """Owner replies to a review of their car. Can only reply once."""
    result = await db.execute(
        select(Review, Car)
        .join(Car, Car.id == Review.vehicle_id)
        .where(Review.id == data.review_id, Car.owner_id == owner.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(404, "Review not found")

    review = row.Review
    if review.owner_reply:
        raise HTTPException(400, "You have already replied to this review")

    review.owner_reply = data.reply
    return review


async def get_car_rating_stats(car_id: str, db: AsyncSession) -> dict:
    """Detailed rating breakdown for a car (1-5 star distribution)."""
    result = await db.execute(
        select(
            func.avg(Review.rating).label("avg"),
            func.count(Review.id).label("total"),
            func.sum((Review.rating == 5).cast(int)).label("five"),
            func.sum((Review.rating == 4).cast(int)).label("four"),
            func.sum((Review.rating == 3).cast(int)).label("three"),
            func.sum((Review.rating == 2).cast(int)).label("two"),
            func.sum((Review.rating == 1).cast(int)).label("one"),
        ).where(Review.vehicle_id == car_id)
    )
    row = result.one()

    total = row.total or 0
    avg   = round(float(row.avg), 1) if row.avg else None

    return {
        "avg_rating":   avg,
        "total_reviews": total,
        "distribution": {
            "5": row.five  or 0,
            "4": row.four  or 0,
            "3": row.three or 0,
            "2": row.two   or 0,
            "1": row.one   or 0,
        },
        "pct_positive": round((((row.five or 0) + (row.four or 0)) / total * 100), 1) if total else 0,
    }


async def get_pending_reviews(customer_id: str, db: AsyncSession) -> list[dict]:
    """
    Completed bookings the customer hasn't reviewed yet.
    Shown in-app as 'Rate your trip' prompts.
    """
    reviewed_ids = select(Review.booking_id).where(Review.reviewer_id == customer_id)

    result = await db.execute(
        select(Booking, Car)
        .join(Car, Car.id == Booking.vehicle_id)
        .where(
            Booking.customer_id == customer_id,
            Booking.status == BookingStatus.COMPLETED,
            Booking.id.not_in(reviewed_ids),
        )
        .order_by(Booking.dropoff_time.desc())
        .limit(5)
    )
    rows = result.all()

    return [
        {
            "booking_id": row.Booking.id,
            "car":        f"{row.Car.make} {row.Car.model}",
            "dropoff":    row.Booking.dropoff_time.isoformat(),
        }
        for row in rows
    ]
