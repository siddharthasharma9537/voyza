"""
app/schemas/admin.py
─────────────────────
Pydantic v2 schemas for all admin operations:
  • KYC queue review
  • User management
  • Booking disputes
  • Platform analytics
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ── KYC Review ────────────────────────────────────────────────────────────────

class KYCReviewRequest(BaseModel):
    car_id:   str
    decision: str = Field(..., pattern="^(approved|rejected)$")
    notes:    str | None = Field(default=None, max_length=500)


class KYCQueueItem(BaseModel):
    car_id:              str
    owner_name:          str
    owner_phone:         str
    make:                str
    model:               str
    registration_number: str
    city:                str
    submitted_at:        datetime
    rc_document_url:     str | None
    insurance_url:       str | None

    model_config = {"from_attributes": True}


# ── User Management ────────────────────────────────────────────────────────────

class AdminUserListItem(BaseModel):
    id:          str
    full_name:   str
    phone:       str
    email:       str | None
    role:        str
    is_active:   bool
    is_verified: bool
    created_at:  datetime
    booking_count: int = 0

    model_config = {"from_attributes": True}


class ToggleUserRequest(BaseModel):
    is_active: bool
    reason:    str | None = None


# ── Dispute Management ────────────────────────────────────────────────────────

class DisputeStatus(str):
    OPEN     = "open"
    RESOLVED = "resolved"
    CLOSED   = "closed"


class DisputeResolveRequest(BaseModel):
    booking_id: str
    resolution: str = Field(..., min_length=10, max_length=1000)
    refund_amount: int | None = Field(default=None, ge=0, description="Paise — 0 for no refund")


class DisputeItem(BaseModel):
    booking_id:    str
    customer_name: str
    owner_name:    str
    car:           str
    pickup_time:   datetime
    total_amount:  int
    status:        str
    created_at:    datetime

    model_config = {"from_attributes": True}


# ── Analytics ─────────────────────────────────────────────────────────────────

class PlatformAnalytics(BaseModel):
    """Snapshot of platform health metrics."""
    # Users
    total_users:      int
    total_owners:     int
    active_users_30d: int
    new_users_30d:    int

    # Cars
    total_cars:       int
    active_cars:      int
    pending_kyc:      int

    # Bookings
    total_bookings:         int
    bookings_this_month:    int
    bookings_last_month:    int
    completed_bookings:     int
    cancellation_rate:      float   # 0.0 – 1.0

    # Revenue (paise)
    total_gmv:              int     # Gross Merchandise Value
    platform_revenue:       int     # 20% of GMV
    gmv_this_month:         int
    gmv_last_month:         int

    # Quality
    avg_rating:             float | None
    dispute_rate:           float   # disputed / completed


class MonthlyMetric(BaseModel):
    month:    str   # "2026-04"
    bookings: int
    gmv:      int   # paise
    revenue:  int   # paise (20% of GMV)
    new_users: int
