"""
Views (Pydantic Schemas)

These Pydantic models define the API request and response schemas.
They provide validation for incoming data and serialization for outgoing data.
"""

from app.views.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
)
from app.views.deck import (
    CardInDeck,
    DeckCreate,
    DeckUpdate,
    DeckResponse,
)
from app.views.card import (
    CardSearchParams,
    CardSearchResponse,
    CardPrintingResponse,
    PaginationInfo,
)
from app.views.health import HealthResponse

__all__ = [
    # User views
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    # Deck views
    "CardInDeck",
    "DeckCreate",
    "DeckUpdate",
    "DeckResponse",
    # Card views
    "CardSearchParams",
    "CardSearchResponse",
    "CardPrintingResponse",
    "PaginationInfo",
    # Health views
    "HealthResponse",
]
