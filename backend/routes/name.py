
from fastapi import APIRouter, Query, Request
from typing import Any
from dataclasses import asdict
from sqlalchemy import text
from fastapi import HTTPException
from backend.models.dbmodels import DbCard

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
                text("""
                    SELECT id, name, mana_cost, cmc, power, toughness, type_line, oracle_text, colors, color_identity, rarity, keywords, set_id, set_name, image_uris, legalities
                    FROM cards
                    WHERE LOWER(name) = ANY(:names)
                """), {"names": names_to_check}
            )
            row = result.first()
            if row:
                data = dict(row._mapping)
                card = DbCard(**data)
                return {"status": "found", **asdict(card)}
            else:
                raise HTTPException(status_code=404, detail={"status": "not found", "name": name})
    except HTTPException:
        # Let FastAPI handle HTTPException (404)
        raise
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
