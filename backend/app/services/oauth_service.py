"""
app/services/oauth_service.py
──────────────────────────────
OAuth token exchange and account linking logic.
Handles Google, Apple, and Facebook OAuth flows with proper JWT verification.
"""

import json
from typing import Optional
from functools import lru_cache

import requests
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jwt import decode as jwt_decode, PyJWTError

from app.core.config import settings
from app.core.security import hash_password
from app.models.models import User, UserRole


# ── JWKS Caching (for Google public keys) ─────────────────────────────────────

@lru_cache(maxsize=1)
def _get_google_jwks() -> dict:
    """Fetch and cache Google's JWKS (public keys) for verifying ID tokens."""
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v3/certs",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Google JWKS: {str(e)}",
        )


def _get_google_key(kid: str) -> Optional[dict]:
    """Get a specific public key from Google's JWKS by key ID."""
    try:
        jwks = _get_google_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse Google keys: {str(e)}",
        )


# ── Google OAuth ──────────────────────────────────────────────────────────────

async def exchange_google_code(code: str, redirect_uri: str) -> dict:
    """
    Exchange Google authorization code for ID token and verify signature.
    Returns decoded ID token with email, name, google_id.
    Raises HTTPException if code is invalid or signature verification fails.
    """
    token_url = "https://oauth2.googleapis.com/token"

    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        response = requests.post(token_url, json=payload, timeout=10)
        response.raise_for_status()
        token_data = response.json()

        if "id_token" not in token_data:
            raise ValueError("Missing id_token in response")

        id_token = token_data["id_token"]

        # Verify JWT signature using Google's public keys
        try:
            # Get the key ID from JWT header
            header_part = id_token.split(".")[0]
            import base64
            padding = 4 - (len(header_part) % 4)
            if padding != 4:
                header_part += "=" * padding
            header = json.loads(base64.urlsafe_b64decode(header_part))
            kid = header.get("kid")

            if not kid:
                raise ValueError("Missing 'kid' in JWT header")

            # Get the public key
            google_key = _get_google_key(kid)
            if not google_key:
                raise ValueError(f"Could not find key with ID: {kid}")

            # Convert JWK to PEM format for verification
            from jwt.algorithms import RSAAlgorithm
            public_key = RSAAlgorithm.from_jwk(json.dumps(google_key))

            # Verify the token signature
            id_token_data = jwt_decode(
                id_token,
                public_key,
                algorithms=["RS256"],
                audience=settings.GOOGLE_CLIENT_ID,
                options={"verify_signature": True}
            )

            # Additional validation
            if not id_token_data.get("email_verified"):
                raise ValueError("Email not verified by Google")

            return {
                "provider": "google",
                "provider_id": id_token_data.get("sub"),
                "email": id_token_data.get("email"),
                "name": id_token_data.get("name"),
            }

        except PyJWTError as e:
            raise ValueError(f"JWT verification failed: {str(e)}")

    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange Google code: {str(e)}",
        )
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode Google token: {str(e)}",
        )


# ── Apple OAuth ───────────────────────────────────────────────────────────────

async def exchange_apple_code(code: str) -> dict:
    """
    Exchange Apple authorization code for ID token and verify signature.
    Returns decoded user data with email, apple_id.
    Raises HTTPException if code is invalid or signature verification fails.
    """
    from datetime import datetime, timedelta, timezone
    import jwt as pyjwt

    token_url = "https://appleid.apple.com/auth/token"

    # Validate Apple configuration
    if not settings.APPLE_PRIVATE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Apple OAuth not configured: missing APPLE_PRIVATE_KEY",
        )

    # Generate client secret (JWT) using the private key
    now = datetime.now(timezone.utc)
    client_secret_payload = {
        "iss": settings.APPLE_TEAM_ID,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "aud": "https://appleid.apple.com",
        "sub": settings.APPLE_CLIENT_ID,
    }

    try:
        client_secret = pyjwt.encode(
            client_secret_payload,
            settings.APPLE_PRIVATE_KEY,
            algorithm="ES256",
            headers={"kid": settings.APPLE_KEY_ID},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Apple client secret: {str(e)}",
        )

    payload = {
        "client_id": settings.APPLE_CLIENT_ID,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
    }

    try:
        response = requests.post(token_url, json=payload, timeout=10)
        response.raise_for_status()
        token_data = response.json()

        if "id_token" not in token_data:
            raise ValueError("Missing id_token in response")

        id_token = token_data["id_token"]

        # Fetch Apple's public keys for verification
        jwks_response = requests.get(
            "https://appleid.apple.com/auth/keys",
            timeout=10,
        )
        jwks_response.raise_for_status()
        apple_jwks = jwks_response.json()

        # Get the key ID from JWT header
        header_part = id_token.split(".")[0]
        import base64
        padding = 4 - (len(header_part) % 4)
        if padding != 4:
            header_part += "=" * padding
        header = json.loads(base64.urlsafe_b64decode(header_part))
        kid = header.get("kid")

        if not kid:
            raise ValueError("Missing 'kid' in JWT header")

        # Find the matching public key
        apple_key = None
        for key in apple_jwks.get("keys", []):
            if key.get("kid") == kid:
                apple_key = key
                break

        if not apple_key:
            raise ValueError(f"Could not find Apple key with ID: {kid}")

        # Convert JWK to PEM format and verify signature
        from jwt.algorithms import RSAAlgorithm
        public_key = RSAAlgorithm.from_jwk(json.dumps(apple_key))

        try:
            id_token_data = jwt_decode(
                id_token,
                public_key,
                algorithms=["RS256"],
                audience=settings.APPLE_CLIENT_ID,
                options={"verify_signature": True}
            )
        except PyJWTError as e:
            raise ValueError(f"JWT verification failed: {str(e)}")

        return {
            "provider": "apple",
            "provider_id": id_token_data.get("sub"),
            "email": id_token_data.get("email"),
        }

    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange Apple code: {str(e)}",
        )
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode Apple token: {str(e)}",
        )


