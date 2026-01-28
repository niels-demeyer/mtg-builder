"""
Deck Database Model

Represents the 'decks' table:
- id: UUID PRIMARY KEY
- user_id: UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
- name: VARCHAR(100) NOT NULL
- format: VARCHAR(50) DEFAULT 'Standard'
- description: TEXT
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Deck:
    """Database model for the decks table."""
    id: str
    user_id: str
    name: str
    format: str = "Standard"
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
