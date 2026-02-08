"""
Mana utility functions for game logic.

Land mana detection for tap-for-mana functionality.
"""

import re
from typing import Optional

from app.models.game import ManaPool, GameCard

ManaColor = str  # "W" | "U" | "B" | "R" | "G" | "C"
MANA_COLORS: list[ManaColor] = ["W", "U", "B", "R", "G", "C"]


def parse_land_mana_from_text(oracle_text: str) -> list[ManaColor]:
    """Parse a land's oracle text to determine what mana it can produce."""
    text = oracle_text.lower()
    colors: list[ManaColor] = []

    # Check for "any color" patterns
    any_color_patterns = [
        "add one mana of any color",
        "adds one mana of any color",
        "add mana of any color",
        "any one color",
        "mana of any type",
    ]
    for pattern in any_color_patterns:
        if pattern in text:
            return ["W", "U", "B", "R", "G"]

    # Match mana symbols in "add" statements
    add_pattern = re.compile(r"add\s+(?:\{[wubrgc]\}(?:\s*(?:,|or)\s*)?)+", re.IGNORECASE)
    add_matches = add_pattern.findall(text)

    if add_matches:
        for match in add_matches:
            if "{w}" in match:
                colors.append("W")
            if "{u}" in match:
                colors.append("U")
            if "{b}" in match:
                colors.append("B")
            if "{r}" in match:
                colors.append("R")
            if "{g}" in match:
                colors.append("G")
            if "{c}" in match:
                colors.append("C")

    # Also check for standalone mana symbol additions
    symbol_pattern = re.compile(r"\{([wubrgc])\}", re.IGNORECASE)
    for match in symbol_pattern.finditer(text):
        context_start = max(0, match.start() - 20)
        context = text[context_start : match.start()]
        if "add" in context or "produce" in context:
            color = match.group(1).upper()
            if color not in colors:
                colors.append(color)

    return list(dict.fromkeys(colors))  # deduplicate preserving order


def detect_land_mana(card: GameCard) -> list[ManaColor]:
    """Detect what mana a land can produce by reading its type line and text."""
    type_line = card.type_line.lower()
    oracle_text = card.oracle_text or ""

    # Check basic land types in type line first
    colors: list[ManaColor] = []
    if "plains" in type_line:
        colors.append("W")
    if "island" in type_line:
        colors.append("U")
    if "swamp" in type_line:
        colors.append("B")
    if "mountain" in type_line:
        colors.append("R")
    if "forest" in type_line:
        colors.append("G")

    if colors:
        return colors

    # Parse oracle text for mana production
    parsed = parse_land_mana_from_text(oracle_text)
    if parsed:
        return parsed

    # Default to colorless
    return ["C"]
