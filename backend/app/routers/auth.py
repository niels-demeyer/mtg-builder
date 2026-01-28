"""
Auth Router

API routes for user authentication.
"""

from fastapi import APIRouter, Request, Depends, status

from app.controllers.auth import AuthController
from app.views.user import UserRegister, UserLogin, UserResponse, Token, TokenData

router = APIRouter()


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_data: UserRegister):
    """Register a new user."""
    async with request.app.state.async_session() as session:
        return await AuthController.register(session, user_data)


@router.post("/auth/login", response_model=Token)
async def login(request: Request, user_data: UserLogin):
    """Login and get an access token."""
    async with request.app.state.async_session() as session:
        return await AuthController.login(session, user_data)


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user(
    request: Request, token_data: TokenData = Depends(AuthController.verify_jwt_token)
):
    """Get current authenticated user info."""
    async with request.app.state.async_session() as session:
        return await AuthController.get_current_user(session, token_data)
