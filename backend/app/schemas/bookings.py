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
    owner_id:         str
    pickup_time:      datetime
    dropoff_time:     datetime
    pickup_address:   str | None
    pickup_latitude:  Decimal | None
    pickup_longitude: Decimal | None
    status:           str
    base_amount:      int
    discount_amount:  int
    tax_amount:       int
    total_amount:     int
    security_deposit: int
    promo_code:       str | None
    created_at:       datetime

    model_config = {"from_attributes": True}


class BookingDetailResponse(BaseModel):
    """Enhanced booking response with vehicle and customer details - for summary and details page."""
    # Booking details
    id:                str
    booking_reference: str  # e.g., "VOY-20260426-001234"
    status:            str

    # Vehicle details
    vehicle_id:        str
    vehicle_name:      str  # e.g., "Maruti Swift LXi"
    vehicle_make:      str
    vehicle_model:     str
    vehicle_year:      int
    vehicle_color:     str
    vehicle_image:     str | None
    registration_number: str | None

    # Owner details
    owner_id:          str
    owner_name:        str
    owner_rating:      float | None

    # Customer details
    customer_id:       str
    customer_name:     str
    customer_phone:    str
    customer_email:    str | None

    # Pickup/Dropoff
    pickup_time:       datetime
    dropoff_time:      datetime
    pickup_address:    str | None
    dropoff_address:   str | None
    pickup_latitude:   Decimal | None
    pickup_longitude:  Decimal | None

    # Pricing breakdown
    base_amount:       int      # paise
    discount_amount:   int      # paise
    tax_amount:        int      # paise
    security_deposit:  int      # paise
    total_amount:      int      # paise

    # Additional info
    promo_code:        str | None
    cancel_reason:     str | None
    cancelled_at:      datetime | None

    # Timestamps
    created_at:        datetime
    updated_at:        datetime

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
