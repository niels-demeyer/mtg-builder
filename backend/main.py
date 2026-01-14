import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: create database connection pool
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)
    yield
    # Shutdown: close the connection pool
    await app.state.pool.close()


app = FastAPI(
    title="MTG Builder API",
    description="API for building and managing Magic: The Gathering decks",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Health check endpoint that verifies database connectivity."""
    try:
        async with app.state.pool.acquire() as connection:
            result = await connection.fetchval("SELECT 1")
            return {"status": "healthy", "database": "connected", "check": result}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
