"""
Card Controller

Business logic for card search and lookup operations.
"""

import json
from dataclasses import asdict
from typing import Any, Dict, List

import httpx
from fastapi import HTTPException
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import DbCard


class CardController:
    """Controller for card search and lookup operations."""

    @staticmethod
    async def search_cards(
        session: AsyncSession,
        q: str = "",
        text: str = "",
        colors: str = "",
        color_match: str = "any",
        types: str = "",
        rarity: str = "",
        cmc_min: int = None,
        cmc_max: int = None,
        keywords: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Search for cards with advanced MTG filters."""
        try:
            conditions = []
            params: Dict[str, Any] = {}
            offset = (page - 1) * page_size

            # Name search
            if q and len(q) >= 2:
                conditions.append("LOWER(name) LIKE :name_pattern")
                params["name_pattern"] = f"%{q.lower()}%"

            # Oracle text search
            if text and len(text) >= 2:
                conditions.append("LOWER(oracle_text) LIKE :text_pattern")
                params["text_pattern"] = f"%{text.lower()}%"

            # Color filter
            if colors:
                color_list = [c.strip().upper() for c in colors.split(",") if c.strip()]
                if "C" in color_list:
                    # Colorless cards
                    color_list.remove("C")
                    if color_list:
                        # Looking for colorless OR specific colors
                        color_conditions = ["(colors IS NULL OR colors = '[]' OR colors = '')"]
                        for i, color in enumerate(color_list):
                            color_conditions.append(f"colors LIKE :color_{i}")
                            params[f"color_{i}"] = f'%"{color}"%'
                        conditions.append(f"({' OR '.join(color_conditions)})")
                    else:
                        # Only colorless
                        conditions.append("(colors IS NULL OR colors = '[]' OR colors = '')")
                elif color_list:
                    if color_match == "exact":
                        # Exact color match - must have all specified colors and no others
                        for i, color in enumerate(color_list):
                            conditions.append(f"colors LIKE :color_{i}")
                            params[f"color_{i}"] = f'%"{color}"%'
                        # Count colors in the card
                        conditions.append(f"(LENGTH(colors) - LENGTH(REPLACE(colors, '\"', ''))) / 2 = :color_count")
                        params["color_count"] = len(color_list)
                    elif color_match == "all":
                        # Must include all specified colors
                        for i, color in enumerate(color_list):
                            conditions.append(f"colors LIKE :color_{i}")
                            params[f"color_{i}"] = f'%"{color}"%'
                    else:
                        # Any of the specified colors (default)
                        color_conditions = []
                        for i, color in enumerate(color_list):
                            color_conditions.append(f"colors LIKE :color_{i}")
                            params[f"color_{i}"] = f'%"{color}"%'
                        conditions.append(f"({' OR '.join(color_conditions)})")

            # Type filter
            if types:
                type_list = [t.strip() for t in types.split(",") if t.strip()]
                type_conditions = []
                for i, card_type in enumerate(type_list):
                    type_conditions.append(f"LOWER(type_line) LIKE :type_{i}")
                    params[f"type_{i}"] = f"%{card_type.lower()}%"
                conditions.append(f"({' OR '.join(type_conditions)})")

            # Rarity filter
            if rarity:
                rarity_list = [r.strip().lower() for r in rarity.split(",") if r.strip()]
                rarity_placeholders = ", ".join([f":rarity_{i}" for i in range(len(rarity_list))])
                conditions.append(f"LOWER(rarity) IN ({rarity_placeholders})")
                for i, r in enumerate(rarity_list):
                    params[f"rarity_{i}"] = r

            # CMC range
            if cmc_min is not None:
                conditions.append("cmc >= :cmc_min")
                params["cmc_min"] = cmc_min
            if cmc_max is not None:
                conditions.append("cmc <= :cmc_max")
                params["cmc_max"] = cmc_max

            # Keywords filter - searches both keywords column AND oracle_text
            if keywords:
                keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
                for i, keyword in enumerate(keyword_list):
                    conditions.append(
                        f"(LOWER(keywords) LIKE :keyword_{i} OR LOWER(oracle_text) LIKE :keyword_{i})"
                    )
                    params[f"keyword_{i}"] = f"%{keyword.lower()}%"

            # Build query
            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Count query for pagination
            count_query = f"SELECT COUNT(*) FROM cards WHERE {where_clause}"

            # Data query with pagination
            data_query = f"""
                SELECT id, name, mana_cost, cmc, power, toughness, type_line,
                       oracle_text, colors, color_identity, rarity, keywords,
                       set_id, set_name, image_uris, legalities, card_faces, layout
                FROM cards
                WHERE {where_clause}
                ORDER BY name
                LIMIT :page_size OFFSET :offset
            """

            params["page_size"] = page_size
            params["offset"] = offset

            # Get total count
            count_result = await session.execute(sql_text(count_query), params)
            total_cards = count_result.scalar() or 0
            total_pages = (total_cards + page_size - 1) // page_size

            # Get paginated data
            result = await session.execute(sql_text(data_query), params)
            rows = result.fetchall()
            cards = []
            for row in rows:
                data = dict(row._mapping)
                # Parse JSON string fields
                for field in ('image_uris', 'legalities', 'colors', 'color_identity', 'keywords', 'card_faces'):
                    if field in data and isinstance(data[field], str) and data[field]:
                        try:
                            data[field] = json.loads(data[field])
                        except json.JSONDecodeError:
                            pass
                card = DbCard(**data)
                cards.append(asdict(card))

            return {
                "data": cards,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_cards": total_cards,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        except Exception as e:
            return {
                "data": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_cards": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                },
                "error": str(e)
            }

    @staticmethod
    async def get_card_printings(session: AsyncSession, card_id: str) -> Dict[str, Any]:
        """Get all printings of a card from Scryfall."""
        try:
            result = await session.execute(
                sql_text("SELECT prints_search_uri FROM cards WHERE id = :card_id"),
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
                    # For DFCs, image_uris is inside card_faces instead of top-level
                    image_uris = card.get("image_uris")
                    card_faces = card.get("card_faces")
                    if not image_uris and card_faces:
                        image_uris = card_faces[0].get("image_uris") if card_faces else None

                    printings.append({
                        "id": card.get("id"),
                        "name": card.get("name"),
                        "set_name": card.get("set_name"),
                        "set_code": card.get("set"),
                        "collector_number": card.get("collector_number"),
                        "rarity": card.get("rarity"),
                        "image_uris": image_uris,
                        "card_faces": card_faces,
                        "released_at": card.get("released_at"),
                    })

                return {"data": printings, "total_printings": len(printings)}
        except httpx.HTTPError as e:
            return {"data": [], "error": f"Failed to fetch from Scryfall: {str(e)}"}
        except Exception as e:
            return {"data": [], "error": str(e)}

    @staticmethod
    async def lookup_by_name(session: AsyncSession, name: str) -> Dict[str, Any]:
        """Look up a card by exact name."""
        # Handle special case for double-faced cards
        names_to_check = [name]
        if ' // ' in name:
            part1, part2 = name.split(' // ', 1)
            names_to_check.extend([part1.strip(), part2.strip()])
        # Convert all names to lowercase for case-insensitive search
        names_to_check = [n.lower() for n in names_to_check]

        result = await session.execute(
            sql_text("""
                SELECT id, name, mana_cost, cmc, power, toughness, type_line, oracle_text,
                       colors, color_identity, rarity, keywords, set_id, set_name, image_uris, legalities,
                       card_faces, layout
                FROM cards
                WHERE LOWER(name) = ANY(:names)
            """),
            {"names": names_to_check}
        )
        row = result.first()
        if row:
            data = dict(row._mapping)
            for field in ('image_uris', 'legalities', 'colors', 'color_identity', 'keywords', 'card_faces'):
                if field in data and isinstance(data[field], str) and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except json.JSONDecodeError:
                        pass
            card = DbCard(**data)
            return {"status": "found", **asdict(card)}
        else:
            raise HTTPException(status_code=404, detail={"status": "not found", "name": name})
