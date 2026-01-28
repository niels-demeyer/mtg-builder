"""
Auth Controller

Business logic for user authentication operations.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.views.user import UserRegister, UserLogin, UserResponse, Token, TokenData


# JWT Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthController:
    """Controller for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_jwt_token(token: str = Depends(oauth2_scheme)) -> TokenData:
        """Verify JWT token and return token data."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            user_id = payload.get("user_id")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid JWT token: missing subject",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return TokenData(username=username, user_id=user_id)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def register(session: AsyncSession, user_data: UserRegister) -> UserResponse:
        """Register a new user."""
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
        password_hash = AuthController.hash_password(user_data.password)
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

    @staticmethod
    async def login(session: AsyncSession, user_data: UserLogin) -> Token:
        """Authenticate user and return access token."""
        result = await session.execute(
            text("SELECT id, username, password_hash FROM users WHERE username = :username"),
            {"username": user_data.username},
        )
        row = result.fetchone()

        if not row or not AuthController.verify_password(user_data.password, row[2]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = AuthController.create_access_token(
            data={"sub": row[1], "user_id": str(row[0])},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return Token(access_token=access_token)

    @staticmethod
    async def get_current_user(session: AsyncSession, token_data: TokenData) -> UserResponse:
        """Get current authenticated user info."""
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
