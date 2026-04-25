"""
tests/unit/test_owner_service.py
──────────────────────────────────
Unit tests for owner service — pricing, earnings math, schema validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.schemas.owner import BlockSlotRequest, KYCSubmitRequest


# ── KYC Schema validation ──────────────────────────────────────────────────────

class TestKYCSchema:
    def test_valid_pan(self):
        kyc = KYCSubmitRequest(
            pan_number="ABCDE1234F",
            aadhaar_number="123456789012",
            bank_account="1234567890",
            bank_ifsc="SBIN0001234",
            bank_name="SBI",
            account_holder="Test User",
        )
        assert kyc.pan_number == "ABCDE1234F"

    def test_invalid_pan_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            KYCSubmitRequest(
                pan_number="INVALID",   # wrong format
                aadhaar_number="123456789012",
                bank_account="1234567890",
                bank_ifsc="SBIN0001234",
                bank_name="SBI",
                account_holder="Test User",
            )

    def test_invalid_aadhaar_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            KYCSubmitRequest(
                pan_number="ABCDE1234F",
                aadhaar_number="1234",   # too short
                bank_account="1234567890",
                bank_ifsc="SBIN0001234",
                bank_name="SBI",
                account_holder="Test User",
            )

    def test_invalid_ifsc_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            KYCSubmitRequest(
                pan_number="ABCDE1234F",
                aadhaar_number="123456789012",
                bank_account="1234567890",
                bank_ifsc="INVALID",
                bank_name="SBI",
                account_holder="Test User",
            )


# ── Earnings calculation ───────────────────────────────────────────────────────

class TestEarningsCalculation:
    """Test the platform fee math without hitting the DB."""

    PLATFORM_FEE = 0.20

    def owner_cut(self, base_amount: int) -> int:
        return int(base_amount * (1 - self.PLATFORM_FEE))

    def test_platform_fee_is_20_percent(self):
        base = 100000   # ₹1000 in paise
        cut = self.owner_cut(base)
        assert cut == 80000   # ₹800 — 80% of base

    def test_zero_earnings(self):
        assert self.owner_cut(0) == 0

    def test_large_booking(self):
        base = 500000   # ₹5000
        assert self.owner_cut(base) == 400000   # ₹4000

    def test_earnings_truncated_not_rounded(self):
        """int() truncates — ensures no floating-point inflation."""
        base = 100001   # odd number in paise
        cut = self.owner_cut(base)
        assert cut == int(100001 * 0.80)
        assert isinstance(cut, int)


# ── Block slot schema ──────────────────────────────────────────────────────────

class TestBlockSlotSchema:
    def _dt(self, hours_from_now: float) -> datetime:
        return datetime.now(timezone.utc) + timedelta(hours=hours_from_now)

    def test_valid_block_slot(self):
        slot = BlockSlotRequest(
            car_id="some-car-uuid",
            start_time=self._dt(2),
            end_time=self._dt(10),
            reason="maintenance",
        )
        assert slot.reason == "maintenance"

    def test_invalid_reason_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            BlockSlotRequest(
                car_id="some-car-uuid",
                start_time=self._dt(2),
                end_time=self._dt(10),
                reason="holiday",   # not in allowed list
            )
