from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class ImageUris:
    small: str
    normal: str
    large: str
    png: str
    art_crop: str
    border_crop: str

@dataclass
class DbCard:
    id: str
    name: str
    mana_cost: Optional[str] = None
    cmc: int = 0
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