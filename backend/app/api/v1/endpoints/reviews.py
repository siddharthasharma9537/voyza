"""
app/api/v1/endpoints/reviews.py
────────────────────────────────
POST /reviews             — submit review (customer, post-trip)
POST /reviews/reply       — owner reply to review
GET  /reviews/pending     — bookings awaiting customer review
GET  /cars/{id}/rating    — detailed rating stats for a car
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_owner, get_current_user
from app.db.base import get_db
from app.models.models import User
from app.services.review_service import (
    CreateReviewRequest, OwnerReplyRequest,
    add_owner_reply, create_review,
    get_car_rating_stats, get_pending_reviews,
)

router = APIRouter(tags=["Reviews"])


@router.post("/reviews")
async def submit_review(
    data: CreateReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a post-trip review. Only for COMPLETED bookings."""
    review = await create_review(data, current_user, db)
    return {"id": review.id, "message": "Review submitted. Thank you!"}


@router.post("/reviews/reply")
async def owner_reply(
    data: OwnerReplyRequest,
    owner: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Owner adds a public reply to a review of their car."""
    review = await add_owner_reply(data, owner, db)
    return {"id": review.id, "message": "Reply added"}


@router.get("/reviews/pending")
async def pending_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns completed bookings awaiting a review from this customer."""
    return await get_pending_reviews(current_user.id, db)


@router.get("/cars/{car_id}/rating")
async def car_rating_stats(
    car_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Detailed rating breakdown for a car (avg, distribution, % positive)."""
    return await get_car_rating_stats(car_id, db)
