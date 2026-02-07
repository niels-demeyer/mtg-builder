"""
Mana utility functions for game logic.

Ported from frontend/src/stores/gameStore.ts
"""

import re
from dataclasses import dataclass
from typing import Optional

from app.models.game import ManaPool, GameCard

ManaColor = str  # "W" | "U" | "B" | "R" | "G" | "C"
MANA_COLORS: list[ManaColor] = ["W", "U", "B", "R", "G", "C"]


@dataclass
class ParsedManaCost:
    generic: int = 0
    W: int = 0
    U: int = 0
    B: int = 0
    R: int = 0
    G: int = 0
    C: int = 0
    total: int = 0


def parse_mana_cost(mana_cost: Optional[str]) -> ParsedManaCost:
    """Parse a mana cost string like '{2}{W}{U}' into structured data."""
    result = ParsedManaCost()
    if not mana_cost:
        return result

    symbols = re.findall(r"\{([^}]+)\}", mana_cost)
    for content in symbols:
        if content in ("W", "U", "B", "R", "G", "C"):
            setattr(result, content, getattr(result, content) + 1)
            result.total += 1
        elif content.isdigit():
            num = int(content)
            result.generic += num
            result.total += num
        elif content == "X":
            pass  # variable, don't add
        elif "/" in content:
            result.total += 1  # hybrid, count as 1

    return result


def can_pay_mana_cost(pool: ManaPool, cost: ParsedManaCost) -> bool:
    """Check if the player can pay a mana cost with their current pool."""
    if pool.W < cost.W:
        return False
    if pool.U < cost.U:
        return False
    if pool.B < cost.B:
        return False
    if pool.R < cost.R:
        return False
    if pool.G < cost.G:
        return False
    if pool.C < cost.C:
        return False

    remaining = (
        (pool.W - cost.W)
        + (pool.U - cost.U)
        + (pool.B - cost.B)
        + (pool.R - cost.R)
        + (pool.G - cost.G)
        + (pool.C - cost.C)
    )
    return remaining >= cost.generic


def pay_mana_cost(
    pool: ManaPool,
    cost: ParsedManaCost,
    generic_allocation: Optional[dict[str, int]] = None,
) -> tuple[bool, ManaPool, Optional[str]]:
    """
    Pay a mana cost from the pool.
    Returns (success, new_pool, error_message).
    """
    if not can_pay_mana_cost(pool, cost):
        return False, pool, "Not enough mana"

    new_pool = pool.copy()
    new_pool.W -= cost.W
    new_pool.U -= cost.U
    new_pool.B -= cost.B
    new_pool.R -= cost.R
    new_pool.G -= cost.G
    new_pool.C -= cost.C

    generic_remaining = cost.generic

    if generic_allocation:
        for color in MANA_COLORS:
            amount = generic_allocation.get(color, 0)
            if amount > 0:
                current = getattr(new_pool, color)
                actual = min(amount, current)
                setattr(new_pool, color, current - actual)
                generic_remaining -= actual

    # Auto-pay remaining generic (colorless first, then others)
    if generic_remaining > 0:
        pay_order = ["C", "W", "U", "B", "R", "G"]
        for color in pay_order:
            while generic_remaining > 0 and getattr(new_pool, color) > 0:
                setattr(new_pool, color, getattr(new_pool, color) - 1)
                generic_remaining -= 1

    if generic_remaining > 0:
        return False, pool, "Not enough mana for generic cost"

    return True, new_pool, None


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
