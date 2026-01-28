"""
Deck Controller

Business logic for deck management operations.
"""

import json
from typing import List, Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.views.user import TokenData
from app.views.deck import CardInDeck, DeckCreate, DeckUpdate, DeckResponse


class DeckController:
    """Controller for deck management operations."""

    @staticmethod
    def _parse_card_data(card_row: tuple) -> CardInDeck:
        """Parse a card row from database into CardInDeck view."""
        card_data = card_row[5] if card_row[5] else {}
        if isinstance(card_data, str):
            card_data = json.loads(card_data)

        return CardInDeck(
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
        )

    @staticmethod
    def _card_to_json(card: CardInDeck) -> str:
        """Convert CardInDeck to JSON for storage."""
        return json.dumps({
            "name": card.name,
            "mana_cost": card.mana_cost,
            "cmc": card.cmc,
            "type_line": card.type_line,
            "colors": card.colors,
            "rarity": card.rarity,
            "image_uri": card.image_uri,
        })

    @staticmethod
    async def list_decks(session: AsyncSession, token_data: TokenData) -> List[DeckResponse]:
        """List all decks for the current user with their cards."""
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

            cards = [DeckController._parse_card_data(card_row) for card_row in card_rows]

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

    @staticmethod
    async def create_deck(
        session: AsyncSession, deck_data: DeckCreate, token_data: TokenData
    ) -> DeckResponse:
        """Create a new deck with optional cards."""
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
        row = result.fetchone()
        deck_id = str(row[0])

        # Add cards if provided
        cards = []
        for card in deck_data.cards:
            card_data_json = DeckController._card_to_json(card)

            await session.execute(
                text("""
                    INSERT INTO deck_cards (deck_id, card_id, quantity, zone, tags, is_commander, card_data)
                    VALUES (CAST(:deck_id AS uuid), :card_id, :quantity, :zone, :tags, :is_commander, CAST(:card_data AS jsonb))
                    ON CONFLICT (deck_id, card_id, zone) DO UPDATE SET
                        quantity = :quantity,
                        tags = :tags,
                        is_commander = :is_commander,
                        card_data = CAST(:card_data AS jsonb)
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

    @staticmethod
    async def get_deck(
        session: AsyncSession, deck_id: str, token_data: TokenData
    ) -> DeckResponse:
        """Get a specific deck with its cards."""
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

        cards = [DeckController._parse_card_data(card_row) for card_row in card_rows]

        return DeckResponse(
            id=str(deck_row[0]),
            name=deck_row[1],
            format=deck_row[2] or "Standard",
            description=deck_row[3],
            cards=cards,
            createdAt=deck_row[4].isoformat() if deck_row[4] else None,
            updatedAt=deck_row[5].isoformat() if deck_row[5] else None,
        )

    @staticmethod
    async def update_deck(
        session: AsyncSession, deck_id: str, deck_data: DeckUpdate, token_data: TokenData
    ) -> DeckResponse:
        """Update a deck's name, format, description, and/or cards."""
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
                card_data_json = DeckController._card_to_json(card)

                await session.execute(
                    text("""
                        INSERT INTO deck_cards (deck_id, card_id, quantity, zone, tags, is_commander, card_data)
                        VALUES (CAST(:deck_id AS uuid), :card_id, :quantity, :zone, :tags, :is_commander, CAST(:card_data AS jsonb))
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
            cards = [DeckController._parse_card_data(card_row) for card_row in card_rows]

        await session.commit()

        return DeckResponse(
            id=str(row[0]),
            name=row[1],
            format=row[2] or "Standard",
            description=row[3],
            cards=cards,
            createdAt=row[4].isoformat() if row[4] else None,
            updatedAt=row[5].isoformat() if row[5] else None,
        )

    @staticmethod
    async def delete_deck(
        session: AsyncSession, deck_id: str, token_data: TokenData
    ) -> None:
        """Delete a deck."""
        result = await session.execute(
            text("DELETE FROM decks WHERE id = CAST(:deck_id AS uuid) AND user_id = CAST(:user_id AS uuid) RETURNING id"),
            {"deck_id": deck_id, "user_id": token_data.user_id},
        )
        await session.commit()
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
            )
