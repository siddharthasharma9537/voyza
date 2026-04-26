"""
app/schemas/auth.py
───────────────────
Request / Response schemas for auth endpoints.
Pydantic v2 with strict validation.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class PhoneSendOTPRequest(BaseModel):
    phone: str = Field(..., examples=["9876543210"])

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Accept 10-digit Indian phone numbers
        v = v.strip()
        # Remove country code if present
        if v.startswith("+91"):
            v = v[3:]
        elif v.startswith("91"):
            v = v[2:]
        # Validate 10-digit Indian number
        pattern = r"^[6-9]\d{9}$"
        if not re.match(pattern, v):
            raise ValueError("Phone must be a valid 10-digit Indian number, e.g. 9876543210")
        # Convert to E.164 format for storage
        return f"+91{v}"


class PhoneVerifyOTPRequest(BaseModel):
    phone: str
    otp:   str = Field(..., min_length=6, max_length=6)
    purpose: str = Field(default="login", pattern="^(login|verify)$")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Accept 10-digit Indian phone numbers
        v = v.strip()
        # Remove country code if present
        if v.startswith("+91"):
            v = v[3:]
        elif v.startswith("91"):
            v = v[2:]
        # Validate 10-digit Indian number
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Phone must be a valid 10-digit Indian number, e.g. 9876543210")
        # Convert to E.164 format for storage
        return f"+91{v}"


class RegisterRequest(BaseModel):
    full_name: str   = Field(..., min_length=2, max_length=120)
    phone:     str
    email:     EmailStr | None = None
    password:  str | None      = Field(default=None, min_length=8)
    role:      str             = Field(default="customer", pattern="^(customer|owner)$")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Accept 10-digit Indian phone numbers
        v = v.strip()
        # Remove country code if present
        if v.startswith("+91"):
            v = v[3:]
        elif v.startswith("91"):
            v = v[2:]
        # Validate 10-digit Indian number
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Phone must be a valid 10-digit Indian number, e.g. 9876543210")
        # Convert to E.164 format for storage
        return f"+91{v}"


class LoginRequest(BaseModel):
    phone:    str | None = None
    email:    EmailStr | None = None
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        # Accept 10-digit Indian phone numbers
        v = v.strip()
        # Remove country code if present
        if v.startswith("+91"):
            v = v[3:]
        elif v.startswith("91"):
            v = v[2:]
        # Validate 10-digit Indian number
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Phone must be a valid 10-digit Indian number, e.g. 9876543210")
        # Convert to E.164 format for storage
        return f"+91{v}"

    @field_validator("email", mode="before")
    @classmethod
    def validate_email_or_phone(cls, v: str | None, info) -> str | None:
        # Ensure either email or phone is provided
        phone = info.data.get("phone")
        if not v and not phone:
            raise ValueError("Either email or phone must be provided")
        return v


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int  # seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id:           str
    full_name:    str
    email:        str | None
    phone:        str
    role:         str
    is_verified:  bool
    avatar_url:   str | None

    model_config = {"from_attributes": True}


# ── Phone Registration Schemas ────────────────────────────────────────────────

class PhoneRegistrationStartRequest(BaseModel):
    """Request to start phone-based registration (send OTP)."""
    phone: str = Field(..., examples=["9876543210"])

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if v.startswith("+91"):
            v = v[3:]
        elif v.startswith("91"):
            v = v[2:]
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Phone must be a valid 10-digit Indian number")
        return f"+91{v}"


class PhoneRegistrationVerifyRequest(BaseModel):
    """Request to verify phone OTP and create account."""
    phone: str
    otp: str = Field(..., min_length=6, max_length=6)
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    role: str = Field(default="customer", pattern="^(customer|owner)$")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if v.startswith("+91"):
            v = v[3:]
        elif v.startswith("91"):
            v = v[2:]
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Phone must be a valid 10-digit Indian number")
        return f"+91{v}"


class EmailVerificationStartRequest(BaseModel):
    """Request to start email verification (send OTP)."""
    email: EmailStr


class EmailVerificationVerifyRequest(BaseModel):
    """Request to verify email OTP."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


# ── OAuth Schemas ─────────────────────────────────────────────────────────────

class GoogleOAuthCallbackRequest(BaseModel):
    """Request to complete Google OAuth callback."""
    code: str
    redirect_uri: str = Field(..., examples=["http://localhost:8000/auth/oauth/google/callback"])


class OAuthLinkPhoneRequest(BaseModel):
    """Request to link phone number after OAuth signup."""
    phone: str
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if v.startswith("+91"):
            v = v[3:]
        elif v.startswith("91"):
            v = v[2:]
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Phone must be a valid 10-digit Indian number")
        return f"+91{v}"


class OAuthSetPasswordRequest(BaseModel):
    """Request to set password for OAuth user (backup authentication)."""
    password: str = Field(..., min_length=8, examples=["SecurePass123!"])


class OAuthTokenResponse(BaseModel):
    """Response after OAuth signup (temporary auth for phone linking)."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    message: str = "Complete phone verification to finalize account"


class RegistrationCompleteResponse(BaseModel):
    """Response when registration is complete."""
    id: str
    full_name: str
    email: str | None
    phone: str
    role: str
    is_verified: bool
    email_verified: bool
    oauth_provider: str | None

    model_config = {"from_attributes": True}
