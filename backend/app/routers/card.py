"""
Card Router

API routes for card search and lookup.
"""

from typing import Any

from fastapi import APIRouter, Query, Request, Path

from app.controllers.card import CardController

router = APIRouter()


@router.get("/search")
async def search_cards(
    request: Request,
    q: str = Query("", description="Search query for card names"),
    text: str = Query("", description="Search in oracle text"),
    colors: str = Query("", description="Color filter (comma-separated: W,U,B,R,G,C)"),
    color_match: str = Query("any", description="Color match mode: any, all, exact"),
    types: str = Query("", description="Card type filter (comma-separated)"),
    rarity: str = Query("", description="Rarity filter (comma-separated: common,uncommon,rare,mythic)"),
    cmc_min: int = Query(None, ge=0, description="Minimum converted mana cost"),
    cmc_max: int = Query(None, ge=0, description="Maximum converted mana cost"),
    keywords: str = Query("", description="Keywords filter (comma-separated)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Results per page"),
) -> dict[str, Any]:
    """Search for cards with advanced MTG filters."""
    async with request.app.state.async_session() as session:
        return await CardController.search_cards(
            session=session,
            q=q,
            text=text,
            colors=colors,
            color_match=color_match,
            types=types,
            rarity=rarity,
            cmc_min=cmc_min,
            cmc_max=cmc_max,
            keywords=keywords,
            page=page,
            page_size=page_size,
        )


@router.get("/cards/{card_id}/printings")
async def get_card_printings(
    request: Request,
    card_id: str = Path(..., description="The card ID to get printings for"),
) -> dict[str, Any]:
    """Get all printings of a card from Scryfall."""
    async with request.app.state.async_session() as session:
        return await CardController.get_card_printings(session, card_id)


@router.get("/name")
async def name_check(
    request: Request,
    name: str = Query(..., description="Name to look for in the cards database"),
) -> dict[str, Any]:
    """Look up a card by exact name."""
    async with request.app.state.async_session() as session:
        return await CardController.lookup_by_name(session, name)