# ── Facebook OAuth ────────────────────────────────────────────────────────────

async def exchange_facebook_code(code: str, redirect_uri: str) -> dict:
    """
    Exchange Facebook authorization code for access token.
    Returns user data with email, facebook_id.
    Raises HTTPException if code is invalid.
    """
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    user_url = "https://graph.facebook.com/me"

    try:
        # Step 1: Exchange code for access token
        token_params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        token_response = requests.get(token_url, params=token_params, timeout=10)
        token_response.raise_for_status()
        token_data = token_response.json()

        if "access_token" not in token_data:
            raise ValueError("Missing access_token in response")

        access_token = token_data["access_token"]

        # Step 2: Get user info using access token
        user_params = {
            "fields": "id,email,name",
            "access_token": access_token,
        }
        user_response = requests.get(user_url, params=user_params, timeout=10)
        user_response.raise_for_status()
        user_data = user_response.json()

        return {
            "provider": "facebook",
            "provider_id": user_data.get("id"),
            "email": user_data.get("email"),
            "name": user_data.get("name"),
        }

    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange Facebook code: {str(e)}",
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode Facebook response: {str(e)}",
        )


# ── OAuth Account Management ──────────────────────────────────────────────────

async def find_or_create_oauth_user(
    provider: str,
    provider_id: str,
    email: str,
    full_name: str,
    role: str = "customer",
    db: AsyncSession = None,
) -> User:
    """
    Find existing user by OAuth provider ID or email, or create new user.
    Returns user with phone_verified=False (must verify phone before using).
    """
    if not db:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session not provided",
        )

    # Check if user with this OAuth provider ID exists
    if provider == "google":
        result = await db.execute(select(User).where(User.google_id == provider_id))
        existing = result.scalar_one_or_none()
        if existing:
            return existing
    elif provider == "apple":
        result = await db.execute(select(User).where(User.apple_id == provider_id))
        existing = result.scalar_one_or_none()
        if existing:
            return existing
    elif provider == "facebook":
        result = await db.execute(select(User).where(User.facebook_id == provider_id))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Check if user with this email exists
    if email:
        result = await db.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            # Link OAuth provider to existing user
            if provider == "google":
                existing.google_id = provider_id
            elif provider == "apple":
                existing.apple_id = provider_id
            elif provider == "facebook":
                existing.facebook_id = provider_id
            await db.flush()
            return existing

    # Create new user with temporary phone (will be verified later)
    new_user = User(
        full_name=full_name or email.split("@")[0],
        email=email,
        phone="",  # Placeholder — must be verified before account is usable
        role=UserRole(role),
        is_active=True,
        is_verified=False,  # Not phone verified
        email_verified=True,  # Email verified via OAuth provider
        oauth_provider=provider,
    )

    # Link OAuth provider ID
    if provider == "google":
        new_user.google_id = provider_id
    elif provider == "apple":
        new_user.apple_id = provider_id
    elif provider == "facebook":
        new_user.facebook_id = provider_id

    db.add(new_user)
    await db.flush()
    return new_user


async def link_oauth_to_phone(
    user_id: str,
    phone: str,
    db: AsyncSession,
) -> User:
    """
    Link phone number to OAuth user (after phone OTP verification).
    Returns updated user.
    """
    # Check phone uniqueness
    result = await db.execute(select(User).where(User.phone == phone))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    # Get user and link phone
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.phone = phone
    user.is_verified = True  # Mark phone verified
    await db.flush()
    return user


async def set_oauth_password(
    user_id: str,
    password: str,
    db: AsyncSession,
) -> User:
    """
    Set password for OAuth user (backup authentication).
    Returns updated user.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.hashed_password = hash_password(password)
    await db.flush()
    return user
