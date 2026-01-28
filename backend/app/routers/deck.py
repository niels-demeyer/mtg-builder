"""
Deck Router

API routes for deck management.
"""

from typing import List

from fastapi import APIRouter, Request, Depends, Path, status

from app.controllers.auth import AuthController
from app.controllers.deck import DeckController
from app.views.user import TokenData
from app.views.deck import DeckCreate, DeckUpdate, DeckResponse

router = APIRouter()


@router.get("/decks", response_model=List[DeckResponse])
async def list_decks(
    request: Request, token_data: TokenData = Depends(AuthController.verify_jwt_token)
):
    """List all decks for the current user with their cards."""
    async with request.app.state.async_session() as session:
        return await DeckController.list_decks(session, token_data)


@router.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(
    request: Request,
    deck_data: DeckCreate,
    token_data: TokenData = Depends(AuthController.verify_jwt_token),
):
    """Create a new deck with optional cards."""
    async with request.app.state.async_session() as session:
        return await DeckController.create_deck(session, deck_data, token_data)


@router.get("/decks/{deck_id}", response_model=DeckResponse)
async def get_deck(
    request: Request,
    deck_id: str = Path(...),
    token_data: TokenData = Depends(AuthController.verify_jwt_token),
):
    """Get a specific deck with its cards."""
    async with request.app.state.async_session() as session:
        return await DeckController.get_deck(session, deck_id, token_data)


@router.put("/decks/{deck_id}", response_model=DeckResponse)
async def update_deck(
    request: Request,
    deck_data: DeckUpdate,
    deck_id: str = Path(...),
    token_data: TokenData = Depends(AuthController.verify_jwt_token),
):
    """Update a deck's name, format, description, and/or cards."""
    async with request.app.state.async_session() as session:
        return await DeckController.update_deck(session, deck_id, deck_data, token_data)


@router.delete("/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(
    request: Request,
    deck_id: str = Path(...),
    token_data: TokenData = Depends(AuthController.verify_jwt_token),
):
    """Delete a deck."""
    async with request.app.state.async_session() as session:
        await DeckController.delete_deck(session, deck_id, token_data)
