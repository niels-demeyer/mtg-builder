from fastapi import APIRouter
from typing import Any
from sqlalchemy import text
from fastapi import Request

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check(request: Request) -> dict[str, Any]:
    """Health check endpoint that verifies database connectivity using SQLAlchemy."""
    try:
        async with request.app.state.async_session() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            return {"status": "healthy", "database": "connected", "check": value}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
