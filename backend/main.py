import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
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
    # Startup: create SQLAlchemy async engine and sessionmaker
    engine = create_async_engine(DATABASE_URL, echo=True, future=True)
    app.state.engine = engine
    app.state.async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield
    # Shutdown: dispose the engine
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

    uvicorn.run(app, host="0.0.0.0", port=8000)
