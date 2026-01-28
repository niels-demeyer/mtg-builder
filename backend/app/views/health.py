"""
Health Views (Pydantic Schemas)

Response schemas for health check endpoints.
"""

from pydantic import BaseModel
from typing import Optional, Any


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str
    database: str
    check: Optional[Any] = None
    error: Optional[str] = None
