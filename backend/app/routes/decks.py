from fastapi import APIRouter, HTTPException, status, Request, Depends, Path
from pydantic import BaseModel, Field
from sqlalchemy import text
from typing import Optional, List

from app.models.user import verify_jwt_token, TokenData

router = APIRouter()


class DeckCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class DeckUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class DeckCardAdd(BaseModel):
    card_id: str
    quantity: int = Field(1, ge=1)


class DeckCardUpdate(BaseModel):
    quantity: int = Field(..., ge=1)


class DeckCardResponse(BaseModel):
    id: str
    card_id: str
    quantity: int
    card_name: Optional[str] = None


class DeckResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DeckWithCardsResponse(DeckResponse):
    cards: List[DeckCardResponse] = []


@router.get("/decks", response_model=List[DeckResponse])
async def list_decks(request: Request, token_data: TokenData = Depends(verify_jwt_token)):
    """List all decks for the current user."""
    async with request.app.state.async_session() as session:
        result = await session.execute(
            text("""
                SELECT id, name, description, created_at, updated_at
                FROM decks
                WHERE user_id = :user_id::uuid
                ORDER BY updated_at DESC
            """),
            {"user_id": token_data.user_id},
        )
        rows = result.fetchall()
        return [
            DeckResponse(
                id=str(row[0]),
                name=row[1],
                description=row[2],
                created_at=row[3].isoformat() if row[3] else None,
                updated_at=row[4].isoformat() if row[4] else None,
            )
            for row in rows
        ]


@router.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(
    request: Request,
    deck_data: DeckCreate,
    token_data: TokenData = Depends(verify_jwt_token),
):
    """Create a new deck."""
    async with request.app.state.async_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO decks (user_id, name, description)
                VALUES (:user_id::uuid, :name, :description)
                RETURNING id, name, description, created_at, updated_at
            """),
            {
                "user_id": token_data.user_id,
                "name": deck_data.name,
                "description": deck_data.description,
            },
        )
        await session.commit()
        row = result.fetchone()
        return DeckResponse(
            id=str(row[0]),
            name=row[1],
            description=row[2],
            created_at=row[3].isoformat() if row[3] else None,
            updated_at=row[4].isoformat() if row[4] else None,
        )


@router.get("/decks/{deck_id}", response_model=DeckWithCardsResponse)
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
                SELECT id, name, description, created_at, updated_at
                FROM decks
                WHERE id = :deck_id::uuid AND user_id = :user_id::uuid
            """),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        deck_row = result.fetchone()
        if not deck_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )

        # Get cards in deck with card names
        result = await session.execute(
            text("""
                SELECT dc.id, dc.card_id, dc.quantity, c.name as card_name
                FROM deck_cards dc
                LEFT JOIN cards c ON dc.card_id = c.id
                WHERE dc.deck_id = :deck_id::uuid
                ORDER BY c.name
            """),
            {"deck_id": deck_id},
        )
        card_rows = result.fetchall()

        return DeckWithCardsResponse(
            id=str(deck_row[0]),
            name=deck_row[1],
            description=deck_row[2],
            created_at=deck_row[3].isoformat() if deck_row[3] else None,
            updated_at=deck_row[4].isoformat() if deck_row[4] else None,
            cards=[
                DeckCardResponse(
                    id=str(row[0]),
                    card_id=row[1],
                    quantity=row[2],
                    card_name=row[3],
                )
                for row in card_rows
            ],
        )


@router.put("/decks/{deck_id}", response_model=DeckResponse)
async def update_deck(
    request: Request,
    deck_data: DeckUpdate,
    deck_id: str = Path(...),
    token_data: TokenData = Depends(verify_jwt_token),
):
    """Update a deck's name and/or description."""
    async with request.app.state.async_session() as session:
        # Check ownership
        result = await session.execute(
            text("SELECT id FROM decks WHERE id = :deck_id::uuid AND user_id = :user_id::uuid"),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )

        # Build update query dynamically
        updates = []
        params = {"deck_id": deck_id}
        if deck_data.name is not None:
            updates.append("name = :name")
            params["name"] = deck_data.name
        if deck_data.description is not None:
            updates.append("description = :description")
            params["description"] = deck_data.description

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        updates.append("updated_at = NOW()")
        update_clause = ", ".join(updates)

        result = await session.execute(
            text(f"""
                UPDATE decks
                SET {update_clause}
                WHERE id = :deck_id::uuid
                RETURNING id, name, description, created_at, updated_at
            """),
            params,
        )
        await session.commit()
        row = result.fetchone()
        return DeckResponse(
            id=str(row[0]),
            name=row[1],
            description=row[2],
            created_at=row[3].isoformat() if row[3] else None,
            updated_at=row[4].isoformat() if row[4] else None,
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
            text("DELETE FROM decks WHERE id = :deck_id::uuid AND user_id = :user_id::uuid RETURNING id"),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        await session.commit()
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )


