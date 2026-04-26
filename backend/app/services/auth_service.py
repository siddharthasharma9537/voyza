"""
app/services/auth_service.py
─────────────────────────────
Pure business logic — no HTTP/FastAPI imports.
This separation allows easy unit testing without spinning up a server.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    hash_otp,
    hash_password,
    hash_refresh_token,
    verify_otp,
    verify_password,
    verify_refresh_token_hash,
)
from app.models.models import OTPCode, RefreshToken, User, UserRole
from app.schemas.auth import RegisterRequest, TokenResponse


# ── OTP ───────────────────────────────────────────────────────────────────────

async def send_otp(phone: str, purpose: str, db: AsyncSession) -> str:
    """
    Generate OTP, store its hash, and return the raw OTP for sending via SMS.
    In production, the caller dispatches the SMS via Twilio/AWS SNS.
    Returns the raw OTP (only for dev/test — do NOT log in production).
    """
    # Invalidate any prior unused OTPs for this phone+purpose
    existing = await db.execute(
        select(OTPCode).where(
            OTPCode.phone == phone,
            OTPCode.purpose == purpose,
            OTPCode.is_used.is_(False),
        )
    )
    for old in existing.scalars().all():
        old.is_used = True  # soft-invalidate

    raw_otp = generate_otp()
    otp_record = OTPCode(
        phone=phone,
        code_hash=hash_otp(raw_otp),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        is_used=False,
        purpose=purpose,
    )
    db.add(otp_record)
    await db.flush()
    return raw_otp


async def verify_otp_code(phone: str, otp: str, purpose: str, db: AsyncSession) -> bool:
    """Verify OTP; marks it used on success. Raises 400 on failure."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(OTPCode)
        .where(
            OTPCode.phone == phone,
            OTPCode.purpose == purpose,
            OTPCode.is_used.is_(False),
            OTPCode.expires_at > now,
        )
        .order_by(OTPCode.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()

    if not record or not verify_otp(otp, record.code_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    record.is_used = True
    await db.flush()
    return True


# ── Registration ──────────────────────────────────────────────────────────────

async def register_user(data: RegisterRequest, db: AsyncSession) -> User:
    # Check phone uniqueness
    existing = await db.execute(select(User).where(User.phone == data.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Check email uniqueness if provided
    if data.email:
        existing_email = await db.execute(select(User).where(User.email == data.email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=data.full_name,
        phone=data.phone,
        email=data.email,
        hashed_password=hash_password(data.password) if data.password else None,
        role=UserRole(data.role),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    return user


# ── Token issuance ────────────────────────────────────────────────────────────

async def _issue_tokens(user: User, db: AsyncSession, device_info: str | None = None) -> TokenResponse:
    """Create access + refresh tokens; persist hashed refresh token."""
    access = create_access_token(subject=user.id, role=user.role)
    raw_refresh, expires_at = create_refresh_token(subject=user.id)

    # Revoke any existing tokens for this device (optional; helps limit concurrent sessions)
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=expires_at,
        revoked=False,
        device_info=device_info,
    )
    db.add(token_record)
    await db.flush()

    return TokenResponse(
        access_token=access,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def login_with_password(phone: str, password: str, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.phone == phone, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect phone or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")

    return await _issue_tokens(user, db)


async def login_with_email_and_password(email: str, password: str, db: AsyncSession) -> TokenResponse:
    """Login using email and password."""
    result = await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")

    return await _issue_tokens(user, db)


async def login_with_otp(phone: str, db: AsyncSession) -> TokenResponse:
    """Called after OTP has already been verified."""
    result = await db.execute(select(User).where(User.phone == phone, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found — please register first")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")

    # Auto-verify on OTP login
    if not user.is_verified:
        user.is_verified = True

    return await _issue_tokens(user, db)


async def refresh_access_token(raw_refresh_token: str, db: AsyncSession) -> TokenResponse:
    """Rotate refresh tokens — each refresh issues a new pair."""
    from jose import JWTError
    from app.core.security import decode_token

    try:
        payload = decode_token(raw_refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Wrong token type")
        user_id = payload["sub"]
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired or revoked")

    # Revoke old token
    stored.revoked = True

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive")

    return await _issue_tokens(user, db)


# ── Phone Registration ─────────────────────────────────────────────────────────

async def register_with_phone(
    phone: str,
    full_name: str,
    email: str,
    role: str,
    db: AsyncSession,
) -> User:
    """
    Create user account after phone OTP verification.
    Phone is pre-verified, email can be verified later.
    """
    # Check phone uniqueness
    existing_phone = await db.execute(select(User).where(User.phone == phone))
    if existing_phone.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Check email uniqueness if provided
    if email:
        existing_email = await db.execute(select(User).where(User.email == email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=full_name,
        phone=phone,
        email=email,
        role=UserRole(role),
        is_active=True,
        is_verified=True,  # Phone verified
        email_verified=False,  # Email not yet verified
        oauth_provider="phone",
    )
    db.add(user)
    await db.flush()
    return user


async def verify_email_otp_for_user(
    email: str,
    otp: str,
    db: AsyncSession,
) -> User:
    """
    Verify email OTP and mark email as verified.
    Called after account creation.
    """
    # Verify OTP
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(OTPCode)
        .where(
            OTPCode.phone == email,  # Store email OTP with phone column for now
            OTPCode.purpose == "email_verification",
            OTPCode.is_used.is_(False),
            OTPCode.expires_at > now,
        )
        .order_by(OTPCode.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()

    if not record or not verify_otp(otp, record.code_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    record.is_used = True

    # Find user by email and mark verified
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.email_verified = True
    await db.flush()
    return user
