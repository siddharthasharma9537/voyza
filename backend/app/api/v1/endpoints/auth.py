"""
app/api/v1/endpoints/auth.py
─────────────────────────────
Auth endpoints:
  POST /auth/send-otp         — request OTP for phone
  POST /auth/verify-otp       — verify OTP → login or mark verified
  POST /auth/register         — email+password registration
  POST /auth/login            — password login
  POST /auth/refresh          — refresh access token
  POST /auth/logout           — revoke refresh token
  GET  /auth/me               — get current user profile
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.models import User
from app.schemas.auth import (
    LoginRequest,
    PhoneSendOTPRequest,
    PhoneVerifyOTPRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(
    body: PhoneSendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a 6-digit OTP to the given phone number.
    Rate-limited via middleware (60 req/min per IP).
    """
    raw_otp = await auth_service.send_otp(
        phone=body.phone,
        purpose="login",
        db=db,
    )

    # TODO: Dispatch SMS via Twilio / AWS SNS
    # In dev mode, return OTP in response for testing
    from app.core.config import settings
    response = {"message": "OTP sent successfully"}
    if settings.DEBUG:
        response["otp"] = raw_otp   # NEVER in production
    return response


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    body: PhoneVerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP and return JWT tokens (login or phone verification)."""
    await auth_service.verify_otp_code(
        phone=body.phone,
        otp=body.otp,
        purpose=body.purpose,
        db=db,
    )

    if body.purpose == "login":
        return await auth_service.login_with_otp(phone=body.phone, db=db)

    return {"message": "Phone verified successfully"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new customer or owner account."""
    user = await auth_service.register_user(data=body, db=db)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Password-based login (returns access + refresh tokens)."""
    return await auth_service.login_with_password(
        phone=body.phone,
        password=body.password,
        db=db,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate refresh token.
    Old refresh token is revoked; new pair is issued.
    """
    return await auth_service.refresh_access_token(
        raw_refresh_token=body.refresh_token,
        db=db,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Revoke the given refresh token (client should also discard the access token)."""
    from app.core.security import hash_refresh_token
    from sqlalchemy import select
    from app.models.models import RefreshToken

    token_hash = hash_refresh_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()
    if stored:
        stored.revoked = True


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
