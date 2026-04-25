"""
app/schemas/vehicles.py
────────────────────────
Pydantic v2 schemas for vehicle listing, browsing, and detail views.
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


# ── Images ────────────────────────────────────────────────────────────────────

class VehicleImageOut(BaseModel):
    id:         str
    url:        str
    is_primary: bool
    sort_order: int

    model_config = {"from_attributes": True}


# ── Browse / List card ────────────────────────────────────────────────────────

class VehicleListItem(BaseModel):
    """Lightweight projection used in browse grids — avoids over-fetching."""
    id:             str
    make:           str
    model:          str
    variant:        str | None
    year:           int
    city:           str
    fuel_type:      str
    transmission:   str
    seating:        int
    price_per_hour: int           # paise
    price_per_day:  int           # paise
    primary_image:  str | None    # URL of primary image
    avg_rating:     float | None  # computed
    review_count:   int

    model_config = {"from_attributes": True}


# ── Full detail ────────────────────────────────────────────────────────────────

class VehicleDetail(BaseModel):
    id:               str
    owner_id:         str
    make:             str
    model:            str
    variant:          str | None
    year:             int
    color:            str
    seating:          int
    fuel_type:        str
    transmission:     str
    mileage_kmpl:     Decimal | None
    city:             str
    state:            str
    latitude:         Decimal | None
    longitude:        Decimal | None
    address:          str | None
    price_per_hour:   int
    price_per_day:    int
    security_deposit: int
    features:         dict[str, Any]
    images:           list[VehicleImageOut]
    avg_rating:       float | None
    review_count:     int
    status:           str

    model_config = {"from_attributes": True}


# ── Browse query filters ──────────────────────────────────────────────────────

class VehicleBrowseParams(BaseModel):
    """Query parameters for GET /vehicles — validated server-side."""
    city:           str | None = None
    fuel_type:      str | None = None
    transmission:   str | None = None
    min_seating:    int | None = Field(default=None, ge=2, le=9)
    max_price_day:  int | None = Field(default=None, ge=0)        # paise
    min_price_day:  int | None = Field(default=None, ge=0)        # paise
    pickup_time:    str | None = None   # ISO 8601
    dropoff_time:   str | None = None   # ISO 8601
    page:           int        = Field(default=1, ge=1)
    limit:          int        = Field(default=20, ge=1, le=100)
    sort_by:        str        = Field(default="price_asc",
                                       pattern="^(price_asc|price_desc|rating|newest)$")


class PaginatedVehicles(BaseModel):
    items:       list[VehicleListItem]
    total:       int
    page:        int
    limit:       int
    total_pages: int


# ── Owner: create/update vehicle ──────────────────────────────────────────────

class VehicleCreateRequest(BaseModel):
    make:                str   = Field(..., min_length=1, max_length=80)
    model:               str   = Field(..., min_length=1, max_length=80)
    variant:             str | None = None
    year:                int   = Field(..., ge=2000, le=2035)
    color:               str   = Field(..., max_length=40)
    seating:             int   = Field(..., ge=2, le=9)
    fuel_type:           str   = Field(..., pattern="^(petrol|diesel|electric|hybrid|cng)$")
    transmission:        str   = Field(..., pattern="^(manual|automatic)$")
    mileage_kmpl:        Decimal | None = None
    city:                str   = Field(..., max_length=100)
    state:               str   = Field(..., max_length=100)
    address:             str | None = None
    latitude:            Decimal | None = None
    longitude:           Decimal | None = None
    price_per_hour:      int   = Field(..., gt=0)   # paise
    price_per_day:       int   = Field(..., gt=0)   # paise
    security_deposit:    int   = Field(default=0, ge=0)
    registration_number: str   = Field(..., min_length=5, max_length=20)
    features:            dict[str, Any] = Field(default_factory=dict)


class VehicleUpdateRequest(BaseModel):
    """All fields optional — PATCH semantics."""
    variant:          str | None     = None
    color:            str | None     = None
    address:          str | None     = None
    latitude:         Decimal | None = None
    longitude:        Decimal | None = None
    price_per_hour:   int | None     = Field(default=None, gt=0)
    price_per_day:    int | None     = Field(default=None, gt=0)
    security_deposit: int | None     = Field(default=None, ge=0)
    features:         dict[str, Any] | None = None
