"""
Game Models

In-memory models for multiplayer game state.
These are NOT database models -- games live in memory during play.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class GamePhase(str, Enum):
    UNTAP = "untap"
    UPKEEP = "upkeep"
    DRAW = "draw"
    MAIN1 = "main1"
    COMBAT_BEGIN = "combat_begin"
    COMBAT_ATTACKERS = "combat_attackers"
    COMBAT_BLOCKERS = "combat_blockers"
    COMBAT_DAMAGE = "combat_damage"
    COMBAT_END = "combat_end"
    MAIN2 = "main2"
    END = "end"
    CLEANUP = "cleanup"


class GameZone(str, Enum):
    LIBRARY = "library"
    HAND = "hand"
    BATTLEFIELD = "battlefield"
    GRAVEYARD = "graveyard"
    EXILE = "exile"
    COMMAND = "command"


@dataclass
class GameCard:
    instance_id: str
    card_id: str
    name: str
    mana_cost: Optional[str]
    cmc: float
    type_line: str
    oracle_text: Optional[str]
    power: Optional[str]
    toughness: Optional[str]
    colors: Optional[list[str]]
    rarity: str
    image_uri: Optional[str]
    zone: GameZone
    is_tapped: bool = False
    counters: dict[str, int] = field(default_factory=dict)
    attached_to: Optional[str] = None
    face_down: bool = False
    is_commander: bool = False

    def to_dict(self) -> dict:
        return {
            "instanceId": self.instance_id,
            "cardId": self.card_id,
            "name": self.name,
            "mana_cost": self.mana_cost,
            "cmc": self.cmc,
            "type_line": self.type_line,
            "oracle_text": self.oracle_text,
            "power": self.power,
            "toughness": self.toughness,
            "colors": self.colors,
            "rarity": self.rarity,
            "image_uri": self.image_uri,
            "zone": self.zone.value,
            "isTapped": self.is_tapped,
            "counters": self.counters,
            "attachedTo": self.attached_to,
            "faceDown": self.face_down,
            "isCommander": self.is_commander,
        }

    def to_hidden_dict(self) -> dict:
        """Card representation with hidden info (for opponents' hands)."""
        return {
            "instanceId": self.instance_id,
            "faceDown": True,
            "zone": self.zone.value,
        }


@dataclass
class ManaPool:
    W: int = 0
    U: int = 0
    B: int = 0
    R: int = 0
    G: int = 0
    C: int = 0

    def to_dict(self) -> dict:
        return {"W": self.W, "U": self.U, "B": self.B, "R": self.R, "G": self.G, "C": self.C}

    def total(self) -> int:
        return self.W + self.U + self.B + self.R + self.G + self.C

    def copy(self) -> "ManaPool":
        return ManaPool(W=self.W, U=self.U, B=self.B, R=self.R, G=self.G, C=self.C)


@dataclass
class PlayerGameState:
    id: str
    name: str
    deck_id: str
    deck_name: str
    life: int = 40
    poison: int = 0
    commander_damage: dict[str, int] = field(default_factory=dict)
    mana_pool: ManaPool = field(default_factory=ManaPool)
    library: list[GameCard] = field(default_factory=list)
    hand: list[GameCard] = field(default_factory=list)
    battlefield: list[GameCard] = field(default_factory=list)
    graveyard: list[GameCard] = field(default_factory=list)
    exile: list[GameCard] = field(default_factory=list)
    command: list[GameCard] = field(default_factory=list)
    mulligan_count: int = 0
    has_drawn_opening: bool = False
    is_ready: bool = False

    def to_dict(self, is_owner: bool = False) -> dict:
        """Serialize player state. Redacts hidden zones for non-owners."""
        result: dict = {
            "id": self.id,
            "name": self.name,
            "life": self.life,
            "poison": self.poison,
            "commanderDamage": self.commander_damage,
            "manaPool": self.mana_pool.to_dict(),
            "battlefield": [c.to_dict() for c in self.battlefield],
            "graveyard": [c.to_dict() for c in self.graveyard],
            "exile": [c.to_dict() for c in self.exile],
            "command": [c.to_dict() for c in self.command],
        }

        if is_owner:
            result["library"] = [c.to_dict() for c in self.library]
            result["hand"] = [c.to_dict() for c in self.hand]
        else:
            result["library_count"] = len(self.library)
            result["hand_count"] = len(self.hand)
            result["hand"] = []
            result["library"] = []

        return result

    def find_card(self, instance_id: str) -> tuple[Optional[GameCard], Optional[GameZone]]:
        """Find a card by instance_id across all zones."""
        for zone in GameZone:
            zone_list: list[GameCard] = getattr(self, zone.value)
            for card in zone_list:
                if card.instance_id == instance_id:
                    return card, zone
        return None, None

    def remove_card(self, instance_id: str) -> Optional[GameCard]:
        """Remove a card from whatever zone it's in and return it."""
        for zone in GameZone:
            zone_list: list[GameCard] = getattr(self, zone.value)
            for i, card in enumerate(zone_list):
                if card.instance_id == instance_id:
                    return zone_list.pop(i)
        return None


@dataclass
class GameAction:
    id: str
    timestamp: float
    player_id: str
    action_type: str
    card_instance_id: Optional[str] = None
    from_zone: Optional[str] = None
    to_zone: Optional[str] = None
    details: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "playerId": self.player_id,
            "type": self.action_type,
            "cardInstanceId": self.card_instance_id,
            "fromZone": self.from_zone,
            "toZone": self.to_zone,
            "details": self.details,
        }


@dataclass
class GameRoom:
    id: str
    game_code: str
    host_id: str
    format: str = "Commander"
    max_players: int = 4
    min_players: int = 2
    players: dict[str, PlayerGameState] = field(default_factory=dict)
    turn_order: list[str] = field(default_factory=list)
    active_player_id: Optional[str] = None
    turn_number: int = 0
    phase: GamePhase = GamePhase.MAIN1
    started: bool = False
    history: list[GameAction] = field(default_factory=list)

    def to_dict(self, viewer_id: Optional[str] = None) -> dict:
        """Serialize game state, redacting hidden info based on viewer."""
        players_list = []
        for pid, player in self.players.items():
            is_owner = (pid == viewer_id) if viewer_id else False
            players_list.append(player.to_dict(is_owner=is_owner))

        return {
            "id": self.id,
            "game_code": self.game_code,
            "format": self.format,
            "players": players_list,
            "active_player_id": self.active_player_id,
            "turn_number": self.turn_number,
            "phase": self.phase.value,
            "turn_order": self.turn_order,
            "started": self.started,
            "history": [a.to_dict() for a in self.history[-20:]],
        }

    def lobby_dict(self) -> dict:
        """Lobby info for game list."""
        return {
            "game_code": self.game_code,
            "host": self.host_id,
            "players": [
                {
                    "id": p.id,
                    "username": p.name,
                    "deck_name": p.deck_name,
                    "ready": p.is_ready,
                }
                for p in self.players.values()
            ],
            "max_players": self.max_players,
            "started": self.started,
        }
