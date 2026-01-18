
from fastapi import APIRouter, Query, Request
from typing import Any
from sqlalchemy import text

router = APIRouter()

@router.get("/name")
async def name_check(
    request: Request,
    name: str = Query(..., description="Name to look for in the cards database")
) -> dict[str, Any]:
    """Looks for a name in the cards database."""
    try:
        async with request.app.state.async_session() as session:
            result = await session.execute(
                text("SELECT name FROM cards WHERE name = :name"), {"name": name}
            )
            value = result.scalar()
            if value:
                return {"status": "found", "name": value}
            else:
                return {"status": "not found", "name": name}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
