"""
User Views (Pydantic Schemas)

Request and response schemas for user authentication endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class UserRegister(BaseModel):
    """Request schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Request schema for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Response schema for user data."""
    id: str
    username: str


class Token(BaseModel):
    """Response schema for JWT token."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Internal schema for decoded JWT token data."""
    username: Optional[str] = None
    user_id: Optional[str] = None
