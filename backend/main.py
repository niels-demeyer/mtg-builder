import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import asyncpg
from sqlalchemy import text
from dotenv import load_dotenv
from fastapi import FastAPI

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



@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Health check endpoint that verifies database connectivity using SQLAlchemy."""
    try:
        async with app.state.async_session() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            return {"status": "healthy", "database": "connected", "check": value}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
