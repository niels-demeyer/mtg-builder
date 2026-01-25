import type { Deck, CardInDeck, CardZone, DeckFormat } from "./types";

/**
 * Export a deck to txt format.
 * Format:
 * // Deck: My Deck Name
 * // Format: Standard
 * // Description: Optional description
 *
 * // Commander
 * 1 Atraxa, Praetors' Voice
 *
 * // Mainboard
 * 4 Lightning Bolt
 * 3 Counterspell
 *
 * // Sideboard
 * 2 Surgical Extraction
 *
 * // Maybeboard
 * 1 Some Card
 */
export function exportDeckToTxt(deck: Deck): string {
  const lines: string[] = [];

  // Header with metadata
  lines.push(`// Deck: ${deck.name}`);
  lines.push(`// Format: ${deck.format}`);
  if (deck.description) {
    lines.push(`// Description: ${deck.description}`);
  }
  lines.push("");

  // Group cards by zone
  const zones: CardZone[] = [
    "commander",
    "mainboard",
    "sideboard",
    "maybeboard",
    "considering",
  ];

  for (const zone of zones) {
    const cardsInZone = deck.cards.filter((c) => c.zone === zone);
    if (cardsInZone.length === 0) continue;

    const zoneName = zone.charAt(0).toUpperCase() + zone.slice(1);
    lines.push(`// ${zoneName}`);

    // Sort by name for consistent output
    const sortedCards = [...cardsInZone].sort((a, b) =>
      a.name.localeCompare(b.name)
    );

    for (const card of sortedCards) {
      lines.push(`${card.quantity} ${card.name}`);
    }
    lines.push("");
  }

  return lines.join("\n").trim();
}

/**
 * Parse result from importing a deck txt file.
 */
export interface ParsedDeck {
  name: string;
  format: DeckFormat;
  description: string;
  cards: ParsedCard[];
}

export interface ParsedCard {
  name: string;
  quantity: number;
  zone: CardZone;
}

/**
 * Parse a deck txt file into a ParsedDeck structure.
 * Supports multiple formats:
 * - Standard format: "4 Lightning Bolt" or "4x Lightning Bolt"
 * - Zone headers: "// Sideboard", "Sideboard:", "SB:", etc.
 * - Metadata: "// Deck: Name", "// Format: Standard"
 */
export function parseDeckTxt(content: string): ParsedDeck {
  const lines = content.split(/\r?\n/);

  let name = "Imported Deck";
  let format: DeckFormat = "Standard";
  let description = "";
  let currentZone: CardZone = "mainboard";
  const cards: ParsedCard[] = [];

  for (let line of lines) {
    line = line.trim();

    // Skip empty lines
    if (!line) continue;

    // Check for metadata comments
    const deckMatch = line.match(/^\/\/\s*Deck:\s*(.+)$/i);
    if (deckMatch) {
      name = deckMatch[1].trim();
      continue;
    }

    const formatMatch = line.match(/^\/\/\s*Format:\s*(.+)$/i);
    if (formatMatch) {
      const formatValue = formatMatch[1].trim();
      if (isValidFormat(formatValue)) {
        format = formatValue as DeckFormat;
      }
      continue;
    }

    const descMatch = line.match(/^\/\/\s*Description:\s*(.+)$/i);
    if (descMatch) {
      description = descMatch[1].trim();
      continue;
    }

    // Check for zone headers
    const zoneHeader = parseZoneHeader(line);
    if (zoneHeader) {
      currentZone = zoneHeader;
      continue;
    }

    // Skip other comments
    if (line.startsWith("//") || line.startsWith("#")) {
      continue;
    }

    // Parse card line
    const cardMatch = parseCardLine(line);
    if (cardMatch) {
      cards.push({
        name: cardMatch.name,
        quantity: cardMatch.quantity,
        zone: currentZone,
      });
    }
  }

  return { name, format, description, cards };
}

function isValidFormat(format: string): boolean {
  const validFormats = [
    "Standard",
    "Modern",
    "Legacy",
    "Vintage",
    "Commander",
    "Pioneer",
    "Pauper",
    "Historic",
    "Brawl",
    "Custom",
  ];
  return validFormats.includes(format);
}

function parseZoneHeader(line: string): CardZone | null {
  // Match patterns like: "// Sideboard", "Sideboard:", "SB:", "SIDEBOARD"
  const normalizedLine = line
    .replace(/^\/\/\s*/, "")
    .replace(/:$/, "")
    .toLowerCase()
    .trim();

  const zoneMap: Record<string, CardZone> = {
    mainboard: "mainboard",
    main: "mainboard",
    maindeck: "mainboard",
    deck: "mainboard",
    sideboard: "sideboard",
    side: "sideboard",
    sb: "sideboard",
    maybeboard: "maybeboard",
    maybe: "maybeboard",
    considering: "considering",
    commander: "commander",
    cmdr: "commander",
  };

  return zoneMap[normalizedLine] || null;
}

function parseCardLine(
  line: string
): { name: string; quantity: number } | null {
  // Match patterns like:
  // "4 Lightning Bolt"
  // "4x Lightning Bolt"
  // "4X Lightning Bolt"
  // "Lightning Bolt" (assume quantity 1)
  // "1x Ashaya, Soul of the Wild (sld) 2014 [Commander{top}]"
  // "1x Forest (tmt) 314 *F* [Land]"

  // Remove foil markers like *F*
  line = line.replace(/\s*\*F\*\s*/gi, " ");

  // Remove tags in square brackets (can contain any characters): [Artifact], [Commander{top}]
  line = line.replace(/\s*\[[^\]]*\]\s*/g, " ");

  // Remove set codes in parentheses: (sld), (LEA), (m20)
  line = line.replace(/\s*\([a-z0-9]+\)\s*/gi, " ");

  // Remove collector numbers (standalone numbers after removing set codes)
  line = line.replace(/\s+\d+\s*$/, "");
  line = line.replace(/\s+\d+★?\s+/g, " ");

  // Remove set codes with dashes like FUT-167, LEA-123, etc.
  line = line.replace(/\s+[A-Z]+-\d+\s*/gi, " ");

  // Clean up extra whitespace
  line = line.replace(/\s+/g, " ").trim();

  // Try to match "quantity cardname" format
  const match = line.match(/^(\d+)\s*x?\s+(.+)$/i);
  if (match) {
    return {
      quantity: parseInt(match[1], 10),
      name: match[2].trim(),
    };
  }

  // If no quantity, assume 1 (but only if it looks like a card name)
  if (line.length > 0 && !line.match(/^\d+$/)) {
    return {
      quantity: 1,
      name: line,
    };
  }

  return null;
}

/**
 * Generate a filename for exporting a deck.
 */
export function generateDeckFilename(deck: Deck): string {
  const safeName = deck.name
    .replace(/[^a-zA-Z0-9\s-]/g, "")
    .replace(/\s+/g, "_")
    .toLowerCase();
  return `${safeName}.txt`;
}

/**
 * Download a deck as a txt file.
 */
export function downloadDeckAsTxt(deck: Deck): void {
  const content = exportDeckToTxt(deck);
  const filename = generateDeckFilename(deck);

  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}
