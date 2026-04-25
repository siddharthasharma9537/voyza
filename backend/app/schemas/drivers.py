"""
app/schemas/drivers.py
───────────────────────
Pydantic v2 schemas for driver management.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class DriverRegisterRequest(BaseModel):
    license_number:  str         = Field(..., min_length=5, max_length=30)
    license_class:   str         = Field(..., pattern="^(LMV|MCWOG|TRANS)$")
    license_expiry:  datetime
    vehicle_id:      str | None  = None


class DriverOut(BaseModel):
    id:                  str
    user_id:             str
    license_number:      str
    license_class:       str
    license_expiry:      datetime
    vehicle_id:          str | None
    status:              str
    is_verified:         bool
    total_rides:         int
    avg_rating:          Decimal | None
    last_latitude:       Decimal | None
    last_longitude:      Decimal | None
    location_updated_at: datetime | None

    model_config = {"from_attributes": True}


class DriverStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(offline|available)$")


class DriverLocationUpdate(BaseModel):
    latitude:  Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
