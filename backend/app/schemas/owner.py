"""
app/schemas/owner.py
─────────────────────
Pydantic v2 schemas for all owner-facing operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


# ── KYC ───────────────────────────────────────────────────────────────────────

class KYCSubmitRequest(BaseModel):
    """Owner submits personal KYC documents for admin review."""
    pan_number:       str = Field(..., min_length=10, max_length=10, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    aadhaar_number:   str = Field(..., min_length=12, max_length=12, pattern=r"^\d{12}$")
    bank_account:     str = Field(..., min_length=9, max_length=18)
    bank_ifsc:        str = Field(..., min_length=11, max_length=11, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    bank_name:        str
    account_holder:   str


class KYCStatusResponse(BaseModel):
    status:    str
    notes:     str | None
    submitted_at: datetime | None

    model_config = {"from_attributes": True}


# ── Availability management ────────────────────────────────────────────────────

class BlockSlotRequest(BaseModel):
    vehicle_id: str
    start_time: datetime
    end_time:   datetime
    reason:     str = Field(default="blocked", pattern="^(blocked|maintenance|personal)$")

    class Config:
        json_schema_extra = {
            "example": {
                "vehicle_id": "uuid",
                "start_time": "2026-05-01T00:00:00+05:30",
                "end_time":   "2026-05-03T00:00:00+05:30",
                "reason":     "maintenance",
            }
        }


# ── Earnings ──────────────────────────────────────────────────────────────────

class EarningsSummary(BaseModel):
    total_earnings:    int   # paise — lifetime
    this_month:        int   # paise
    last_month:        int   # paise
    pending_payout:    int   # paise — bookings not yet paid out
    total_bookings:    int
    completed_bookings: int
    avg_rating:        float | None
    top_car:           str | None   # "Make Model" of best-earning car


class MonthlyEarning(BaseModel):
    month:    str   # "2026-04"
    amount:   int   # paise
    bookings: int


# ── Owner booking view ────────────────────────────────────────────────────────

class OwnerBookingItem(BaseModel):
    id:            str
    car_make:      str
    car_model:     str
    customer_name: str
    pickup_time:   datetime
    dropoff_time:  datetime
    status:        str
    total_amount:  int
    owner_earnings: int   # total - platform fee

    model_config = {"from_attributes": True}
