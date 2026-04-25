"""
tests/unit/test_auth_service.py
────────────────────────────────
Unit tests for security utilities and auth service logic.
These tests do NOT require a running database — pure Python.
"""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    hash_otp,
    hash_password,
    hash_refresh_token,
    verify_otp,
    verify_password,
    verify_refresh_token_hash,
)


# ── Password ──────────────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plain(self):
        hashed = hash_password("MySecret123!")
        assert hashed != "MySecret123!"

    def test_correct_password_verifies(self):
        hashed = hash_password("MySecret123!")
        assert verify_password("MySecret123!", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("MySecret123!")
        assert verify_password("wrong", hashed) is False

    def test_different_hashes_for_same_password(self):
        """bcrypt uses random salt — same password → different hash each time."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


# ── JWT ───────────────────────────────────────────────────────────────────────

class TestJWT:
    def test_access_token_payload(self):
        token = create_access_token(subject="user-123", role="customer")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["role"] == "customer"
        assert payload["type"] == "access"

    def test_refresh_token_payload(self):
        raw, expires_at = create_refresh_token(subject="user-123")
        payload = decode_token(raw)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"
        assert "jti" in payload  # unique per issuance

    def test_expired_token_raises(self):
        from jose import JWTError

        payload = {
            "sub": "user-123",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        with pytest.raises(JWTError):
            decode_token(expired_token)

    def test_tampered_token_raises(self):
        from jose import JWTError

        token = create_access_token(subject="user-123", role="customer")
        tampered = token[:-5] + "XXXXX"

        with pytest.raises(JWTError):
            decode_token(tampered)


# ── OTP ───────────────────────────────────────────────────────────────────────

class TestOTP:
    def test_otp_is_6_digits(self):
        otp = generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()

    def test_otp_verification_succeeds(self):
        otp = generate_otp()
        hashed = hash_otp(otp)
        assert verify_otp(otp, hashed) is True

    def test_wrong_otp_fails(self):
        otp = generate_otp()
        hashed = hash_otp(otp)
        assert verify_otp("000000", hashed) is False

    def test_otps_are_unique(self):
        otps = {generate_otp() for _ in range(100)}
        # With 6 digits (10^6 possibilities), 100 samples should almost certainly be unique
        assert len(otps) > 90


# ── Refresh Token Hashing ─────────────────────────────────────────────────────

class TestRefreshTokenHashing:
    def test_hash_is_deterministic(self):
        raw = "some.jwt.token"
        assert hash_refresh_token(raw) == hash_refresh_token(raw)

    def test_verify_matches(self):
        raw = "some.jwt.token"
        stored = hash_refresh_token(raw)
        assert verify_refresh_token_hash(raw, stored) is True

    def test_wrong_token_fails(self):
        stored = hash_refresh_token("correct.token")
        assert verify_refresh_token_hash("wrong.token", stored) is False
