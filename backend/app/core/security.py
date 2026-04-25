"""
app/core/security.py
────────────────────
All cryptographic operations live here — single source of truth for:
  • Password hashing (bcrypt)
  • JWT creation / verification (access + refresh)
  • OTP generation and hashing
  • Refresh token hashing (SHA-256)
"""

import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: str, role: str, extra: dict | None = None) -> str:
    """
    Create a short-lived access token.
    `subject` = user UUID.
    """
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": _now_utc(),
        "exp": _now_utc() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    """
    Returns (raw_token, expires_at).
    Store only the hash of raw_token in the DB.
    """
    expires_at = _now_utc() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": _now_utc(),
        "exp": expires_at,
        # jti adds uniqueness per token issuance
        "jti": secrets.token_hex(16),
    }
    raw = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return raw, expires_at


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT. Raises JWTError on failure.
    Callers should handle JWTError and return 401.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ── Refresh token hashing ─────────────────────────────────────────────────────

def hash_refresh_token(raw_token: str) -> str:
    """SHA-256 hash of the raw JWT string — stored in DB."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def verify_refresh_token_hash(raw_token: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_refresh_token(raw_token), stored_hash)


# ── OTP ───────────────────────────────────────────────────────────────────────

def generate_otp(length: int = 6) -> str:
    """Cryptographically secure numeric OTP."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def hash_otp(otp: str) -> str:
    """bcrypt hash of OTP — stored in DB, not the raw OTP."""
    return pwd_context.hash(otp)


def verify_otp(plain_otp: str, hashed: str) -> bool:
    return pwd_context.verify(plain_otp, hashed)


# ── Razorpay webhook signature verification ───────────────────────────────────

def verify_razorpay_signature(
    order_id: str,
    payment_id: str,
    signature: str,
) -> bool:
    """
    Razorpay expects:
        HMAC-SHA256( order_id + "|" + payment_id, key_secret )
    """
    message = f"{order_id}|{payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
