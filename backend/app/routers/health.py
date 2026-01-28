"""
Health Router

API routes for health checks.
"""

from typing import Any

from fastapi import APIRouter, Request

from app.controllers.health import HealthController

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check(request: Request) -> dict[str, Any]:
    """Health check endpoint that verifies database connectivity."""
    async with request.app.state.async_session() as session:
        return await HealthController.check_health(session)
