from fastapi import APIRouter, Query, Request
from typing import Any
from dataclasses import asdict
from sqlalchemy import text

from models.dbmodels import DbCard

router = APIRouter()


@router.get("/search")
async def search_cards(
    request: Request,
    q: str = Query(..., min_length=2, description="Search query for card names"),
    limit: int = Query(50, ge=1, le=175, description="Maximum number of results")
) -> dict[str, Any]:
    """Search for cards by name (case-insensitive partial match)."""
    try:
        search_pattern = f"%{q.lower()}%"
        async with request.app.state.async_session() as session:
            result = await session.execute(
                text("""
                    SELECT id, name, mana_cost, cmc, power, toughness, type_line,
                           oracle_text, colors, color_identity, rarity, keywords,
                           set_id, set_name, image_uris, legalities
                    FROM cards
                    WHERE LOWER(name) LIKE :pattern
                    ORDER BY name
                    LIMIT :limit
                """),
                {"pattern": search_pattern, "limit": limit}
            )
            rows = result.fetchall()
            cards = []
            for row in rows:
                data = dict(row._mapping)
                card = DbCard(**data)
                cards.append(asdict(card))
            return {"data": cards, "total_cards": len(cards)}
    except Exception as e:
        return {"data": [], "total_cards": 0, "error": str(e)}
