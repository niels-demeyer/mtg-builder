import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI

# Import and include routers
from routes.health import router as health_router

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




app.include_router(health_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
