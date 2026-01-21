import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import and include routers
from app.routes.health import router as health_router
from app.routes.name import router as name_router
from app.routes.search import router as search_router
from app.routes.auth import router as auth_router
from app.routes.decks import router as decks_router

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
    # Startup: create database connection pool
    pool = await asyncpg.create_pool(asyncpg_dsn)  # type: ignore[attr-defined]
    app.state.pool = pool

    # Setup SQLAlchemy async sessionmaker
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    engine = create_async_engine(sqlalchemy_dsn, echo=False)
    app.state.async_session = async_sessionmaker(engine, expire_on_commit=False)

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:1420", "http://127.0.0.1:1420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router,
                   prefix="/api/v1",
                   tags=["Health"])


app.include_router(name_router,
                   prefix="/api/v1",
                   tags=["Name"])

app.include_router(search_router,
                   prefix="/api/v1",
                   tags=["Search"])

app.include_router(auth_router,
                   prefix="/api/v1",
                   tags=["Auth"])

app.include_router(decks_router,
                   prefix="/api/v1",
                   tags=["Decks"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
