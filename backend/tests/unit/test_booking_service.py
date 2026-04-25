"""
tests/unit/test_booking_service.py
────────────────────────────────────
Unit tests for the pricing engine and booking validation logic.
These tests run without a database — pure Python logic.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.booking_service import TAX_RATE, calculate_pricing


def make_car(price_per_hour: int, price_per_day: int, security_deposit: int = 0):
    """Build a mock Car object for testing."""
    car = MagicMock()
    car.price_per_hour   = price_per_hour
    car.price_per_day    = price_per_day
    car.security_deposit = security_deposit
    return car


def dt(hours_from_now: float) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours_from_now)


# ── Pricing engine ─────────────────────────────────────────────────────────────

class TestPricingEngine:
    """
    Prices in paise:
      price_per_hour = 20000  (₹200/hr)
      price_per_day  = 100000 (₹1000/day)
    """

    def setup_method(self):
        self.car = make_car(
            price_per_hour=20000,
            price_per_day=100000,
            security_deposit=50000,
        )

    def test_2_hour_booking_uses_hourly_rate(self):
        result = calculate_pricing(self.car, dt(0), dt(2))
        assert result.base_amount == 20000 * 2  # 2 hrs × ₹200
        assert result.duration_hours == pytest.approx(2.0, abs=0.1)

    def test_19_hour_booking_uses_hourly_rate(self):
        """< 20 hours → hourly"""
        result = calculate_pricing(self.car, dt(0), dt(19))
        assert result.base_amount == 20000 * 19

    def test_20_hour_booking_uses_daily_rate(self):
        """>= 20 hours → switch to daily"""
        result = calculate_pricing(self.car, dt(0), dt(20))
        assert result.base_amount == 100000 * 1   # 1 day

    def test_2_day_booking(self):
        result = calculate_pricing(self.car, dt(0), dt(48))
        assert result.base_amount == 100000 * 2
        assert result.duration_days == 2

    def test_tax_is_18_percent(self):
        result = calculate_pricing(self.car, dt(0), dt(2))
        base = 20000 * 2
        expected_tax = int(base * TAX_RATE)
        assert result.tax_amount == expected_tax

    def test_total_includes_security_deposit(self):
        result = calculate_pricing(self.car, dt(0), dt(2))
        assert result.total_amount == result.base_amount + result.tax_amount + result.security_deposit

    def test_promo_discount_applied(self):
        discount = 10000  # ₹100 off
        result = calculate_pricing(self.car, dt(0), dt(2), promo_discount_paise=discount)
        assert result.discount_amount == discount
        after_discount = result.base_amount - discount
        assert result.tax_amount == int(after_discount * TAX_RATE)

    def test_promo_cannot_exceed_base(self):
        """Promo discount is capped at base_amount."""
        huge_discount = 99999999
        result = calculate_pricing(self.car, dt(0), dt(2), promo_discount_paise=huge_discount)
        base = 20000 * 2
        assert result.discount_amount == base   # capped
        assert result.tax_amount == 0           # nothing left to tax

    def test_fractional_hours_ceil(self):
        """1.5 hour booking → ceil to 2 hours."""
        pickup  = datetime.now(timezone.utc)
        dropoff = pickup + timedelta(minutes=90)
        result  = calculate_pricing(self.car, pickup, dropoff)
        assert result.base_amount == 20000 * 2  # ceil(1.5) = 2


# ── Schema validation ──────────────────────────────────────────────────────────

class TestBookingSchema:
    def test_dropoff_before_pickup_raises(self):
        from pydantic import ValidationError
        from app.schemas.bookings import BookingCreateRequest

        with pytest.raises(ValidationError):
            BookingCreateRequest(
                car_id="some-uuid",
                pickup_time=dt(5),
                dropoff_time=dt(2),   # before pickup
            )

    def test_minimum_1_hour_enforced(self):
        from pydantic import ValidationError
        from app.schemas.bookings import BookingCreateRequest

        with pytest.raises(ValidationError):
            BookingCreateRequest(
                car_id="some-uuid",
                pickup_time=dt(0),
                dropoff_time=dt(0) + timedelta(minutes=30),  # only 30 min
            )

    def test_maximum_30_days_enforced(self):
        from pydantic import ValidationError
        from app.schemas.bookings import BookingCreateRequest

        with pytest.raises(ValidationError):
            BookingCreateRequest(
                car_id="some-uuid",
                pickup_time=dt(0),
                dropoff_time=dt(0) + timedelta(days=31),
            )

    def test_valid_booking_passes(self):
        from app.schemas.bookings import BookingCreateRequest

        b = BookingCreateRequest(
            car_id="some-uuid",
            pickup_time=dt(0),
            dropoff_time=dt(24),
        )
        assert b.car_id == "some-uuid"
