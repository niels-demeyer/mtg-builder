"""
Card Views (Pydantic Schemas)

Request and response schemas for card search and lookup endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class CardSearchParams(BaseModel):
    """Query parameters for card search."""
    q: str = ""
    text: str = ""
    colors: str = ""
    color_match: str = "any"
    types: str = ""
    rarity: str = ""
    cmc_min: Optional[int] = None
    cmc_max: Optional[int] = None
    keywords: str = ""
    page: int = 1
    page_size: int = 50


class PaginationInfo(BaseModel):
    """Pagination metadata for search results."""
    page: int
    page_size: int
    total_cards: int
    total_pages: int
    has_next: bool
    has_prev: bool


class CardSearchResponse(BaseModel):
    """Response schema for card search results."""
    data: List[Dict[str, Any]]
    pagination: PaginationInfo
    error: Optional[str] = None


class CardPrinting(BaseModel):
    """Schema for a single card printing."""
    id: str
    name: str
    set_name: str
    set_code: str
    collector_number: str
    rarity: str
    image_uris: Optional[Dict[str, str]] = None
    released_at: Optional[str] = None


class CardPrintingResponse(BaseModel):
    """Response schema for card printings."""
    data: List[CardPrinting]
    total_printings: int = 0
    error: Optional[str] = None


class CardLookupResponse(BaseModel):
    """Response schema for card name lookup."""
    status: str
    id: Optional[str] = None
    name: Optional[str] = None
    mana_cost: Optional[str] = None
    cmc: Optional[float] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    colors: Optional[List[str]] = None
    color_identity: Optional[List[str]] = None
    rarity: Optional[str] = None
    keywords: Optional[List[str]] = None
    set_id: Optional[str] = None
    set_name: Optional[str] = None
    image_uris: Optional[Dict[str, str]] = None
    legalities: Optional[Dict[str, str]] = None
