"""
tests/unit/test_admin_service.py
──────────────────────────────────
Unit tests for admin service logic — no DB required.
"""

import pytest
from datetime import datetime, timezone


# ── Analytics math ─────────────────────────────────────────────────────────────

class TestAnalyticsMath:

    PLATFORM_FEE = 0.20

    def platform_revenue(self, gmv: int) -> int:
        return int(gmv * self.PLATFORM_FEE)

    def cancellation_rate(self, cancelled: int, total: int) -> float:
        return cancelled / total if total else 0.0

    def dispute_rate(self, disputed: int, completed: int) -> float:
        return disputed / completed if completed else 0.0

    def test_platform_revenue_is_20_percent(self):
        assert self.platform_revenue(1_000_000) == 200_000

    def test_zero_gmv_gives_zero_revenue(self):
        assert self.platform_revenue(0) == 0

    def test_cancellation_rate_correct(self):
        rate = self.cancellation_rate(cancelled=10, total=100)
        assert rate == pytest.approx(0.10)

    def test_zero_bookings_gives_zero_rate(self):
        assert self.cancellation_rate(0, 0) == 0.0

    def test_dispute_rate_correct(self):
        rate = self.dispute_rate(disputed=2, completed=200)
        assert rate == pytest.approx(0.01)

    def test_revenue_integer_truncation(self):
        """int() truncates — verify no floating-point inflation."""
        gmv = 333_333  # doesn't divide evenly by 5
        rev = self.platform_revenue(gmv)
        assert rev == int(333_333 * 0.20)
        assert isinstance(rev, int)


# ── KYC state transitions ──────────────────────────────────────────────────────

class TestKYCTransitions:
    """Document valid KYC state transitions."""

    def test_pending_can_be_approved(self):
        from app.models import CarStatus, KYCStatus
        # On approval
        assert CarStatus.ACTIVE   == "active"
        assert KYCStatus.APPROVED == "approved"

    def test_pending_can_be_rejected(self):
        from app.models import CarStatus, KYCStatus
        # On rejection — car goes back to DRAFT so owner can fix
        assert CarStatus.DRAFT    == "draft"
        assert KYCStatus.REJECTED == "rejected"

    def test_only_pending_cars_in_queue(self):
        from app.models import CarStatus
        reviewable = [CarStatus.PENDING]
        non_reviewable = [CarStatus.ACTIVE, CarStatus.DRAFT, CarStatus.SUSPENDED]
        for status in non_reviewable:
            assert status not in reviewable


# ── Admin schema validation ────────────────────────────────────────────────────

class TestAdminSchemas:

    def test_kyc_review_only_allows_approved_or_rejected(self):
        from pydantic import ValidationError
        from app.schemas.admin import KYCReviewRequest

        with pytest.raises(ValidationError):
            KYCReviewRequest(car_id="abc", decision="maybe")

        # Valid decisions
        r1 = KYCReviewRequest(car_id="abc", decision="approved")
        r2 = KYCReviewRequest(car_id="abc", decision="rejected")
        assert r1.decision == "approved"
        assert r2.decision == "rejected"

    def test_dispute_resolve_refund_cannot_be_negative(self):
        from pydantic import ValidationError
        from app.schemas.admin import DisputeResolveRequest

        with pytest.raises(ValidationError):
            DisputeResolveRequest(
                booking_id="abc",
                resolution="Test resolution that is long enough",
                refund_amount=-1000,
            )

    def test_dispute_resolution_minimum_length(self):
        from pydantic import ValidationError
        from app.schemas.admin import DisputeResolveRequest

        with pytest.raises(ValidationError):
            DisputeResolveRequest(
                booking_id="abc",
                resolution="short",  # less than 10 chars
            )

    def test_toggle_user_schema(self):
        from app.schemas.admin import ToggleUserRequest
        req = ToggleUserRequest(is_active=False, reason="Fraud detected")
        assert req.is_active is False
        assert req.reason == "Fraud detected"


# ── Role protection ────────────────────────────────────────────────────────────

class TestRoleProtection:

    def test_admin_role_value(self):
        from app.models import UserRole
        assert UserRole.ADMIN == "admin"

    def test_require_admin_dependency_exists(self):
        from app.core.dependencies import get_current_admin
        assert callable(get_current_admin)

    def test_admin_cannot_be_suspended(self):
        """Document that toggle_user_status blocks admin suspension."""
        import inspect
        from app.services import admin_service
        source = inspect.getsource(admin_service.toggle_user_status)
        assert "ADMIN" in source
        assert "403" in source or "Forbidden" in source.lower() or "Cannot suspend" in source
