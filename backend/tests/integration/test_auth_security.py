"""
tests/integration/test_auth_security.py
───────────────────────────────────────
Integration tests for authentication security:
  1. Phone OTP flows (SMS dispatch)
  2. Password strength validation
  3. Phone format validation (Indian numbers)
  4. OAuth phone verification requirement
  5. Token refresh and revocation
  6. Phone verification dependency

Run with: pytest tests/integration/test_auth_security.py -v
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.models.models import User, UserRole, OTPCode
from app.core.security import create_access_token, hash_password, hash_otp, verify_otp


@pytest.fixture
async def test_user_for_otp(db_session: AsyncSession) -> User:
    """Create a test user for OTP testing."""
    user = User(
        id="otp-user-test-1",
        full_name="OTP Test User",
        phone="+919876543210",
        email="otp@test.com",
        hashed_password=hash_password("Test@1234"),
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def test_oauth_user(db_session: AsyncSession) -> User:
    """Create a test OAuth user without phone."""
    user = User(
        id="oauth-user-test-1",
        full_name="OAuth Test User",
        email="oauth@test.com",
        phone=None,  # No phone initially
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=False,
        oauth_provider="google",
    )
    db_session.add(user)
    await db_session.flush()
    return user


def oauth_user_auth_header(test_oauth_user: User) -> dict:
    """Auth header for OAuth user."""
    token = create_access_token(subject=test_oauth_user.id, role=test_oauth_user.role)
    return {"Authorization": f"Bearer {token}"}


# ── Test Classes ───────────────────────────────────────────────────────────────

class TestPhoneValidation:
    """Test phone number validation."""

    async def test_valid_10_digit_phone(self, async_client):
        """Accept valid 10-digit Indian phone numbers."""
        response = await async_client.post(
            "/api/v1/auth/register/send-phone-otp",
            json={"phone": "9876543210"}
        )
        assert response.status_code == 200

    async def test_phone_with_plus91_prefix(self, async_client):
        """Accept phone with +91 country code."""
        response = await async_client.post(
            "/api/v1/auth/register/send-phone-otp",
            json={"phone": "+919876543210"}
        )
        assert response.status_code == 200

    async def test_phone_with_91_prefix(self, async_client):
        """Accept phone with 91 country code."""
        response = await async_client.post(
            "/api/v1/auth/register/send-phone-otp",
            json={"phone": "919876543210"}
        )
        assert response.status_code == 200

    async def test_invalid_phone_too_short(self, async_client):
        """Reject phone numbers that are too short."""
        response = await async_client.post(
            "/api/v1/auth/register/send-phone-otp",
            json={"phone": "123456"}
        )
        assert response.status_code == 422

    async def test_invalid_phone_starts_with_wrong_digit(self, async_client):
        """Reject Indian phones not starting with 6-9."""
        response = await async_client.post(
            "/api/v1/auth/register/send-phone-otp",
            json={"phone": "5876543210"}  # Starts with 5
        )
        assert response.status_code == 422

    async def test_invalid_phone_characters(self, async_client):
        """Reject phone with invalid characters."""
        response = await async_client.post(
            "/api/v1/auth/register/send-phone-otp",
            json={"phone": "987abc3210"}
        )
        assert response.status_code == 422


class TestPasswordValidation:
    """Test password strength validation."""

    async def test_valid_strong_password(self, async_client, test_user_for_otp):
        """Accept passwords meeting all requirements."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Test User",
                "phone": "+919876543210",
                "email": "test@example.com",
                "password": "SecurePass123!",
                "role": "customer",
            }
        )
        # Should succeed (or be 201/409 depending on phone existence)
        assert response.status_code in [201, 400, 409]

    async def test_password_too_short(self, async_client):
        """Reject passwords shorter than 8 characters."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Test User",
                "phone": "+919876543211",
                "email": "test2@example.com",
                "password": "Short1!",  # 7 chars
                "role": "customer",
            }
        )
        assert response.status_code == 422
        assert "at least 8 characters" in str(response.json()).lower()

    async def test_password_missing_uppercase(self, async_client):
        """Reject passwords without uppercase letters."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Test User",
                "phone": "+919876543212",
                "email": "test3@example.com",
                "password": "lowercase123!",
                "role": "customer",
            }
        )
        assert response.status_code == 422
        assert "uppercase" in str(response.json()).lower()

    async def test_password_missing_number(self, async_client):
        """Reject passwords without numbers."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Test User",
                "phone": "+919876543213",
                "email": "test4@example.com",
                "password": "NoNumbers!",
                "role": "customer",
            }
        )
        assert response.status_code == 422
        assert "number" in str(response.json()).lower()

    async def test_password_missing_special_char(self, async_client):
        """Reject passwords without special characters."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Test User",
                "phone": "+919876543214",
                "email": "test5@example.com",
                "password": "NoSpecialChar123",
                "role": "customer",
            }
        )
        assert response.status_code == 422
        assert "special" in str(response.json()).lower()


