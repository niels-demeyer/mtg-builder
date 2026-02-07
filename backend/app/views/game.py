"""
Game Views (Pydantic Schemas)

Request and response schemas for game lobby endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class GameCreateRequest(BaseModel):
    """Request to create a game lobby."""
    deck_id: str
    max_players: int = Field(default=4, ge=2, le=4)


class GameJoinRequest(BaseModel):
    """Request to join a game lobby."""
    game_code: str
    deck_id: str


class LobbyPlayerResponse(BaseModel):
    """Player info in a game lobby."""
    id: str
    username: str
    deck_name: str
    ready: bool


class GameLobbyResponse(BaseModel):
    """Response for game lobby info."""
    game_code: str
    host: str
    players: list[LobbyPlayerResponse]
    max_players: int
    started: bool


class GameListResponse(BaseModel):
    """Response listing open game lobbies."""
    games: list[GameLobbyResponse]
