"""
app/schemas/rides.py
─────────────────────
Pydantic v2 schemas for ride requests and responses.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class RideRequestCreate(BaseModel):
    pickup_address:   str     = Field(..., min_length=5)
    pickup_latitude:  Decimal = Field(..., ge=-90, le=90)
    pickup_longitude: Decimal = Field(..., ge=-180, le=180)
    dropoff_address:  str     = Field(..., min_length=5)
    dropoff_latitude: Decimal = Field(..., ge=-90, le=90)
    dropoff_longitude: Decimal = Field(..., ge=-180, le=180)
    booking_id:       str | None = None   # optional — link to pre-existing booking


class RideOut(BaseModel):
    id:               str
    booking_id:       str | None
    customer_id:      str
    driver_id:        str | None
    vehicle_id:       str
    status:           str
    pickup_address:   str
    pickup_latitude:  Decimal
    pickup_longitude: Decimal
    dropoff_address:  str
    dropoff_latitude: Decimal
    dropoff_longitude: Decimal
    estimated_fare:   int
    final_fare:       int | None
    distance_km:      Decimal | None
    duration_minutes: int | None
    requested_at:     datetime
    accepted_at:      datetime | None
    started_at:       datetime | None
    completed_at:     datetime | None
    cancelled_at:     datetime | None
    cancel_reason:    str | None

    model_config = {"from_attributes": True}


class RideCancelRequest(BaseModel):
    reason: str | None = None


class FareEstimate(BaseModel):
    estimated_fare:   int      # paise
    distance_km:      Decimal
    duration_minutes: int
    surge_multiplier: Decimal = Decimal("1.0")
