"""
Routers

API route definitions that wire together views and controllers.
Routers are thin layers that handle HTTP requests and delegate to controllers.
"""

from app.routers.auth import router as auth_router
from app.routers.deck import router as deck_router
from app.routers.card import router as card_router
from app.routers.health import router as health_router
from app.routers.game import router as game_router

__all__ = [
    "auth_router",
    "deck_router",
    "card_router",
    "health_router",
    "game_router",
]
