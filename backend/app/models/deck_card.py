"""
DeckCard Database Model

Represents the 'deck_cards' junction table:
- id: UUID PRIMARY KEY
- deck_id: UUID NOT NULL REFERENCES decks(id) ON DELETE CASCADE
- card_id: VARCHAR(255) NOT NULL
- quantity: INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0)
- zone: VARCHAR(20) DEFAULT 'mainboard'
- tags: TEXT[] DEFAULT '{}'
- is_commander: BOOLEAN DEFAULT FALSE
- card_data: JSONB
- UNIQUE(deck_id, card_id, zone)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class DeckCard:
    """Database model for the deck_cards junction table."""
    id: str
    deck_id: str
    card_id: str
    quantity: int = 1
    zone: str = "mainboard"
    tags: List[str] = field(default_factory=list)
    is_commander: bool = False
    card_data: Optional[Dict[str, Any]] = None
