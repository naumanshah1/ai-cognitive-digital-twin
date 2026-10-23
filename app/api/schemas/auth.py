"""Authentication request and response schemas."""

import re
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from app.api.schemas.users import UserProfile


class RegisterRequest(BaseModel):
    """User registration payload."""

    email: str = Field(..., description="Valid unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="Account password (min 8 characters)")
    name: Optional[str] = Field(None, max_length=128, description="User full display name")
    display_name: Optional[str] = Field(None, max_length=128, description="Alternative field for display name")
    username: Optional[str] = Field(None, min_length=3, max_length=64, description="Optional chosen username")

    @model_validator(mode="after")
    def validate_and_normalize(self) -> "RegisterRequest":
        clean_email = self.email.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
            raise ValueError("Invalid email address format")
        self.email = clean_email

        # Resolve display name
        resolved_name = (self.name or self.display_name or self.username or clean_email.split("@")[0]).strip()
        if len(resolved_name) < 2:
            raise ValueError("Name or display_name must be at least 2 characters long")
        self.name = resolved_name
        self.display_name = resolved_name
        return self


class LoginRequest(BaseModel):
    """User login payload."""

    email: Optional[str] = Field(None, description="Account email or username")
    email_or_username: Optional[str] = Field(None, description="Alternative field for email or username")
    password: str = Field(..., min_length=1, description="Account password")

    @model_validator(mode="after")
    def validate_identifier(self) -> "LoginRequest":
        raw = self.email or self.email_or_username
        if not raw or not raw.strip():
            raise ValueError("Email or username is required")
        self.email = raw.strip().lower()
        self.email_or_username = self.email
        return self


class AuthResponse(BaseModel):
    """Structured response containing JWT bearer token and user profile."""

    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token: str = Field(..., description="Alias for access_token")
    token_type: str = Field("Bearer", description="Authorization header scheme")
    expires_in_hours: int = Field(24, description="Token validity duration in hours")
    user: UserProfile = Field(..., description="Authenticated user profile and roles")


class ChangePasswordRequest(BaseModel):
    """Payload for authenticated password change."""

    current_password: str = Field(..., min_length=1, description="Current account password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password (min 8 characters)")
