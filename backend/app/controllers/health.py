"""
Health Controller

Business logic for health check operations.
"""

from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthController:
    """Controller for health check operations."""

    @staticmethod
    async def check_health(session: AsyncSession) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            return {"status": "healthy", "database": "connected", "check": value}
        except Exception as e:
            return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
