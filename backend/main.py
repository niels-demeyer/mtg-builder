"""
MTG Builder API

FastAPI application entry point.
Uses MVC architecture:
- Models: Database models (app/models/)
- Views: Pydantic schemas for API request/response (app/views/)
- Controllers: Business logic (app/controllers/)
- Routers: Route definitions (app/routers/)
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Import routers
from app.routers import auth_router, deck_router, card_router, health_router, game_router
from app.controllers.game import GameRoomManager

load_dotenv()

# Get raw DSN from env
_raw_db_url = os.getenv("DATABASE_URL", "")

# For asyncpg, must be 'postgresql://' or 'postgres://'
if _raw_db_url.startswith("postgresql+asyncpg://"):
    asyncpg_dsn = _raw_db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
elif _raw_db_url.startswith("postgres://"):
    asyncpg_dsn = _raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    asyncpg_dsn = _raw_db_url

# For SQLAlchemy, must be 'postgresql+asyncpg://'
if _raw_db_url.startswith("postgres://"):
    sqlalchemy_dsn = _raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _raw_db_url.startswith("postgresql://"):
    sqlalchemy_dsn = _raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    sqlalchemy_dsn = _raw_db_url


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for database setup/teardown."""
    # Startup: create database connection pool
    pool = await asyncpg.create_pool(asyncpg_dsn)  # type: ignore[attr-defined]
    app.state.pool = pool

    # Setup SQLAlchemy async sessionmaker
    engine = create_async_engine(sqlalchemy_dsn, echo=False)
    app.state.async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Initialize game room manager
    app.state.game_manager = GameRoomManager()

    yield

    # Shutdown: close the connection pool and SQLAlchemy engine
    await pool.close()  # type: ignore[attr-defined]
    await engine.dispose()


app = FastAPI(
    title="MTG Builder API",
    description="API for building and managing Magic: The Gathering decks",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:1420",
        "http://127.0.0.1:1420",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(deck_router, prefix="/api/v1", tags=["Decks"])
app.include_router(card_router, prefix="/api/v1", tags=["Cards"])
app.include_router(game_router, prefix="/api/v1", tags=["Game"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
