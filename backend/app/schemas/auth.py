"""
app/schemas/auth.py
───────────────────
Request / Response schemas for auth endpoints.
Pydantic v2 with strict validation.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class PhoneSendOTPRequest(BaseModel):
    phone: str = Field(..., examples=["+919876543210"])

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # E.164 format: +[country][number], 7-15 digits
        pattern = r"^\+[1-9]\d{6,14}$"
        if not re.match(pattern, v):
            raise ValueError("Phone must be in E.164 format, e.g. +919876543210")
        return v


class PhoneVerifyOTPRequest(BaseModel):
    phone: str
    otp:   str = Field(..., min_length=6, max_length=6)
    purpose: str = Field(default="login", pattern="^(login|verify)$")


class RegisterRequest(BaseModel):
    full_name: str   = Field(..., min_length=2, max_length=120)
    phone:     str
    email:     EmailStr | None = None
    password:  str | None      = Field(default=None, min_length=8)
    role:      str             = Field(default="customer", pattern="^(customer|owner)$")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^\+[1-9]\d{6,14}$", v):
            raise ValueError("Invalid phone format")
        return v


class LoginRequest(BaseModel):
    phone:    str
    password: str


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
