from fastapi import APIRouter, HTTPException, status, Request, Depends, Path
from pydantic import BaseModel, Field
from sqlalchemy import text
from typing import Optional, List, Any
import json

from app.models.user import verify_jwt_token, TokenData

router = APIRouter()


class CardInDeck(BaseModel):
    id: str
    name: str
    mana_cost: Optional[str] = None
    cmc: float = 0
    type_line: str = ""
    colors: Optional[List[str]] = None
    rarity: str = "common"
    image_uri: Optional[str] = None
    quantity: int = 1
    zone: str = "mainboard"
    tags: List[str] = []
    isCommander: Optional[bool] = False


class DeckCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    format: str = "Standard"
    description: Optional[str] = None
    cards: List[CardInDeck] = []


class DeckUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    format: Optional[str] = None
    description: Optional[str] = None
    cards: Optional[List[CardInDeck]] = None


class DeckResponse(BaseModel):
    id: str
    name: str
    format: str = "Standard"
    description: Optional[str] = None
    cards: List[CardInDeck] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


@router.get("/decks", response_model=List[DeckResponse])
async def list_decks(request: Request, token_data: TokenData = Depends(verify_jwt_token)):
    """List all decks for the current user with their cards."""
    async with request.app.state.async_session() as session:
        # Get all decks
        result = await session.execute(
            text("""
                SELECT id, name, format, description, created_at, updated_at
                FROM decks
                WHERE user_id = CAST(:user_id AS uuid)
                ORDER BY updated_at DESC
            """),
            {"user_id": token_data.user_id},
        )
        deck_rows = result.fetchall()

        decks = []
        for deck_row in deck_rows:
            deck_id = str(deck_row[0])

            # Get cards for this deck
            cards_result = await session.execute(
                text("""
                    SELECT card_id, quantity, zone, tags, is_commander, card_data
                    FROM deck_cards
                    WHERE deck_id = CAST(:deck_id AS uuid)
                """),
                {"deck_id": deck_id},
            )
            card_rows = cards_result.fetchall()

            cards = []
            for card_row in card_rows:
                card_data = card_row[5] if card_row[5] else {}
                if isinstance(card_data, str):
                    card_data = json.loads(card_data)

                cards.append(CardInDeck(
                    id=card_row[0],
                    name=card_data.get("name", "Unknown"),
                    mana_cost=card_data.get("mana_cost"),
                    cmc=card_data.get("cmc", 0),
                    type_line=card_data.get("type_line", ""),
                    colors=card_data.get("colors"),
                    rarity=card_data.get("rarity", "common"),
                    image_uri=card_data.get("image_uri"),
                    quantity=card_row[1],
                    zone=card_row[2] or "mainboard",
                    tags=card_row[3] or [],
                    isCommander=card_row[4] or False,
                ))

            decks.append(DeckResponse(
                id=deck_id,
                name=deck_row[1],
                format=deck_row[2] or "Standard",
                description=deck_row[3],
                cards=cards,
                createdAt=deck_row[4].isoformat() if deck_row[4] else None,
                updatedAt=deck_row[5].isoformat() if deck_row[5] else None,
            ))

        return decks


@router.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(
    request: Request,
    deck_data: DeckCreate,
    token_data: TokenData = Depends(verify_jwt_token),
):
    """Create a new deck with optional cards."""
    async with request.app.state.async_session() as session:
        # Create the deck
        result = await session.execute(
            text("""
                INSERT INTO decks (user_id, name, format, description)
                VALUES (CAST(:user_id AS uuid), :name, :format, :description)
                RETURNING id, name, format, description, created_at, updated_at
            """),
            {
                "user_id": token_data.user_id,
                "name": deck_data.name,
                "format": deck_data.format,
                "description": deck_data.description,
            },
        )
        await session.commit()
        row = result.fetchone()
        deck_id = str(row[0])

        # Add cards if provided
        cards = []
        for card in deck_data.cards:
            card_data_json = json.dumps({
                "name": card.name,
                "mana_cost": card.mana_cost,
                "cmc": card.cmc,
                "type_line": card.type_line,
                "colors": card.colors,
                "rarity": card.rarity,
                "image_uri": card.image_uri,
            })

            await session.execute(
                text("""
                    INSERT INTO deck_cards (deck_id, card_id, quantity, zone, tags, is_commander, card_data)
                    VALUES (CAST(:deck_id AS uuid), :card_id, :quantity, :zone, :tags, :is_commander, :card_data::jsonb)
                    ON CONFLICT (deck_id, card_id, zone) DO UPDATE SET
                        quantity = :quantity,
                        tags = :tags,
                        is_commander = :is_commander,
                        card_data = :card_data::jsonb
                """),
                {
                    "deck_id": deck_id,
                    "card_id": card.id,
                    "quantity": card.quantity,
                    "zone": card.zone,
                    "tags": card.tags,
                    "is_commander": card.isCommander,
                    "card_data": card_data_json,
                },
            )
            cards.append(card)

        await session.commit()

        return DeckResponse(
            id=deck_id,
            name=row[1],
            format=row[2] or "Standard",
            description=row[3],
            cards=cards,
            createdAt=row[4].isoformat() if row[4] else None,
            updatedAt=row[5].isoformat() if row[5] else None,
        )


