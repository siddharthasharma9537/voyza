"""
app/schemas/bookings.py
────────────────────────
Booking request / response schemas.
Prices are always in paise (integer) to avoid float bugs.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class BookingCreateRequest(BaseModel):
    vehicle_id:       str
    pickup_time:      datetime
    dropoff_time:     datetime
    pickup_address:   str | None  = None
    pickup_latitude:  Decimal | None = None
    pickup_longitude: Decimal | None = None
    promo_code:       str | None  = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.dropoff_time <= self.pickup_time:
            raise ValueError("dropoff_time must be after pickup_time")
        # Minimum booking: 1 hour
        diff_hours = (self.dropoff_time - self.pickup_time).total_seconds() / 3600
        if diff_hours < 1:
            raise ValueError("Minimum booking duration is 1 hour")
        # Maximum booking: 30 days
        if diff_hours > 30 * 24:
            raise ValueError("Maximum booking duration is 30 days")
        return self


class PricingBreakdown(BaseModel):
    """Shown to user before payment confirmation."""
    duration_hours:   float
    duration_days:    int
    base_amount:      int     # paise
    discount_amount:  int     # paise
    tax_amount:       int     # paise
    security_deposit: int     # paise
    total_amount:     int     # paise
    currency:         str = "INR"


class BookingResponse(BaseModel):
    id:               str
    vehicle_id:       str
    customer_id:      str
    pickup_time:      datetime
    dropoff_time:     datetime
    status:           str
    base_amount:      int
    discount_amount:  int
    tax_amount:       int
    total_amount:     int
    security_deposit: int
    promo_code:       str | None
    created_at:       datetime

    model_config = {"from_attributes": True}


class BookingListItem(BaseModel):
    id:           str
    car_make:     str
    car_model:    str
    car_image:    str | None
    pickup_time:  datetime
    dropoff_time: datetime
    status:       str
    total_amount: int

    model_config = {"from_attributes": True}


class CancelBookingRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
