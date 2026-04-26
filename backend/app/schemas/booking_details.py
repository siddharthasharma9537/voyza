"""
app/schemas/booking_details.py
───────────────────────────────
Enhanced booking detail schemas with full vehicle, owner, and customer info.
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.models import BookingStatus


class OwnerInfoResponse(BaseModel):
    """Owner/vehicle owner information in booking context."""

    id: str
    full_name: str
    phone: str
    email: str | None = None
    avatar_url: str | None = None
    avg_rating: float | None = None
    total_reviews: int = 0

    class Config:
        from_attributes = True


class CustomerInfoResponse(BaseModel):
    """Customer information in booking context."""

    id: str
    full_name: str
    phone: str
    email: str | None = None
    avatar_url: str | None = None
    is_verified: bool = False

    class Config:
        from_attributes = True


class VehicleInfoResponse(BaseModel):
    """Vehicle information in booking context."""

    id: str
    make: str
    model: str
    variant: str | None = None
    year: int
    color: str
    registration_number: str
    fuel_type: str
    transmission: str
    seating: int
    mileage_kmpl: float | None = None
    image_url: str | None = None

    class Config:
        from_attributes = True


class BookingDetailResponse(BaseModel):
    """Complete booking detail with all enriched information."""

    # Booking meta
    id: str
    booking_reference: str
    status: BookingStatus
    created_at: datetime

    # Timeline
    pickup_time: datetime
    dropoff_time: datetime
    duration_hours: float
    duration_days: int

    # Location
    pickup_address: str | None = None
    pickup_latitude: float | None = None
    pickup_longitude: float | None = None
    dropoff_address: str | None = None

    # Pricing
    base_amount: int
    discount_amount: int
    tax_amount: int
    security_deposit: int
    total_amount: int

    # Promo
    promo_code: str | None = None

    # Entities
    vehicle: VehicleInfoResponse
    owner: OwnerInfoResponse
    customer: CustomerInfoResponse

    # Cancellation info
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    cancelled_by: str | None = None

    # Odometer readings
    odometer_start: int | None = None
    odometer_end: int | None = None

    class Config:
        from_attributes = True


class OwnerBookingDetailResponse(BaseModel):
    """Booking detail response for owner (with owner earnings)."""

    # Booking meta
    id: str
    booking_reference: str
    status: BookingStatus
    created_at: datetime

    # Timeline
    pickup_time: datetime
    dropoff_time: datetime
    duration_hours: float
    duration_days: int

    # Location
    pickup_address: str | None = None
    pickup_latitude: float | None = None
    pickup_longitude: float | None = None
    dropoff_address: str | None = None

    # Pricing & Earnings
    base_amount: int
    discount_amount: int
    tax_amount: int
    security_deposit: int
    total_amount: int
    owner_earnings: int  # Calculated as base_amount * (1 - platform_fee)

    # Entities
    vehicle: VehicleInfoResponse
    customer: CustomerInfoResponse

    # Cancellation info
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    cancelled_by: str | None = None

    # Odometer readings
    odometer_start: int | None = None
    odometer_end: int | None = None

    class Config:
        from_attributes = True
