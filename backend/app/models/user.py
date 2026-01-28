"""
User Database Model

Represents the 'users' table:
- id: UUID PRIMARY KEY
- username: VARCHAR(50) UNIQUE NOT NULL
- password_hash: VARCHAR(255) NOT NULL
- created_at: TIMESTAMP DEFAULT NOW()
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Database model for the users table."""
    id: str
    username: str
    password_hash: str
    created_at: Optional[datetime] = None
