"""
Card Database Model

Represents the 'cards' table (populated from Scryfall):
- id: VARCHAR PRIMARY KEY
- name: VARCHAR NOT NULL
- mana_cost: VARCHAR
- cmc: INTEGER
- power: VARCHAR
- toughness: VARCHAR
- type_line: VARCHAR
- oracle_text: TEXT
- colors: JSONB (list of color characters)
- color_identity: JSONB (list of color characters)
- rarity: VARCHAR
- keywords: JSONB (list of keywords)
- set_id: VARCHAR
- set_name: VARCHAR
- image_uris: JSONB
- legalities: JSONB
- prints_search_uri: VARCHAR
"""

from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class ImageUris:
    """Image URLs for different card image sizes."""
    small: str = ""
    normal: str = ""
    large: str = ""
    png: str = ""
    art_crop: str = ""
    border_crop: str = ""


@dataclass
class DbCard:
    """Database model for the cards table."""
    id: str
    name: str
    mana_cost: Optional[str] = None
    cmc: float = 0
    power: Optional[str] = None
    toughness: Optional[str] = None
    type_line: str = ""
    oracle_text: Optional[str] = None
    colors: Optional[List[str]] = None
    color_identity: Optional[List[str]] = None
    rarity: str = ""
    keywords: Optional[List[str]] = None
    set_id: str = ""
    set_name: str = ""
    image_uris: Optional[ImageUris] = None
    legalities: Optional[Dict[str, str]] = None
    prints_search_uri: Optional[str] = None
    card_faces: Optional[List[Dict]] = None
    layout: Optional[str] = None
