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
    phone:    str
    password: str

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
