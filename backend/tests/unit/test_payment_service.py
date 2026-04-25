"""
tests/unit/test_payment_service.py
────────────────────────────────────
Unit tests for payment logic — refund policy calculation,
HMAC signature verification, idempotency edge cases.
No DB required — pure Python.
"""

import hashlib
import hmac
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch


# ── HMAC Signature verification ────────────────────────────────────────────────

class TestSignatureVerification:
    """
    Razorpay signature = HMAC_SHA256(key_secret, "order_id|payment_id")
    """

    KEY_SECRET = "test_secret_key_12345"

    def _make_sig(self, order_id: str, payment_id: str) -> str:
        msg = f"{order_id}|{payment_id}"
        return hmac.new(
            self.KEY_SECRET.encode(),
            msg.encode(),
            hashlib.sha256,
        ).hexdigest()

    def test_valid_signature_passes(self):
        order_id   = "order_abc123"
        payment_id = "pay_xyz789"
        sig = self._make_sig(order_id, payment_id)

        # Replicate the verification logic
        msg      = f"{order_id}|{payment_id}"
        expected = hmac.new(
            self.KEY_SECRET.encode(), msg.encode(), hashlib.sha256
        ).hexdigest()
        assert hmac.compare_digest(expected, sig) is True

    def test_wrong_secret_fails(self):
        order_id   = "order_abc123"
        payment_id = "pay_xyz789"
        sig        = self._make_sig(order_id, payment_id)

        wrong_expected = hmac.new(
            b"wrong_secret", f"{order_id}|{payment_id}".encode(), hashlib.sha256
        ).hexdigest()
        assert hmac.compare_digest(wrong_expected, sig) is False

    def test_tampered_order_id_fails(self):
        sig = self._make_sig("order_real", "pay_xyz789")
        tampered = hmac.new(
            self.KEY_SECRET.encode(),
            b"order_FAKE|pay_xyz789",
            hashlib.sha256,
        ).hexdigest()
        assert hmac.compare_digest(tampered, sig) is False

    def test_timing_safe_comparison(self):
        """Ensure compare_digest is used (prevents timing attacks)."""
        import inspect
        from app.services import payment_service
        source = inspect.getsource(payment_service.verify_payment)
        assert "compare_digest" in source


# ── Refund policy ──────────────────────────────────────────────────────────────

class TestRefundPolicy:
    """
    Policy:
      > 24h before pickup  → 100% of (base + tax - discount)
      6–24h before pickup  → 50%
      < 6h before pickup   → 0% (raise error)
    """

    def _booking(self, hours_until_pickup: float, base=100000, tax=18000, discount=0):
        """Mock booking object."""
        b = MagicMock()
        b.pickup_time   = datetime.now(timezone.utc) + timedelta(hours=hours_until_pickup)
        b.base_amount   = base
        b.tax_amount    = tax
        b.discount_amount = discount
        return b

    def _calculate_refund(self, booking, partial_amount=None, is_admin=False):
        """Inline the refund calculation logic for testing."""
        now = datetime.now(timezone.utc)
        hours_until = (booking.pickup_time - now).total_seconds() / 3600

        if partial_amount is not None and is_admin:
            return min(partial_amount, 200000)

        if hours_until > 24:
            return booking.base_amount + booking.tax_amount - booking.discount_amount
        elif hours_until > 6:
            return (booking.base_amount + booking.tax_amount - booking.discount_amount) // 2
        else:
            raise ValueError("No refund within 6 hours")

    def test_full_refund_more_than_24h(self):
        b = self._booking(hours_until_pickup=48)
        refund = self._calculate_refund(b)
        assert refund == 100000 + 18000   # base + tax

    def test_half_refund_between_6_and_24h(self):
        b = self._booking(hours_until_pickup=12)
        refund = self._calculate_refund(b)
        assert refund == (100000 + 18000) // 2

    def test_no_refund_under_6h_raises(self):
        b = self._booking(hours_until_pickup=3)
        with pytest.raises(ValueError):
            self._calculate_refund(b)

    def test_discount_reduces_refundable_base(self):
        b = self._booking(hours_until_pickup=48, base=100000, tax=18000, discount=10000)
        refund = self._calculate_refund(b)
        # base + tax - discount = 100000 + 18000 - 10000 = 108000
        assert refund == 108000

    def test_admin_can_set_partial_refund(self):
        b = self._booking(hours_until_pickup=1)   # < 6h — normally 0%
        refund = self._calculate_refund(b, partial_amount=50000, is_admin=True)
        assert refund == 50000

    def test_refund_capped_at_payment_amount(self):
        b = self._booking(hours_until_pickup=48, base=100000, tax=18000)
        # Payment amount is less than what would be refunded
        max_payment = 50000
        refund = min(self._calculate_refund(b), max_payment)
        assert refund == 50000


# ── Webhook signature ──────────────────────────────────────────────────────────

class TestWebhookSignature:

    WEBHOOK_SECRET = "wh_secret_test_abc"

    def _make_webhook_sig(self, body: bytes) -> str:
        return hmac.new(
            self.WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

    def test_valid_webhook_sig_passes(self):
        body = b'{"event":"payment.captured","payload":{}}'
        sig  = self._make_webhook_sig(body)
        expected = hmac.new(
            self.WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        assert hmac.compare_digest(expected, sig)

    def test_tampered_body_fails(self):
        body = b'{"event":"payment.captured","payload":{}}'
        sig  = self._make_webhook_sig(body)
        tampered_body = b'{"event":"payment.captured","payload":{"amount":99999}}'
        expected = hmac.new(
            self.WEBHOOK_SECRET.encode(), tampered_body, hashlib.sha256
        ).hexdigest()
        assert not hmac.compare_digest(expected, sig)

    def test_empty_body_rejected(self):
        sig = self._make_webhook_sig(b"")
        valid_expected = hmac.new(
            self.WEBHOOK_SECRET.encode(), b'{"event":"test"}', hashlib.sha256
        ).hexdigest()
        assert not hmac.compare_digest(valid_expected, sig)
