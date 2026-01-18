
from fastapi import APIRouter, Query, Request
from typing import Any
from sqlalchemy import text
from fastapi import HTTPException

router = APIRouter()

@router.get("/name")
async def name_check(
    request: Request,
    name: str = Query(..., description="Name to look for in the cards database")
) -> dict[str, Any]:
    """Looks for a name in the cards database."""
    try:
        # Handle special case for double-faced cards (e.g., 'Riverglide Pathway // Lavaglide Pathway')
        names_to_check = [name]
        if ' // ' in name:
            part1, part2 = name.split(' // ', 1)
            names_to_check.extend([part1.strip(), part2.strip()])
        # Convert all names to lowercase for case-insensitive search
        names_to_check = [n.lower() for n in names_to_check]
        async with request.app.state.async_session() as session:
            result = await session.execute(
                text("SELECT name, mana_cost, type_line, oracle_text, power, toughness FROM cards WHERE LOWER(name) = ANY(:names)"), {"names": names_to_check}
            )
            row = result.first()
            if row:
                # Convert SQLAlchemy Row to dict
                card = dict(row._mapping)
                return {"status": "found", **card}
            else:
                raise HTTPException(status_code=404, detail={"status": "not found", "name": name})
    except HTTPException:
        # Let FastAPI handle HTTPException (404)
        raise
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
