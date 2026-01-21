import json
import httpx
from fastapi import APIRouter, Query, Request, Path
from typing import Any
from dataclasses import asdict
from sqlalchemy import text

from app.routes.dbmodels import DbCard

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
                # Parse JSON string fields
                for field in ('image_uris', 'legalities', 'colors', 'color_identity', 'keywords'):
                    if field in data and isinstance(data[field], str) and data[field]:
                        try:
                            data[field] = json.loads(data[field])
                        except json.JSONDecodeError:
                            pass
                card = DbCard(**data)
                cards.append(asdict(card))
            return {"data": cards, "total_cards": len(cards)}
    except Exception as e:
        return {"data": [], "total_cards": 0, "error": str(e)}


@router.get("/cards/{card_id}/printings")
async def get_card_printings(
    request: Request,
    card_id: str = Path(..., description="The card ID to get printings for")
) -> dict[str, Any]:
    """Get all printings of a card from Scryfall."""
    try:
        async with request.app.state.async_session() as session:
            result = await session.execute(
                text("SELECT prints_search_uri FROM cards WHERE id = :card_id"),
                {"card_id": card_id}
            )
            row = result.fetchone()
            if not row or not row[0]:
                return {"data": [], "error": "Card not found or no prints_search_uri"}

            prints_uri = row[0]

        async with httpx.AsyncClient() as client:
            response = await client.get(prints_uri, timeout=10.0)
            response.raise_for_status()
            scryfall_data = response.json()

            printings = []
            for card in scryfall_data.get("data", []):
                printings.append({
                    "id": card.get("id"),
                    "name": card.get("name"),
                    "set_name": card.get("set_name"),
                    "set_code": card.get("set"),
                    "collector_number": card.get("collector_number"),
                    "rarity": card.get("rarity"),
                    "image_uris": card.get("image_uris"),
                    "released_at": card.get("released_at"),
                })

            return {"data": printings, "total_printings": len(printings)}
    except httpx.HTTPError as e:
        return {"data": [], "error": f"Failed to fetch from Scryfall: {str(e)}"}
    except Exception as e:
        return {"data": [], "error": str(e)}
