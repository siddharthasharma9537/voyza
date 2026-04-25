"""
app/services/pricing_service.py
────────────────────────────────
Dynamic pricing engine for Voyza.

Pricing factors:
  1. Base rate (car's configured price_per_day / price_per_hour)
  2. Demand surge (0.8x – 2.0x based on city booking density)
  3. Time-of-week multiplier (weekends cost more)
  4. Advance booking discount (book 7+ days ahead = 10% off)
  5. Season multiplier (peak holiday seasons)
  6. Duration discount (longer trips get better daily rates)

Final price = base × demand × time_of_week × season × advance
All multipliers capped at 2.0x to prevent extreme prices.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Booking, BookingStatus, Car


# ── Multiplier constants ──────────────────────────────────────────────────────

WEEKEND_MULTIPLIER   = 1.25    # Friday pickup or Saturday/Sunday in rental period
PEAK_SEASON_MONTHS   = {4, 5, 10, 11, 12}  # Apr-May (summer), Oct-Dec (festive)
PEAK_SEASON_MULT     = 1.15
ADVANCE_DISCOUNT_7D  = 0.90    # 10% off if booked 7+ days ahead
ADVANCE_DISCOUNT_14D = 0.85    # 15% off if booked 14+ days ahead
DURATION_DISCOUNT_3D = 0.95    # 5% off for 3+ day rentals
DURATION_DISCOUNT_7D = 0.90    # 10% off for 7+ day rentals
MAX_SURGE_MULTIPLIER = 2.00
MIN_SURGE_MULTIPLIER = 0.80


async def get_demand_multiplier(
    car: Car,
    pickup_time: datetime,
    db: AsyncSession,
) -> float:
    """
    Calculate demand-based surge for a city+time window.
    High demand (many confirmed bookings in city) → higher multiplier.
    Low demand → discount to encourage bookings.
    """
    window_start = pickup_time - timedelta(hours=12)
    window_end   = pickup_time + timedelta(hours=12)

    # Count confirmed bookings in same city around the same time
    result = await db.execute(
        select(func.count(Booking.id))
        .join(Car, Car.id == Booking.vehicle_id)
        .where(
            and_(
                Car.city == car.city,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
                Booking.pickup_time >= window_start,
                Booking.pickup_time <= window_end,
            )
        )
    )
    demand_count = result.scalar_one() or 0

    # Active cars in the city
    active_result = await db.execute(
        select(func.count(Car.id)).where(
            Car.city == car.city,
            Car.status == "active",
        )
    )
    active_cars = max(active_result.scalar_one() or 1, 1)

    # Demand ratio: bookings / available cars
    demand_ratio = demand_count / active_cars

    # Map ratio to multiplier
    if demand_ratio >= 0.80:
        multiplier = MAX_SURGE_MULTIPLIER   # 80%+ booked → 2x surge
    elif demand_ratio >= 0.60:
        multiplier = 1.50
    elif demand_ratio >= 0.40:
        multiplier = 1.25
    elif demand_ratio >= 0.20:
        multiplier = 1.00
    elif demand_ratio >= 0.10:
        multiplier = 0.95
    else:
        multiplier = MIN_SURGE_MULTIPLIER   # very low demand → 20% discount

    return round(multiplier, 2)


def get_time_of_week_multiplier(pickup: datetime, dropoff: datetime) -> float:
    """Weekend rentals (Fri pickup or Sat/Sun in period) cost more."""
    days = []
    current = pickup
    while current <= dropoff:
        days.append(current.weekday())   # 0=Mon, 4=Fri, 5=Sat, 6=Sun
        current += timedelta(days=1)

    weekend_days = sum(1 for d in days if d >= 4)
    if not days:
        return 1.0

    weekend_fraction = weekend_days / len(days)
    if weekend_fraction >= 0.6:
        return WEEKEND_MULTIPLIER
    elif weekend_fraction >= 0.3:
        return 1.10
    return 1.0


def get_season_multiplier(pickup: datetime) -> float:
    """Peak travel months command higher prices."""
    if pickup.month in PEAK_SEASON_MONTHS:
        return PEAK_SEASON_MULT
    return 1.0


def get_advance_booking_multiplier(
    pickup: datetime,
    booked_at: datetime | None = None,
) -> float:
    """Reward customers who book early with discounts."""
    now = booked_at or datetime.now(timezone.utc)
    days_ahead = (pickup - now).total_seconds() / 86400

    if days_ahead >= 14:
        return ADVANCE_DISCOUNT_14D
    elif days_ahead >= 7:
        return ADVANCE_DISCOUNT_7D
    return 1.0


def get_duration_multiplier(duration_days: int) -> float:
    """Longer trips get better per-day rates."""
    if duration_days >= 7:
        return DURATION_DISCOUNT_7D
    elif duration_days >= 3:
        return DURATION_DISCOUNT_3D
    return 1.0


# ── Main pricing function ─────────────────────────────────────────────────────

async def calculate_dynamic_price(
    car: Car,
    pickup: datetime,
    dropoff: datetime,
    db: AsyncSession,
    promo_discount_paise: int = 0,
) -> "DynamicPricingResult":
    """
    Full dynamic pricing calculation.
    Returns a breakdown of all factors applied.
    """
    duration_seconds = (dropoff - pickup).total_seconds()
    duration_hours   = duration_seconds / 3600
    duration_days    = math.ceil(duration_hours / 24)

    # Base amount (same logic as booking_service)
    if duration_hours >= 20:
        base_amount = car.price_per_day * duration_days
        rate_type   = "daily"
    else:
        hours_ceil  = math.ceil(duration_hours)
        base_amount = car.price_per_hour * hours_ceil
        rate_type   = "hourly"

    # Compute all multipliers
    demand_mult   = await get_demand_multiplier(car, pickup, db)
    time_mult     = get_time_of_week_multiplier(pickup, dropoff)
    season_mult   = get_season_multiplier(pickup)
    advance_mult  = get_advance_booking_multiplier(pickup)
    duration_mult = get_duration_multiplier(duration_days)

    # Combined multiplier (cap at 2.5x total)
    combined = min(demand_mult * time_mult * season_mult * advance_mult * duration_mult, 2.5)
    combined = round(combined, 3)

    dynamic_base = int(base_amount * combined)

    # Apply promo (on dynamic base)
    discount     = min(promo_discount_paise, dynamic_base)
    after_disc   = dynamic_base - discount
    tax_amount   = int(after_disc * 0.18)
    total_amount = after_disc + tax_amount + car.security_deposit

    return DynamicPricingResult(
        duration_hours=round(duration_hours, 2),
        duration_days=duration_days,
        rate_type=rate_type,
        base_amount=base_amount,
        demand_multiplier=demand_mult,
        time_of_week_multiplier=time_mult,
        season_multiplier=season_mult,
        advance_booking_multiplier=advance_mult,
        duration_multiplier=duration_mult,
        combined_multiplier=combined,
        dynamic_base_amount=dynamic_base,
        discount_amount=discount,
        tax_amount=tax_amount,
        security_deposit=car.security_deposit,
        total_amount=total_amount,
        savings=max(base_amount - dynamic_base, 0),
        surge=max(dynamic_base - base_amount, 0),
    )


# ── Result dataclass ──────────────────────────────────────────────────────────

from dataclasses import dataclass


@dataclass
class DynamicPricingResult:
    duration_hours:             float
    duration_days:              int
    rate_type:                  str      # "hourly" | "daily"
    base_amount:                int      # paise — before multipliers
    demand_multiplier:          float
    time_of_week_multiplier:    float
    season_multiplier:          float
    advance_booking_multiplier: float
    duration_multiplier:        float
    combined_multiplier:        float
    dynamic_base_amount:        int      # paise — after multipliers
    discount_amount:            int      # paise
    tax_amount:                 int      # paise
    security_deposit:           int      # paise
    total_amount:               int      # paise
    savings:                    int      # paise saved vs base (if multiplier < 1)
    surge:                      int      # paise extra vs base (if multiplier > 1)
