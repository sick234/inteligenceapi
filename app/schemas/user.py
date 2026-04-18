"""
Pydantic schemas for User request/response validation.

These schemas enforce data integrity at the API boundary layer,
ensuring only valid data reaches the database.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base schema with shared user fields."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration requests."""
    password: str = Field(..., min_length=8, max_length=64, description="Must be 8-64 characters")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(UserBase):
    """Schema for user data in API responses (never includes password)."""
    id: int
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response after successful authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration time in minutes")


class TokenData(BaseModel):
    """Internal schema for decoded JWT payload."""
    email: Optional[str] = None