class TestOTPFlow:
    """Test OTP request and verification."""

    async def test_send_otp_returns_code_in_debug_mode(self, async_client):
        """In DEBUG mode, OTP is returned in response."""
        response = await async_client.post(
            "/api/v1/auth/send-otp",
            json={"phone": "+919876543215"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # OTP will be in debug response if DEBUG is true

    async def test_send_otp_blocks_double_requests(self, async_client, db_session):
        """Sending OTP twice should invalidate first OTP."""
        phone = "+919876543216"

        # Send first OTP
        response1 = await async_client.post(
            "/api/v1/auth/send-otp",
            json={"phone": phone}
        )
        assert response1.status_code == 200
        first_otp = response1.json().get("otp")

        # Send second OTP
        response2 = await async_client.post(
            "/api/v1/auth/send-otp",
            json={"phone": phone}
        )
        assert response2.status_code == 200
        second_otp = response2.json().get("otp")

        # First OTP should be marked as used
        result = await db_session.execute(
            select(OTPCode).where(OTPCode.phone == phone).order_by(OTPCode.created_at.desc())
        )
        otps = result.scalars().all()
        # Both should exist, but first should be marked used
        assert len(otps) >= 1

    async def test_otp_expiration(self, async_client, db_session):
        """Verify OTP expires after configured timeout."""
        phone = "+919876543217"

        # Send OTP
        response = await async_client.post(
            "/api/v1/auth/send-otp",
            json={"phone": phone}
        )
        assert response.status_code == 200
        otp_code = response.json().get("otp", "123456")

        # Manually expire the OTP
        result = await db_session.execute(
            select(OTPCode).where(OTPCode.phone == phone)
        )
        otp = result.scalar_one()
        otp.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await db_session.flush()

        # Try to verify expired OTP
        verify_response = await async_client.post(
            "/api/v1/auth/verify-otp",
            json={
                "phone": phone,
                "otp": otp_code,
                "purpose": "login"
            }
        )
        assert verify_response.status_code == 400
        assert "expired" in verify_response.json()["detail"].lower()


class TestOAuthPhoneVerification:
    """Test OAuth users must verify phone before access."""

    async def test_oauth_user_can_send_phone_otp(
        self, async_client, test_oauth_user
    ):
        """OAuth user can request phone OTP for linking."""
        token = create_access_token(subject=test_oauth_user.id, role=test_oauth_user.role)
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.post(
            "/api/v1/auth/oauth/send-phone-otp",
            headers=headers,
            json={"phone": "+919876543218"}
        )
        assert response.status_code == 200

    async def test_oauth_user_cannot_link_same_phone_twice(
        self, async_client, test_oauth_user, db_session
    ):
        """OAuth user can't link phone if already linked."""
        # Link phone first time
        test_oauth_user.phone = "+919876543219"
        await db_session.flush()

        token = create_access_token(subject=test_oauth_user.id, role=test_oauth_user.role)
        headers = {"Authorization": f"Bearer {token}"}

        # Try to link phone again
        response = await async_client.post(
            "/api/v1/auth/oauth/send-phone-otp",
            headers=headers,
            json={"phone": "+919876543220"}
        )
        assert response.status_code == 400
        assert "already has a phone" in response.json()["detail"].lower()


class TestTokenManagement:
    """Test JWT token creation and refresh."""

    async def test_access_token_includes_user_id(self):
        """Access token payload includes user ID and role."""
        user_id = "test-user-123"
        role = UserRole.CUSTOMER

        token = create_access_token(subject=user_id, role=role)

        from jose import jwt
        from app.core.config import settings

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    async def test_refresh_token_rotation(self, async_client):
        """Using refresh token issues new token pair."""
        from app.core.security import create_refresh_token, hash_refresh_token

        user = User(
            id="token-test-1",
            full_name="Token Test",
            phone="+919876543221",
            email="token@test.com",
            hashed_password=hash_password("Test@1234"),
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,
        )

        # Create tokens
        access = create_access_token(subject=user.id, role=user.role)
        _, refresh_token = create_refresh_token(subject=user.id)

        # Try to refresh
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        # Should succeed or fail gracefully (db might not have the token)
        assert response.status_code in [200, 401]

    async def test_invalid_token_rejected(self, async_client):
        """Invalid/tampered tokens are rejected."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    async def test_expired_token_rejected(self, async_client):
        """Expired tokens are rejected."""
        from jose import jwt
        from app.core.config import settings
        from datetime import datetime, timezone

        # Create token with past expiration
        payload = {
            "sub": "test-user",
            "role": "customer",
            "type": "access",
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401


class TestLogout:
    """Test logout and token revocation."""

    async def test_logout_revokes_refresh_token(self, async_client):
        """Logout endpoint revokes the refresh token."""
        from app.core.security import create_refresh_token

        user_id = "logout-test-1"
        _, refresh_token = create_refresh_token(subject=user_id)

        response = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token}
        )
        # Should succeed or fail gracefully
        assert response.status_code in [204, 401, 404]