@router.get("/decks/{deck_id}", response_model=DeckResponse)
async def get_deck(
    request: Request,
    deck_id: str = Path(...),
    token_data: TokenData = Depends(verify_jwt_token),
):
    """Get a specific deck with its cards."""
    async with request.app.state.async_session() as session:
        # Get deck info
        result = await session.execute(
            text("""
                SELECT id, name, format, description, created_at, updated_at
                FROM decks
                WHERE id = CAST(:deck_id AS uuid) AND user_id = CAST(:user_id AS uuid)
            """),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        deck_row = result.fetchone()
        if not deck_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )

        # Get cards in deck
        result = await session.execute(
            text("""
                SELECT card_id, quantity, zone, tags, is_commander, card_data
                FROM deck_cards
                WHERE deck_id = CAST(:deck_id AS uuid)
            """),
            {"deck_id": deck_id},
        )
        card_rows = result.fetchall()

        cards = []
        for card_row in card_rows:
            card_data = card_row[5] if card_row[5] else {}
            if isinstance(card_data, str):
                card_data = json.loads(card_data)

            cards.append(CardInDeck(
                id=card_row[0],
                name=card_data.get("name", "Unknown"),
                mana_cost=card_data.get("mana_cost"),
                cmc=card_data.get("cmc", 0),
                type_line=card_data.get("type_line", ""),
                colors=card_data.get("colors"),
                rarity=card_data.get("rarity", "common"),
                image_uri=card_data.get("image_uri"),
                quantity=card_row[1],
                zone=card_row[2] or "mainboard",
                tags=card_row[3] or [],
                isCommander=card_row[4] or False,
            ))

        return DeckResponse(
            id=str(deck_row[0]),
            name=deck_row[1],
            format=deck_row[2] or "Standard",
            description=deck_row[3],
            cards=cards,
            createdAt=deck_row[4].isoformat() if deck_row[4] else None,
            updatedAt=deck_row[5].isoformat() if deck_row[5] else None,
        )


@router.put("/decks/{deck_id}", response_model=DeckResponse)
async def update_deck(
    request: Request,
    deck_data: DeckUpdate,
    deck_id: str = Path(...),
    token_data: TokenData = Depends(verify_jwt_token),
):
    """Update a deck's name, format, description, and/or cards."""
    async with request.app.state.async_session() as session:
        # Check ownership
        result = await session.execute(
            text("SELECT id FROM decks WHERE id = CAST(:deck_id AS uuid) AND user_id = CAST(:user_id AS uuid)"),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )

        # Build update query dynamically
        updates = []
        params: dict[str, Any] = {"deck_id": deck_id}
        if deck_data.name is not None:
            updates.append("name = :name")
            params["name"] = deck_data.name
        if deck_data.format is not None:
            updates.append("format = :format")
            params["format"] = deck_data.format
        if deck_data.description is not None:
            updates.append("description = :description")
            params["description"] = deck_data.description

        updates.append("updated_at = NOW()")
        update_clause = ", ".join(updates)

        result = await session.execute(
            text(f"""
                UPDATE decks
                SET {update_clause}
                WHERE id = CAST(:deck_id AS uuid)
                RETURNING id, name, format, description, created_at, updated_at
            """),
            params,
        )
        await session.commit()
        row = result.fetchone()

        # Update cards if provided
        cards = []
        if deck_data.cards is not None:
            # Delete existing cards
            await session.execute(
                text("DELETE FROM deck_cards WHERE deck_id = CAST(:deck_id AS uuid)"),
                {"deck_id": deck_id},
            )

            # Insert new cards
            for card in deck_data.cards:
                card_data_json = json.dumps({
                    "name": card.name,
                    "mana_cost": card.mana_cost,
                    "cmc": card.cmc,
                    "type_line": card.type_line,
                    "colors": card.colors,
                    "rarity": card.rarity,
                    "image_uri": card.image_uri,
                })

                await session.execute(
                    text("""
                        INSERT INTO deck_cards (deck_id, card_id, quantity, zone, tags, is_commander, card_data)
                        VALUES (CAST(:deck_id AS uuid), :card_id, :quantity, :zone, :tags, :is_commander, :card_data::jsonb)
                    """),
                    {
                        "deck_id": deck_id,
                        "card_id": card.id,
                        "quantity": card.quantity,
                        "zone": card.zone,
                        "tags": card.tags,
                        "is_commander": card.isCommander,
                        "card_data": card_data_json,
                    },
                )
                cards.append(card)

            await session.commit()
        else:
            # Fetch existing cards
            result = await session.execute(
                text("""
                    SELECT card_id, quantity, zone, tags, is_commander, card_data
                    FROM deck_cards
                    WHERE deck_id = CAST(:deck_id AS uuid)
                """),
                {"deck_id": deck_id},
            )
            card_rows = result.fetchall()

            for card_row in card_rows:
                card_data = card_row[5] if card_row[5] else {}
                if isinstance(card_data, str):
                    card_data = json.loads(card_data)

                cards.append(CardInDeck(
                    id=card_row[0],
                    name=card_data.get("name", "Unknown"),
                    mana_cost=card_data.get("mana_cost"),
                    cmc=card_data.get("cmc", 0),
                    type_line=card_data.get("type_line", ""),
                    colors=card_data.get("colors"),
                    rarity=card_data.get("rarity", "common"),
                    image_uri=card_data.get("image_uri"),
                    quantity=card_row[1],
                    zone=card_row[2] or "mainboard",
                    tags=card_row[3] or [],
                    isCommander=card_row[4] or False,
                ))

        return DeckResponse(
            id=str(row[0]),
            name=row[1],
            format=row[2] or "Standard",
            description=row[3],
            cards=cards,
            createdAt=row[4].isoformat() if row[4] else None,
            updatedAt=row[5].isoformat() if row[5] else None,
        )


@router.delete("/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(
    request: Request,
    deck_id: str = Path(...),
    token_data: TokenData = Depends(verify_jwt_token),
):
    """Delete a deck."""
    async with request.app.state.async_session() as session:
        result = await session.execute(
            text("DELETE FROM decks WHERE id = CAST(:deck_id AS uuid) AND user_id = CAST(:user_id AS uuid) RETURNING id"),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        await session.commit()
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )
