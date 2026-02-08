"""
Game Controller

Business logic for multiplayer game management.
Manages game rooms, validates actions, and mutates authoritative game state.
"""

import json
import random
import string
import time
import uuid
from typing import Optional

from fastapi import WebSocket

from app.models.game import (
    GameRoom,
    PlayerGameState,
    GameCard,
    GameZone,
    GamePhase,
    ManaPool,
    GameAction,
)
from app.controllers.mana_utils import (
    detect_land_mana,
    ManaColor,
    MANA_COLORS,
)


def _generate_id() -> str:
    return f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:9]}"


def _shuffle(cards: list[GameCard]) -> list[GameCard]:
    """Fisher-Yates shuffle, returns new list."""
    shuffled = list(cards)
    for i in range(len(shuffled) - 1, 0, -1):
        j = random.randint(0, i)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def _card_from_deck_data(card_data: dict, zone: GameZone) -> GameCard:
    """Convert a deck card dict (from DB card_data + deck_cards fields) into a GameCard."""
    return GameCard(
        instance_id=_generate_id(),
        card_id=card_data.get("id", ""),
        name=card_data.get("name", "Unknown"),
        mana_cost=card_data.get("mana_cost"),
        cmc=card_data.get("cmc", 0),
        type_line=card_data.get("type_line", ""),
        oracle_text=card_data.get("oracle_text"),
        power=card_data.get("power"),
        toughness=card_data.get("toughness"),
        colors=card_data.get("colors"),
        rarity=card_data.get("rarity", "common"),
        image_uri=card_data.get("image_uri"),
        zone=zone,
        is_commander=card_data.get("isCommander", False),
    )


def _expand_deck_cards(cards: list[dict], zone: GameZone) -> list[GameCard]:
    """Expand deck cards (respecting quantity) into game cards."""
    game_cards: list[GameCard] = []
    for card in cards:
        quantity = card.get("quantity", 1)
        for _ in range(quantity):
            game_cards.append(_card_from_deck_data(card, zone))
    return game_cards


class GameActionHandler:
    """Handles individual game actions with validation."""

    @staticmethod
    def draw_card(player: PlayerGameState) -> tuple[bool, Optional[str]]:
        if not player.library:
            return False, "Library is empty"
        card = player.library.pop(0)
        card.zone = GameZone.HAND
        player.hand.append(card)
        return True, None

    @staticmethod
    def draw_opening_hand(player: PlayerGameState) -> tuple[bool, Optional[str]]:
        hand_size = max(0, 7 - player.mulligan_count)
        for _ in range(min(hand_size, len(player.library))):
            card = player.library.pop(0)
            card.zone = GameZone.HAND
            player.hand.append(card)
        player.has_drawn_opening = True
        return True, None

    @staticmethod
    def mulligan(player: PlayerGameState) -> tuple[bool, Optional[str]]:
        if player.mulligan_count >= 6:
            return False, "Cannot mulligan further"
        # Put hand back into library
        for card in player.hand:
            card.zone = GameZone.LIBRARY
        player.library.extend(player.hand)
        player.hand.clear()
        player.library = _shuffle(player.library)
        player.mulligan_count += 1
        # Draw new hand
        GameActionHandler.draw_opening_hand(player)
        return True, None

    @staticmethod
    def keep_hand(player: PlayerGameState) -> tuple[bool, Optional[str]]:
        player.is_ready = True
        return True, None

    @staticmethod
    def play_card(
        player: PlayerGameState,
        instance_id: str,
    ) -> tuple[bool, Optional[str]]:
        # Find card in hand
        card = None
        for i, c in enumerate(player.hand):
            if c.instance_id == instance_id:
                card = player.hand.pop(i)
                break
        if not card:
            return False, "Card not found in hand"

        card.zone = GameZone.BATTLEFIELD
        card.is_tapped = False
        player.battlefield.append(card)
        return True, None

    @staticmethod
    def move_card(
        player: PlayerGameState, instance_id: str, to_zone: GameZone
    ) -> tuple[bool, Optional[str]]:
        card = player.remove_card(instance_id)
        if not card:
            return False, "Card not found"

        card.zone = to_zone
        if to_zone in (GameZone.HAND, GameZone.LIBRARY):
            card.is_tapped = False

        zone_list: list[GameCard] = getattr(player, to_zone.value)
        zone_list.append(card)
        return True, None

    @staticmethod
    def discard_card(
        player: PlayerGameState, instance_id: str
    ) -> tuple[bool, Optional[str]]:
        for i, card in enumerate(player.hand):
            if card.instance_id == instance_id:
                card = player.hand.pop(i)
                card.zone = GameZone.GRAVEYARD
                player.graveyard.append(card)
                return True, None
        return False, "Card not found in hand"

    @staticmethod
    def tap_card(
        player: PlayerGameState, instance_id: str
    ) -> tuple[bool, Optional[str]]:
        for card in player.battlefield:
            if card.instance_id == instance_id:
                card.is_tapped = not card.is_tapped
                return True, None
        return False, "Card not found on battlefield"

    @staticmethod
    def tap_for_mana(
        player: PlayerGameState, instance_id: str, color: ManaColor
    ) -> tuple[bool, Optional[str]]:
        for card in player.battlefield:
            if card.instance_id == instance_id:
                if card.is_tapped:
                    return False, "Card is already tapped"
                card.is_tapped = True
                current = getattr(player.mana_pool, color, 0)
                setattr(player.mana_pool, color, current + 1)
                return True, None
        return False, "Card not found on battlefield"

    @staticmethod
    def untap_all(player: PlayerGameState) -> tuple[bool, Optional[str]]:
        for card in player.battlefield:
            card.is_tapped = False
        return True, None

    @staticmethod
    def add_mana(
        player: PlayerGameState, color: ManaColor, amount: int = 1
    ) -> tuple[bool, Optional[str]]:
        if color not in MANA_COLORS:
            return False, f"Invalid mana color: {color}"
        current = getattr(player.mana_pool, color, 0)
        setattr(player.mana_pool, color, current + amount)
        return True, None

    @staticmethod
    def remove_mana(
        player: PlayerGameState, color: ManaColor, amount: int = 1
    ) -> tuple[bool, Optional[str]]:
        if color not in MANA_COLORS:
            return False, f"Invalid mana color: {color}"
        current = getattr(player.mana_pool, color, 0)
        setattr(player.mana_pool, color, max(0, current - amount))
        return True, None

    @staticmethod
    def clear_mana_pool(player: PlayerGameState) -> tuple[bool, Optional[str]]:
        player.mana_pool = ManaPool()
        return True, None

    @staticmethod
    def shuffle_library(player: PlayerGameState) -> tuple[bool, Optional[str]]:
        player.library = _shuffle(player.library)
        return True, None

    @staticmethod
    def mill(player: PlayerGameState, count: int) -> tuple[bool, Optional[str]]:
        for _ in range(min(count, len(player.library))):
            card = player.library.pop(0)
            card.zone = GameZone.GRAVEYARD
            player.graveyard.append(card)
        return True, None

    @staticmethod
    def update_life(player: PlayerGameState, change: int) -> tuple[bool, Optional[str]]:
        player.life += change
        return True, None

    @staticmethod
    def add_counter(
        player: PlayerGameState, instance_id: str, counter_type: str
    ) -> tuple[bool, Optional[str]]:
        for card in player.battlefield:
            if card.instance_id == instance_id:
                card.counters[counter_type] = card.counters.get(counter_type, 0) + 1
                return True, None
        return False, "Card not found on battlefield"

    @staticmethod
    def remove_counter(
        player: PlayerGameState, instance_id: str, counter_type: str
    ) -> tuple[bool, Optional[str]]:
        for card in player.battlefield:
            if card.instance_id == instance_id:
                count = card.counters.get(counter_type, 0)
                if count <= 1:
                    card.counters.pop(counter_type, None)
                else:
                    card.counters[counter_type] = count - 1
                return True, None
        return False, "Card not found on battlefield"


class GameRoomManager:
    """Singleton managing all active game rooms and WebSocket connections."""

    def __init__(self) -> None:
        self.rooms: dict[str, GameRoom] = {}  # game_code -> GameRoom
        self.connections: dict[str, dict[str, WebSocket]] = {}  # game_code -> {user_id -> WS}
        self.player_room: dict[str, str] = {}  # user_id -> game_code

    def _generate_game_code(self) -> str:
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self.rooms:
                return code

    def create_room(
        self,
        host_id: str,
        host_name: str,
        deck_id: str,
        deck_name: str,
        deck_cards: list[dict],
        max_players: int = 4,
    ) -> GameRoom:
        """Create a new game room and initialize the host's player state."""
        game_code = self._generate_game_code()
        room = GameRoom(
            id=_generate_id(),
            game_code=game_code,
            host_id=host_id,
            max_players=max_players,
        )

        # Initialize host player
        player = self._init_player(host_id, host_name, deck_id, deck_name, deck_cards)
        room.players[host_id] = player

        self.rooms[game_code] = room
        self.connections[game_code] = {}
        self.player_room[host_id] = game_code
        return room

    def _init_player(
        self,
        user_id: str,
        username: str,
        deck_id: str,
        deck_name: str,
        deck_cards: list[dict],
    ) -> PlayerGameState:
        """Create a PlayerGameState from deck data."""
        commander_cards = [c for c in deck_cards if c.get("isCommander", False)]
        library_cards = [c for c in deck_cards if not c.get("isCommander", False)]

        library = _shuffle(_expand_deck_cards(library_cards, GameZone.LIBRARY))
        command = _expand_deck_cards(commander_cards, GameZone.COMMAND)

        return PlayerGameState(
            id=user_id,
            name=username,
            deck_id=deck_id,
            deck_name=deck_name,
            life=40,  # Commander default
            library=library,
            command=command,
        )

    def join_room(
        self,
        game_code: str,
        user_id: str,
        username: str,
        deck_id: str,
        deck_name: str,
        deck_cards: list[dict],
    ) -> tuple[Optional[GameRoom], Optional[str]]:
        """Add a player to an existing room. Returns (room, error)."""
        room = self.rooms.get(game_code)
        if not room:
            return None, "Game not found"
        if room.started:
            return None, "Game already started"
        if len(room.players) >= room.max_players:
            return None, "Game is full"
        if user_id in room.players:
            return None, "Already in this game"

        player = self._init_player(user_id, username, deck_id, deck_name, deck_cards)
        room.players[user_id] = player
        self.player_room[user_id] = game_code
        return room, None

    def leave_room(self, user_id: str) -> Optional[str]:
        """Remove a player from their room. Returns game_code or None."""
        game_code = self.player_room.pop(user_id, None)
        if not game_code:
            return None

        room = self.rooms.get(game_code)
        if not room:
            return game_code

        room.players.pop(user_id, None)
        self.connections.get(game_code, {}).pop(user_id, None)

        # If room is empty, clean it up
        if not room.players:
            self.rooms.pop(game_code, None)
            self.connections.pop(game_code, None)

        return game_code

    def register_connection(self, game_code: str, user_id: str, ws: WebSocket) -> None:
        if game_code not in self.connections:
            self.connections[game_code] = {}
        self.connections[game_code][user_id] = ws

    def unregister_connection(self, user_id: str) -> None:
        game_code = self.player_room.get(user_id)
        if game_code and game_code in self.connections:
            self.connections[game_code].pop(user_id, None)

    def start_game(self, game_code: str) -> tuple[bool, Optional[str]]:
        """Start the game if all players are ready."""
        room = self.rooms.get(game_code)
        if not room:
            return False, "Game not found"
        if room.started:
            return False, "Game already started"
        if len(room.players) < room.min_players:
            return False, f"Need at least {room.min_players} players"

        all_ready = all(p.is_ready for p in room.players.values())
        if not all_ready:
            return False, "Not all players are ready"

        # Randomize turn order
        player_ids = list(room.players.keys())
        random.shuffle(player_ids)
        room.turn_order = player_ids
        room.active_player_id = player_ids[0]
        room.turn_number = 1
        room.phase = GamePhase.MAIN1
        room.started = True

        return True, None

    def handle_action(
        self, game_code: str, user_id: str, action: dict
    ) -> tuple[bool, Optional[str]]:
        """Validate and execute a game action. Returns (success, error)."""
        room = self.rooms.get(game_code)
        if not room:
            return False, "Game not found"

        player = room.players.get(user_id)
        if not player:
            return False, "Player not in game"

        action_type = action.get("action", "")

        # Pre-game actions (mulligan/keep)
        if not room.started:
            if action_type == "mulligan":
                return GameActionHandler.mulligan(player)
            elif action_type == "keep_hand":
                success, error = GameActionHandler.keep_hand(player)
                if success:
                    # Check if all players are ready to start
                    all_ready = all(p.is_ready for p in room.players.values())
                    if all_ready and len(room.players) >= room.min_players:
                        self.start_game(game_code)
                return success, error
            elif action_type == "draw_opening_hand":
                if not player.has_drawn_opening:
                    return GameActionHandler.draw_opening_hand(player)
                return False, "Opening hand already drawn"
            return False, "Game has not started yet"

        # In-game actions -- all players can act freely (casual Commander)
        handler_map: dict[str, any] = {
            "draw_card": lambda: GameActionHandler.draw_card(player),
            "play_card": lambda: GameActionHandler.play_card(
                player,
                action.get("instance_id", ""),
            ),
            "move_card": lambda: GameActionHandler.move_card(
                player,
                action.get("instance_id", ""),
                GameZone(action.get("to_zone", "battlefield")),
            ),
            "discard_card": lambda: GameActionHandler.discard_card(
                player, action.get("instance_id", "")
            ),
            "tap_card": lambda: GameActionHandler.tap_card(
                player, action.get("instance_id", "")
            ),
            "tap_for_mana": lambda: GameActionHandler.tap_for_mana(
                player, action.get("instance_id", ""), action.get("color", "C")
            ),
            "untap_all": lambda: GameActionHandler.untap_all(player),
            "add_mana": lambda: GameActionHandler.add_mana(
                player, action.get("color", "C"), action.get("amount", 1)
            ),
            "remove_mana": lambda: GameActionHandler.remove_mana(
                player, action.get("color", "C"), action.get("amount", 1)
            ),
            "clear_mana_pool": lambda: GameActionHandler.clear_mana_pool(player),
            "shuffle_library": lambda: GameActionHandler.shuffle_library(player),
            "mill": lambda: GameActionHandler.mill(
                player, action.get("count", 1)
            ),
            "update_life": lambda: GameActionHandler.update_life(
                player, action.get("change", 0)
            ),
            "add_counter": lambda: GameActionHandler.add_counter(
                player,
                action.get("instance_id", ""),
                action.get("counter_type", "+1/+1"),
            ),
            "remove_counter": lambda: GameActionHandler.remove_counter(
                player,
                action.get("instance_id", ""),
                action.get("counter_type", "+1/+1"),
            ),
            "set_phase": lambda: self._set_phase(
                room, action.get("phase", "main1")
            ),
            "next_turn": lambda: self._next_turn(room, user_id),
        }

        handler = handler_map.get(action_type)
        if not handler:
            return False, f"Unknown action: {action_type}"

        success, error = handler()

        # Record action in history
        if success:
            room.history.append(
                GameAction(
                    id=_generate_id(),
                    timestamp=time.time(),
                    player_id=user_id,
                    action_type=action_type,
                    card_instance_id=action.get("instance_id"),
                    from_zone=None,
                    to_zone=action.get("to_zone"),
                    details=action.get("details"),
                )
            )

        return success, error

    @staticmethod
    def _set_phase(room: GameRoom, phase_str: str) -> tuple[bool, Optional[str]]:
        try:
            room.phase = GamePhase(phase_str)
            return True, None
        except ValueError:
            return False, f"Invalid phase: {phase_str}"

    @staticmethod
    def _next_turn(room: GameRoom, user_id: str) -> tuple[bool, Optional[str]]:
        """Advance to next turn. Untap active player, clear mana, advance turn order."""
        if not room.turn_order:
            return False, "No turn order set"

        # Untap current active player's permanents and clear mana
        active_player = room.players.get(room.active_player_id or "")
        if active_player:
            GameActionHandler.untap_all(active_player)
            GameActionHandler.clear_mana_pool(active_player)

        # Advance to next player
        current_idx = -1
        if room.active_player_id in room.turn_order:
            current_idx = room.turn_order.index(room.active_player_id)

        next_idx = (current_idx + 1) % len(room.turn_order)
        room.active_player_id = room.turn_order[next_idx]
        room.turn_number += 1
        room.phase = GamePhase.UNTAP

        return True, None

    async def broadcast_state(self, game_code: str) -> None:
        """Send redacted game state to each connected player."""
        room = self.rooms.get(game_code)
        if not room:
            return

        conns = self.connections.get(game_code, {})
        disconnected: list[str] = []

        for user_id, ws in conns.items():
            state = room.to_dict(viewer_id=user_id)
            try:
                await ws.send_json({
                    "type": "game_state_update",
                    "game_state": state,
                })
            except Exception:
                disconnected.append(user_id)

        for uid in disconnected:
            conns.pop(uid, None)

    async def broadcast_message(
        self, game_code: str, message: dict, exclude: Optional[str] = None
    ) -> None:
        """Send a message to all players in a room."""
        conns = self.connections.get(game_code, {})
        disconnected: list[str] = []

        for user_id, ws in conns.items():
            if user_id == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(user_id)

        for uid in disconnected:
            conns.pop(uid, None)

    def get_open_rooms(self) -> list[dict]:
        """List all joinable rooms."""
        return [
            room.lobby_dict()
            for room in self.rooms.values()
            if not room.started and len(room.players) < room.max_players
        ]

    def get_room_for_player(self, user_id: str) -> Optional[GameRoom]:
        game_code = self.player_room.get(user_id)
        if game_code:
            return self.rooms.get(game_code)
        return None
