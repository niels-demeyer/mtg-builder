from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime, timezone
import uuid

app = FastAPI(title="MTG Builder API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Type alias for deck storage
DeckDict = dict[str, str | list[dict[str, Any]]]

# In-memory storage (replace with database in production)
decks_db: dict[str, DeckDict] = {}


class CardInDeck(BaseModel):
    id: str
    name: str
    quantity: int
    mana_cost: Optional[str] = None
    type_line: Optional[str] = None
    image_uris: Optional[dict[str, Any]] = None
    card_faces: Optional[list[dict[str, Any]]] = None
    colors: Optional[list[str]] = None
    cmc: Optional[float] = None


class DeckCreate(BaseModel):
    name: str
    format: str = "Standard"
    description: Optional[str] = ""


class DeckUpdate(BaseModel):
    name: Optional[str] = None
    format: Optional[str] = None
    description: Optional[str] = None
    cards: Optional[list[CardInDeck]] = None


class Deck(BaseModel):
    id: str
    name: str
    format: str
    description: str
    cards: list[CardInDeck]
    created_at: str
    updated_at: str


def get_utc_now() -> str:
    """Get current UTC time as ISO format string."""
    return datetime.now(timezone.utc).isoformat()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to MTG Builder API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/decks", response_model=list[Deck])
async def get_decks() -> list[DeckDict]:
    """Get all decks"""
    return list(decks_db.values())


@app.post("/api/decks", response_model=Deck)
async def create_deck(deck: DeckCreate) -> DeckDict:
    """Create a new deck"""
    deck_id = str(uuid.uuid4())
    now = get_utc_now()
    
    new_deck: DeckDict = {
        "id": deck_id,
        "name": deck.name,
        "format": deck.format,
        "description": deck.description or "",
        "cards": [],
        "created_at": now,
        "updated_at": now,
    }
    
    decks_db[deck_id] = new_deck
    return new_deck


@app.get("/api/decks/{deck_id}", response_model=Deck)
async def get_deck(deck_id: str) -> DeckDict:
    """Get a specific deck"""
    if deck_id not in decks_db:
        raise HTTPException(status_code=404, detail="Deck not found")
    return decks_db[deck_id]


@app.put("/api/decks/{deck_id}", response_model=Deck)
async def update_deck(deck_id: str, deck_update: DeckUpdate) -> DeckDict:
    """Update a deck"""
    if deck_id not in decks_db:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    deck = decks_db[deck_id]
    
    if deck_update.name is not None:
        deck["name"] = deck_update.name
    if deck_update.format is not None:
        deck["format"] = deck_update.format
    if deck_update.description is not None:
        deck["description"] = deck_update.description
    if deck_update.cards is not None:
        deck["cards"] = [card.model_dump() for card in deck_update.cards]
    
    deck["updated_at"] = get_utc_now()
    
    return deck


@app.delete("/api/decks/{deck_id}")
async def delete_deck(deck_id: str) -> dict[str, str]:
    """Delete a deck"""
    if deck_id not in decks_db:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    del decks_db[deck_id]
    return {"message": "Deck deleted successfully"}


@app.post("/api/decks/{deck_id}/cards", response_model=Deck)
async def add_card_to_deck(deck_id: str, card: CardInDeck) -> DeckDict:
    """Add a card to a deck"""
    if deck_id not in decks_db:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    deck = decks_db[deck_id]
    cards = deck["cards"]
    
    # Check if card already exists
    if isinstance(cards, list):
        existing_card: dict[str, Any] | None = next(
            (c for c in cards if c.get("id") == card.id), 
            None
        )
        
        if existing_card:
            existing_card["quantity"] += card.quantity
        else:
            cards.append(card.model_dump())
    
    deck["updated_at"] = get_utc_now()
    
    return deck


@app.delete("/api/decks/{deck_id}/cards/{card_id}", response_model=Deck)
async def remove_card_from_deck(deck_id: str, card_id: str) -> DeckDict:
    """Remove a card from a deck"""
    if deck_id not in decks_db:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    deck = decks_db[deck_id]
    cards = deck["cards"]
    if isinstance(cards, list):
        deck["cards"] = [c for c in cards if c.get("id") != card_id]
    deck["updated_at"] = get_utc_now()
    
    return deck
