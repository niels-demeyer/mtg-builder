import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import asyncpg
from sqlalchemy import text
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

_db_url = os.getenv("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
DATABASE_URL = _db_url



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: create database connection pool
    pool = await asyncpg.create_pool(DATABASE_URL)  # type: ignore[attr-defined]
    app.state.pool = pool
    yield
    # Shutdown: close the connection pool
    await pool.close()  # type: ignore[attr-defined]

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
