"""
Game Router

WebSocket endpoint for real-time game communication
and REST endpoints for game lobby management.
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, Query
from jose import JWTError, jwt
from sqlalchemy import text

from app.controllers.auth import AuthController, SECRET_KEY, ALGORITHM
from app.controllers.game import GameRoomManager
from app.views.user import TokenData


router = APIRouter()


def _verify_ws_token(token: str) -> TokenData:
    """Verify JWT token for WebSocket connections (no Depends available)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        if not username:
            return None
        return TokenData(username=username, user_id=user_id)
    except JWTError:
        return None


async def _load_deck_cards(request: Request, deck_id: str, user_id: str) -> tuple[str, list[dict]]:
    """Load a deck's cards from the database. Returns (deck_name, cards_list)."""
    session_maker = request.app.state.async_session
    async with session_maker() as session:
        # Get deck info
        result = await session.execute(
            text("""
                SELECT name, format FROM decks
                WHERE id = CAST(:deck_id AS uuid) AND user_id = CAST(:user_id AS uuid)
            """),
            {"deck_id": deck_id, "user_id": user_id},
        )
        deck_row = result.fetchone()
        if not deck_row:
            return "", []

        deck_name = deck_row[0]

        # Get cards
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
        for row in card_rows:
            card_data = row[5] if row[5] else {}
            if isinstance(card_data, str):
                card_data = json.loads(card_data)

            cards.append({
                "id": row[0],
                "name": card_data.get("name", "Unknown"),
                "mana_cost": card_data.get("mana_cost"),
                "cmc": card_data.get("cmc", 0),
                "type_line": card_data.get("type_line", ""),
                "oracle_text": card_data.get("oracle_text"),
                "power": card_data.get("power"),
                "toughness": card_data.get("toughness"),
                "colors": card_data.get("colors"),
                "rarity": card_data.get("rarity", "common"),
                "image_uri": card_data.get("image_uri"),
                "quantity": row[1],
                "zone": row[2] or "mainboard",
                "tags": row[3] or [],
                "isCommander": row[4] or False,
            })

        return deck_name, cards


def _get_game_manager(request_or_app) -> GameRoomManager:
    """Get the GameRoomManager from app state."""
    if hasattr(request_or_app, "app"):
        return request_or_app.app.state.game_manager
    return request_or_app.state.game_manager


@router.websocket("/ws/game")
async def game_websocket(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket endpoint for game communication.

    Connect: ws://localhost:8000/api/v1/ws/game?token=<jwt>

    Client sends JSON messages:
    - {"type": "create_game", "deck_id": "...", "max_players": 4}
    - {"type": "join_game", "game_code": "ABC123", "deck_id": "..."}
    - {"type": "leave_game"}
    - {"type": "player_ready"}
    - {"type": "game_action", "action": {"action": "draw_card", ...}}
    """
    # Verify JWT
    token_data = _verify_ws_token(token)
    if not token_data or not token_data.user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    user_id = token_data.user_id
    username = token_data.username or "Unknown"
    manager: GameRoomManager = _get_game_manager(websocket)
    current_game_code: str | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            if msg_type == "create_game":
                deck_id = msg.get("deck_id", "")
                max_players = msg.get("max_players", 4)

                # Load deck from DB
                deck_name, deck_cards = await _load_deck_cards(
                    websocket, deck_id, user_id
                )
                if not deck_cards:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Deck not found or empty",
                    })
                    continue

                # Leave current room if in one
                if current_game_code:
                    manager.leave_room(user_id)
                    await manager.broadcast_message(current_game_code, {
                        "type": "player_left",
                        "player_id": user_id,
                        "players": manager.rooms.get(current_game_code, None)
                            and manager.rooms[current_game_code].lobby_dict()["players"]
                            or [],
                    })

                room = manager.create_room(
                    host_id=user_id,
                    host_name=username,
                    deck_id=deck_id,
                    deck_name=deck_name,
                    deck_cards=deck_cards,
                    max_players=max_players,
                )
                current_game_code = room.game_code
                manager.register_connection(room.game_code, user_id, websocket)

                await websocket.send_json({
                    "type": "game_created",
                    "game_code": room.game_code,
                    "game_state": room.to_dict(viewer_id=user_id),
                })

            elif msg_type == "join_game":
                game_code = msg.get("game_code", "").upper()
                deck_id = msg.get("deck_id", "")

                deck_name, deck_cards = await _load_deck_cards(
                    websocket, deck_id, user_id
                )
                if not deck_cards:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Deck not found or empty",
                    })
                    continue

                # Leave current room if in one
                if current_game_code:
                    manager.leave_room(user_id)

                room, error = manager.join_room(
                    game_code=game_code,
                    user_id=user_id,
                    username=username,
                    deck_id=deck_id,
                    deck_name=deck_name,
                    deck_cards=deck_cards,
                )

                if error:
                    await websocket.send_json({"type": "error", "message": error})
                    continue

                current_game_code = game_code
                manager.register_connection(game_code, user_id, websocket)

                # Notify all players with lobby info
                await manager.broadcast_message(game_code, {
                    "type": "player_joined",
                    "player_id": user_id,
                    "player_name": username,
                    "players": room.lobby_dict()["players"],
                })

                # Broadcast full game state to ALL players so everyone has
                # the current player list (not just lobby info)
                await manager.broadcast_state(game_code)

            elif msg_type == "leave_game":
                if current_game_code:
                    manager.leave_room(user_id)
                    room = manager.rooms.get(current_game_code)
                    players = room.lobby_dict()["players"] if room else []
                    await manager.broadcast_message(current_game_code, {
                        "type": "player_left",
                        "player_id": user_id,
                        "players": players,
                    })
                    current_game_code = None

                await websocket.send_json({"type": "left_game"})

            elif msg_type == "game_action":
                if not current_game_code:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Not in a game",
                    })
                    continue

                action = msg.get("action", {})
                success, error = manager.handle_action(
                    current_game_code, user_id, action
                )

                if not success:
                    await websocket.send_json({
                        "type": "action_rejected",
                        "reason": error or "Action failed",
                        "action": action,
                    })
                else:
                    # Broadcast updated state to all players
                    await manager.broadcast_state(current_game_code)

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        # Cleanup on disconnect
        manager.unregister_connection(user_id)
        if current_game_code:
            room = manager.rooms.get(current_game_code)
            manager.leave_room(user_id)
            if room and room.players:
                await manager.broadcast_message(current_game_code, {
                    "type": "player_left",
                    "player_id": user_id,
                    "players": room.lobby_dict()["players"],
                })


@router.get("/games")
async def list_games(request: Request):
    """List open game lobbies that can be joined."""
    manager: GameRoomManager = _get_game_manager(request)
    return {"games": manager.get_open_rooms()}
