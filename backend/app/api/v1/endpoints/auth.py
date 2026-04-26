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

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.models import User
from app.schemas.auth import (
    EmailVerificationStartRequest,
    EmailVerificationVerifyRequest,
    GoogleOAuthCallbackRequest,
    LoginRequest,
    OAuthLinkPhoneRequest,
    OAuthSetPasswordRequest,
    PhoneRegistrationStartRequest,
    PhoneRegistrationVerifyRequest,
    PhoneSendOTPRequest,
    PhoneVerifyOTPRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegistrationCompleteResponse,
    TokenResponse,
    UserResponse,
    OAuthTokenResponse,
)
from app.services import auth_service, oauth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Phone Registration Flow ───────────────────────────────────────────────────

@router.post("/register/send-phone-otp", status_code=status.HTTP_200_OK)
async def register_send_phone_otp(
    body: PhoneRegistrationStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start phone-based registration: send OTP to phone.
    User must verify OTP before account creation.
    """
    raw_otp = await auth_service.send_otp(
        phone=body.phone,
        purpose="registration",
        db=db,
    )

    from app.core.config import settings
    response = {"message": "OTP sent successfully to phone"}
    if settings.DEBUG:
        response["otp"] = raw_otp
    return response


@router.post("/register/verify-phone", response_model=RegistrationCompleteResponse, status_code=status.HTTP_201_CREATED)
async def register_verify_phone(
    body: PhoneRegistrationVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify phone OTP and create account.
    Email can be verified later.
    """
    # Verify OTP
    await auth_service.verify_otp_code(
        phone=body.phone,
        otp=body.otp,
        purpose="registration",
        db=db,
    )

    # Create user
    user = await auth_service.register_with_phone(
        phone=body.phone,
        full_name=body.full_name,
        email=body.email,
        role=body.role,
        db=db,
    )
    await db.commit()

    return RegistrationCompleteResponse.model_validate(user)


@router.post("/register/send-email-otp", status_code=status.HTTP_200_OK)
async def register_send_email_otp(
    body: EmailVerificationStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send email verification OTP.
    This is optional and can be done after registration.
    """
    # For now, store email OTP in otp_codes table with email as the "phone"
    raw_otp = await auth_service.send_otp(
        phone=body.email,  # Use email as phone for lookup
        purpose="email_verification",
        db=db,
    )

    from app.core.config import settings
    response = {"message": "OTP sent successfully to email"}
    if settings.DEBUG:
        response["otp"] = raw_otp
    return response


@router.post("/register/verify-email", response_model=UserResponse)
async def register_verify_email(
    body: EmailVerificationVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email OTP and mark email as verified.
    This is optional.
    """
    user = await auth_service.verify_email_otp_for_user(
        email=body.email,
        otp=body.otp,
        db=db,
    )
    await db.commit()

    return UserResponse.model_validate(user)


# ── Login Endpoints ───────────────────────────────────────────────────────────

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
    """
    Password-based login using either phone or email.
    Returns access + refresh tokens.
    """
    if body.phone:
        return await auth_service.login_with_password(
            phone=body.phone,
            password=body.password,
            db=db,
        )
    elif body.email:
        return await auth_service.login_with_email_and_password(
            email=body.email,
            password=body.password,
            db=db,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either phone or email must be provided",
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


# ── OAuth Endpoints ───────────────────────────────────────────────────────────

@router.get("/oauth/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Google OAuth callback endpoint.
    Frontend redirects here after user authorizes.
    Exchanges code for token and creates/links user account.
    """
    from app.core.config import settings

    # Exchange code for token
    oauth_data = await oauth_service.exchange_google_code(
        code=code,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )

    # Find or create user
    user = await oauth_service.find_or_create_oauth_user(
        provider=oauth_data["provider"],
        provider_id=oauth_data["provider_id"],
        email=oauth_data["email"],
        full_name=oauth_data.get("name", ""),
        role="customer",
        db=db,
    )
    await db.commit()

    # Issue temporary token (user still needs to link phone and set password)
    temp_tokens = await auth_service._issue_tokens(user, db)
    await db.commit()

    return OAuthTokenResponse(
        access_token=temp_tokens.access_token,
        token_type="bearer",
        expires_in=temp_tokens.expires_in,
        message="Phone verification required to complete signup",
    )


@router.get("/oauth/apple/callback")
async def apple_oauth_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Apple OAuth callback endpoint.
    Frontend redirects here after user authorizes.
    """
    # Exchange code for token
    oauth_data = await oauth_service.exchange_apple_code(code=code)

    # Find or create user
    user = await oauth_service.find_or_create_oauth_user(
        provider=oauth_data["provider"],
        provider_id=oauth_data["provider_id"],
        email=oauth_data["email"],
        full_name="",
        role="customer",
        db=db,
    )
    await db.commit()

    # Issue temporary token
    temp_tokens = await auth_service._issue_tokens(user, db)
    await db.commit()

    return OAuthTokenResponse(
        access_token=temp_tokens.access_token,
        token_type="bearer",
        expires_in=temp_tokens.expires_in,
        message="Phone verification required to complete signup",
    )


@router.get("/oauth/facebook/callback")
async def facebook_oauth_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Facebook OAuth callback endpoint.
    Frontend redirects here after user authorizes.
    """
    from app.core.config import settings

    # Exchange code for token
    oauth_data = await oauth_service.exchange_facebook_code(
        code=code,
        redirect_uri=settings.FACEBOOK_REDIRECT_URI,
    )

    # Find or create user
    user = await oauth_service.find_or_create_oauth_user(
        provider=oauth_data["provider"],
        provider_id=oauth_data["provider_id"],
        email=oauth_data["email"],
        full_name=oauth_data.get("name", ""),
        role="customer",
        db=db,
    )
    await db.commit()

    # Issue temporary token
    temp_tokens = await auth_service._issue_tokens(user, db)
    await db.commit()

    return OAuthTokenResponse(
        access_token=temp_tokens.access_token,
        token_type="bearer",
        expires_in=temp_tokens.expires_in,
        message="Phone verification required to complete signup",
    )


@router.post("/oauth/link-phone", response_model=UserResponse)
async def oauth_link_phone(
    body: OAuthLinkPhoneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Link phone number to OAuth account (after OTP verification).
    Requires authentication (from OAuth callback).
    """
    # Verify phone OTP
    await auth_service.verify_otp_code(
        phone=body.phone,
        otp=body.otp,
        purpose="oauth_phone_linking",
        db=db,
    )

    # Link phone to OAuth user
    user = await oauth_service.link_oauth_to_phone(
        user_id=str(current_user.id),
        phone=body.phone,
        db=db,
    )
    await db.commit()

    return UserResponse.model_validate(user)


@router.post("/oauth/set-password", response_model=UserResponse)
async def oauth_set_password(
    body: OAuthSetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Set password for OAuth user (backup authentication).
    Requires authentication (from OAuth callback).
    """
    if not current_user.oauth_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for OAuth users",
        )

    user = await oauth_service.set_oauth_password(
        user_id=str(current_user.id),
        password=body.password,
        db=db,
    )
    await db.commit()

    return UserResponse.model_validate(user)
