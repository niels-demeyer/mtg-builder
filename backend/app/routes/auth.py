from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from datetime import timedelta

from app.models.user import (
    hash_password,
    verify_password,
    create_access_token,
    verify_jwt_token,
    TokenData,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter()


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_data: UserRegister):
    """Register a new user."""
    async with request.app.state.async_session() as session:
        # Check if username already exists
        result = await session.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": user_data.username},
        )
        if result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Hash password and create user
        password_hash = hash_password(user_data.password)
        result = await session.execute(
            text("""
                INSERT INTO users (username, password_hash)
                VALUES (:username, :password_hash)
                RETURNING id, username
            """),
            {"username": user_data.username, "password_hash": password_hash},
        )
        await session.commit()
        row = result.fetchone()
        return UserResponse(id=str(row[0]), username=row[1])


@router.post("/auth/login", response_model=Token)
async def login(request: Request, user_data: UserLogin):
    """Login and get an access token."""
    async with request.app.state.async_session() as session:
        result = await session.execute(
            text("SELECT id, username, password_hash FROM users WHERE username = :username"),
            {"username": user_data.username},
        )
        row = result.fetchone()

        if not row or not verify_password(user_data.password, row[2]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            data={"sub": row[1], "user_id": str(row[0])},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return Token(access_token=access_token)


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user(
    request: Request, token_data: TokenData = Depends(verify_jwt_token)
):
    """Get current authenticated user info."""
    async with request.app.state.async_session() as session:
        result = await session.execute(
            text("SELECT id, username FROM users WHERE id = CAST(:user_id AS uuid)"),
            {"user_id": token_data.user_id},
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return UserResponse(id=str(row[0]), username=row[1])
