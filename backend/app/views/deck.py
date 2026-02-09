"""
Deck Views (Pydantic Schemas)

Request and response schemas for deck management endpoints.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List


class CardInDeck(BaseModel):
    """Schema for a card within a deck."""
    id: str
    name: str
    mana_cost: Optional[str] = None
    cmc: float = 0
    type_line: str = ""
    colors: Optional[List[str]] = None
    rarity: str = "common"
    image_uri: Optional[str] = None
    card_faces: Optional[List[Dict[str, Any]]] = None
    quantity: int = 1
    zone: str = "mainboard"
    tags: List[str] = []
    isCommander: Optional[bool] = False


class DeckCreate(BaseModel):
    """Request schema for creating a new deck."""
    name: str = Field(..., min_length=1, max_length=100)
    format: str = "Standard"
    description: Optional[str] = None
    cards: List[CardInDeck] = []


class DeckUpdate(BaseModel):
    """Request schema for updating a deck."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    format: Optional[str] = None
    description: Optional[str] = None
    cards: Optional[List[CardInDeck]] = None


class DeckResponse(BaseModel):
    """Response schema for deck data."""
    id: str
    name: str
    format: str = "Standard"
    description: Optional[str] = None
    cards: List[CardInDeck] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