@router.post("/decks/{deck_id}/cards", response_model=DeckCardResponse, status_code=status.HTTP_201_CREATED)
async def add_card_to_deck(
    request: Request,
    card_data: DeckCardAdd,
    deck_id: str = Path(...),
    token_data: TokenData = Depends(verify_jwt_token),
):
    """Add a card to a deck."""
    async with request.app.state.async_session() as session:
        # Check deck ownership
        result = await session.execute(
            text("SELECT id FROM decks WHERE id = :deck_id::uuid AND user_id = :user_id::uuid"),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )

        # Upsert card (add or update quantity)
        result = await session.execute(
            text("""
                INSERT INTO deck_cards (deck_id, card_id, quantity)
                VALUES (:deck_id::uuid, :card_id, :quantity)
                ON CONFLICT (deck_id, card_id)
                DO UPDATE SET quantity = deck_cards.quantity + :quantity
                RETURNING id, card_id, quantity
            """),
            {
                "deck_id": deck_id,
                "card_id": card_data.card_id,
                "quantity": card_data.quantity,
            },
        )
        await session.commit()

        # Update deck's updated_at
        await session.execute(
            text("UPDATE decks SET updated_at = NOW() WHERE id = :deck_id::uuid"),
            {"deck_id": deck_id},
        )
        await session.commit()

        row = result.fetchone()

        # Get card name
        name_result = await session.execute(
            text("SELECT name FROM cards WHERE id = :card_id"),
            {"card_id": card_data.card_id},
        )
        name_row = name_result.fetchone()

        return DeckCardResponse(
            id=str(row[0]),
            card_id=row[1],
            quantity=row[2],
            card_name=name_row[0] if name_row else None,
        )


@router.put("/decks/{deck_id}/cards/{card_id}", response_model=DeckCardResponse)
async def update_card_quantity(
    request: Request,
    card_data: DeckCardUpdate,
    deck_id: str = Path(...),
    card_id: str = Path(...),
    token_data: TokenData = Depends(verify_jwt_token),
):
    """Update a card's quantity in a deck."""
    async with request.app.state.async_session() as session:
        # Check deck ownership
        result = await session.execute(
            text("SELECT id FROM decks WHERE id = :deck_id::uuid AND user_id = :user_id::uuid"),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )

        result = await session.execute(
            text("""
                UPDATE deck_cards
                SET quantity = :quantity
                WHERE deck_id = :deck_id::uuid AND card_id = :card_id
                RETURNING id, card_id, quantity
            """),
            {"deck_id": deck_id, "card_id": card_id, "quantity": card_data.quantity},
        )
        await session.commit()
        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Card not in deck"
            )

        # Update deck's updated_at
        await session.execute(
            text("UPDATE decks SET updated_at = NOW() WHERE id = :deck_id::uuid"),
            {"deck_id": deck_id},
        )
        await session.commit()

        # Get card name
        name_result = await session.execute(
            text("SELECT name FROM cards WHERE id = :card_id"),
            {"card_id": card_id},
        )
        name_row = name_result.fetchone()

        return DeckCardResponse(
            id=str(row[0]),
            card_id=row[1],
            quantity=row[2],
            card_name=name_row[0] if name_row else None,
        )


@router.delete("/decks/{deck_id}/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_card_from_deck(
    request: Request,
    deck_id: str = Path(...),
    card_id: str = Path(...),
    token_data: TokenData = Depends(verify_jwt_token),
):
    """Remove a card from a deck."""
    async with request.app.state.async_session() as session:
        # Check deck ownership
        result = await session.execute(
            text("SELECT id FROM decks WHERE id = :deck_id::uuid AND user_id = :user_id::uuid"),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )

        result = await session.execute(
            text("DELETE FROM deck_cards WHERE deck_id = :deck_id::uuid AND card_id = :card_id RETURNING id"),
            {"deck_id": deck_id, "card_id": card_id},
        )
        await session.commit()
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Card not in deck"
            )

        # Update deck's updated_at
        await session.execute(
            text("UPDATE decks SET updated_at = NOW() WHERE id = :deck_id::uuid"),
            {"deck_id": deck_id},
        )
        await session.commit()
