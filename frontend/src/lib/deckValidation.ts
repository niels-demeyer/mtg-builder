import type { Deck, CardInDeck, DeckFormat, CardZone } from './types';

export type ValidationSeverity = 'error' | 'warning';

// Types of automatic fixes that can be applied
export type FixType =
  | 'remove_duplicates_singleton'  // Remove duplicates for singleton formats (keep 1)
  | 'remove_duplicates_4of'        // Remove duplicates exceeding 4 copies
  | 'trim_sideboard'               // Remove excess sideboard cards
  | 'move_to_mainboard';           // Move cards from commander zone to mainboard

export interface ValidationIssue {
  severity: ValidationSeverity;
  message: string;
  cards?: string[];           // Card names involved in the issue
  fixType?: FixType;          // Type of fix that can be applied
  fixDescription?: string;    // Human-readable description of the fix
}

// Basic land names that are exempt from duplicate rules
const BASIC_LANDS = [
  'Plains',
  'Island',
  'Swamp',
  'Mountain',
  'Forest',
  'Wastes',
  // Snow-covered basics
  'Snow-Covered Plains',
  'Snow-Covered Island',
  'Snow-Covered Swamp',
  'Snow-Covered Mountain',
  'Snow-Covered Forest',
];

export function isBasicLand(cardName: string): boolean {
  return BASIC_LANDS.includes(cardName);
}

function getMainboardAndCommanderCards(deck: Deck): CardInDeck[] {
  return deck.cards.filter(c => c.zone === 'mainboard' || c.zone === 'commander');
}

function getMainboardCards(deck: Deck): CardInDeck[] {
  return deck.cards.filter(c => c.zone === 'mainboard');
}

function getSideboardCards(deck: Deck): CardInDeck[] {
  return deck.cards.filter(c => c.zone === 'sideboard');
}

function getCommanderCards(deck: Deck): CardInDeck[] {
  return deck.cards.filter(c => c.zone === 'commander');
}

function getTotalCount(cards: CardInDeck[]): number {
  return cards.reduce((sum, c) => sum + c.quantity, 0);
}

function findDuplicates(cards: CardInDeck[], maxCopies: number): CardInDeck[] {
  const cardCounts = new Map<string, number>();

  // Aggregate counts by card name (excluding basic lands)
  for (const card of cards) {
    if (isBasicLand(card.name)) continue;
    const current = cardCounts.get(card.name) || 0;
    cardCounts.set(card.name, current + card.quantity);
  }

  // Find cards that exceed the limit
  return cards.filter(card => {
    if (isBasicLand(card.name)) return false;
    const total = cardCounts.get(card.name) || 0;
    return total > maxCopies;
  });
}

function validateCommander(deck: Deck): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const deckCards = getMainboardAndCommanderCards(deck);
  const commanderCards = getCommanderCards(deck);
  const totalCards = getTotalCount(deckCards);

  // Check for commander presence
  if (commanderCards.length === 0) {
    issues.push({
      severity: 'error',
      message: 'Commander format requires a commander in the Commander zone',
    });
  } else if (getTotalCount(commanderCards) > 2) {
    issues.push({
      severity: 'error',
      message: 'Commander format allows at most 2 commanders (with Partner)',
      cards: commanderCards.map(c => c.name),
    });
  }

  // Check deck size (exactly 100 including commander)
  if (totalCards < 100) {
    issues.push({
      severity: 'error',
      message: `Commander decks must have exactly 100 cards (currently ${totalCards})`,
    });
  } else if (totalCards > 100) {
    issues.push({
      severity: 'error',
      message: `Commander decks must have exactly 100 cards (currently ${totalCards}, ${totalCards - 100} too many)`,
    });
  }

  // Check for duplicates (singleton format)
  const duplicates = findDuplicates(deckCards, 1);
  if (duplicates.length > 0) {
    const uniqueNames = [...new Set(duplicates.map(c => c.name))];
    // Calculate total excess copies properly by grouping by card name
    const cardTotals = new Map<string, number>();
    for (const card of deckCards) {
      if (isBasicLand(card.name)) continue;
      cardTotals.set(card.name, (cardTotals.get(card.name) || 0) + card.quantity);
    }
    const extraCopies = Array.from(cardTotals.values())
      .filter(total => total > 1)
      .reduce((sum, total) => sum + (total - 1), 0);
    issues.push({
      severity: 'error',
      message: `Commander is singleton - no duplicate cards allowed (except basic lands)`,
      cards: uniqueNames,
      fixType: 'remove_duplicates_singleton',
      fixDescription: `Remove ${extraCopies} duplicate ${extraCopies === 1 ? 'copy' : 'copies'}`,
    });
  }

  // Sideboard check (Commander typically doesn't use sideboards in casual play)
  const sideboardCards = getSideboardCards(deck);
  const sideboardCount = getTotalCount(sideboardCards);
  if (sideboardCount > 0) {
    issues.push({
      severity: 'warning',
      message: `Commander typically doesn't use a sideboard (${sideboardCount} cards in sideboard)`,
    });
  }

  return issues;
}

function validateBrawl(deck: Deck): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const deckCards = getMainboardAndCommanderCards(deck);
  const commanderCards = getCommanderCards(deck);
  const totalCards = getTotalCount(deckCards);

  // Check for commander presence
  if (commanderCards.length === 0) {
    issues.push({
      severity: 'error',
      message: 'Brawl format requires a commander in the Commander zone',
    });
  } else if (getTotalCount(commanderCards) > 1) {
    issues.push({
      severity: 'error',
      message: 'Brawl format allows only 1 commander',
      cards: commanderCards.map(c => c.name),
    });
  }

  // Check deck size (exactly 60 including commander)
  if (totalCards < 60) {
    issues.push({
      severity: 'error',
      message: `Brawl decks must have exactly 60 cards (currently ${totalCards})`,
    });
  } else if (totalCards > 60) {
    issues.push({
      severity: 'error',
      message: `Brawl decks must have exactly 60 cards (currently ${totalCards}, ${totalCards - 60} too many)`,
    });
  }

  // Check for duplicates (singleton format)
  const duplicates = findDuplicates(deckCards, 1);
  if (duplicates.length > 0) {
    const uniqueNames = [...new Set(duplicates.map(c => c.name))];
    // Calculate total excess copies properly by grouping by card name
    const cardTotals = new Map<string, number>();
    for (const card of deckCards) {
      if (isBasicLand(card.name)) continue;
      cardTotals.set(card.name, (cardTotals.get(card.name) || 0) + card.quantity);
    }
    const extraCopies = Array.from(cardTotals.values())
      .filter(total => total > 1)
      .reduce((sum, total) => sum + (total - 1), 0);
    issues.push({
      severity: 'error',
      message: `Brawl is singleton - no duplicate cards allowed (except basic lands)`,
      cards: uniqueNames,
      fixType: 'remove_duplicates_singleton',
      fixDescription: `Remove ${extraCopies} duplicate ${extraCopies === 1 ? 'copy' : 'copies'}`,
    });
  }

  return issues;
}

function validateConstructed(deck: Deck, formatName: string): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const mainboardCards = getMainboardCards(deck);
  const sideboardCards = getSideboardCards(deck);
  const mainboardCount = getTotalCount(mainboardCards);
  const sideboardCount = getTotalCount(sideboardCards);

  // Check minimum mainboard size (60 cards)
  if (mainboardCount < 60) {
    issues.push({
      severity: 'error',
      message: `${formatName} decks require at least 60 cards in mainboard (currently ${mainboardCount})`,
    });
  }

  // Check sideboard size (max 15)
  if (sideboardCount > 15) {
    const excess = sideboardCount - 15;
    issues.push({
      severity: 'error',
      message: `Sideboard cannot exceed 15 cards (currently ${sideboardCount})`,
      fixType: 'trim_sideboard',
      fixDescription: `Remove ${excess} ${excess === 1 ? 'card' : 'cards'} from sideboard`,
    });
  }

  // Check for too many copies (max 4 of each non-basic)
  // Combine mainboard and sideboard for 4-of check
  const allPlayableCards = [...mainboardCards, ...sideboardCards];
  const duplicates = findDuplicates(allPlayableCards, 4);
  if (duplicates.length > 0) {
    const uniqueNames = [...new Set(duplicates.map(c => c.name))];
    // Calculate total excess copies
    const cardCounts = new Map<string, number>();
    for (const card of allPlayableCards) {
      if (isBasicLand(card.name)) continue;
      cardCounts.set(card.name, (cardCounts.get(card.name) || 0) + card.quantity);
    }
    const excessCopies = Array.from(cardCounts.values())
      .filter(count => count > 4)
      .reduce((sum, count) => sum + (count - 4), 0);
    issues.push({
      severity: 'error',
      message: `Maximum 4 copies of each card allowed (except basic lands)`,
      cards: uniqueNames,
      fixType: 'remove_duplicates_4of',
      fixDescription: `Remove ${excessCopies} excess ${excessCopies === 1 ? 'copy' : 'copies'}`,
    });
  }

  // Check if commander zone is used (shouldn't be in constructed)
  const commanderCards = getCommanderCards(deck);
  if (commanderCards.length > 0) {
    issues.push({
      severity: 'warning',
      message: `${formatName} format doesn't use a commander zone`,
      cards: commanderCards.map(c => c.name),
      fixType: 'move_to_mainboard',
      fixDescription: `Move ${getTotalCount(commanderCards)} ${getTotalCount(commanderCards) === 1 ? 'card' : 'cards'} to mainboard`,
    });
  }

  return issues;
}

function validatePauper(deck: Deck): ValidationIssue[] {
  const issues = validateConstructed(deck, 'Pauper');

  // Check for non-common cards
  const mainboardCards = getMainboardCards(deck);
  const sideboardCards = getSideboardCards(deck);
  const allCards = [...mainboardCards, ...sideboardCards];

  const nonCommonCards = allCards.filter(c => c.rarity !== 'common');
  if (nonCommonCards.length > 0) {
    const uniqueNames = [...new Set(nonCommonCards.map(c => c.name))];
    issues.push({
      severity: 'error',
      message: `Pauper only allows common rarity cards`,
      cards: uniqueNames,
    });
  }

  return issues;
}

export function validateDeck(deck: Deck): ValidationIssue[] {
  if (!deck || deck.cards.length === 0) {
    return [];
  }

  switch (deck.format) {
    case 'Commander':
      return validateCommander(deck);
    case 'Brawl':
      return validateBrawl(deck);
    case 'Standard':
      return validateConstructed(deck, 'Standard');
    case 'Modern':
      return validateConstructed(deck, 'Modern');
    case 'Legacy':
      return validateConstructed(deck, 'Legacy');
    case 'Vintage':
      return validateConstructed(deck, 'Vintage');
    case 'Pioneer':
      return validateConstructed(deck, 'Pioneer');
    case 'Historic':
      return validateConstructed(deck, 'Historic');
    case 'Pauper':
      return validatePauper(deck);
    case 'Custom':
      // No validation for custom format
      return [];
    default:
      return [];
  }
}

export function hasErrors(issues: ValidationIssue[]): boolean {
  return issues.some(issue => issue.severity === 'error');
}

export function hasWarnings(issues: ValidationIssue[]): boolean {
  return issues.some(issue => issue.severity === 'warning');
}

export function getErrorCount(issues: ValidationIssue[]): number {
  return issues.filter(issue => issue.severity === 'error').length;
}

export function getWarningCount(issues: ValidationIssue[]): number {
  return issues.filter(issue => issue.severity === 'warning').length;
}

// Fix functions that return the modified cards array

/**
 * Remove duplicate cards to enforce singleton rule (keep 1 copy of each non-basic)
 */
export function fixSingletonDuplicates(cards: CardInDeck[]): CardInDeck[] {
  const seenCards = new Set<string>();
  return cards.map(card => {
    // Basic lands are exempt
    if (isBasicLand(card.name)) {
      return card;
    }
    // Check if we've seen this card before
    const key = `${card.name}-${card.zone}`;
    if (seenCards.has(key)) {
      // Remove entirely (will be filtered out)
      return { ...card, quantity: 0 };
    }
    seenCards.add(key);
    // Keep only 1 copy
    if (card.quantity > 1) {
      return { ...card, quantity: 1 };
    }
    return card;
  }).filter(card => card.quantity > 0);
}

/**
 * Remove excess copies to enforce 4-of rule (keep max 4 copies across all zones)
 */
export function fix4ofDuplicates(cards: CardInDeck[]): CardInDeck[] {
  const cardCounts = new Map<string, number>();

  return cards.map(card => {
    // Basic lands are exempt
    if (isBasicLand(card.name)) {
      return card;
    }

    const currentCount = cardCounts.get(card.name) || 0;
    const remainingAllowed = Math.max(0, 4 - currentCount);

    if (remainingAllowed === 0) {
      // Already at 4 copies, remove this one entirely
      return { ...card, quantity: 0 };
    }

    const newQuantity = Math.min(card.quantity, remainingAllowed);
    cardCounts.set(card.name, currentCount + newQuantity);

    if (newQuantity !== card.quantity) {
      return { ...card, quantity: newQuantity };
    }
    return card;
  }).filter(card => card.quantity > 0);
}

/**
 * Trim sideboard to max 15 cards (removes from end)
 */
export function fixSideboardSize(cards: CardInDeck[]): CardInDeck[] {
  let sideboardCount = 0;
  const sideboardCards = cards.filter(c => c.zone === 'sideboard');
  const otherCards = cards.filter(c => c.zone !== 'sideboard');

  // Calculate current sideboard count
  for (const card of sideboardCards) {
    sideboardCount += card.quantity;
  }

  if (sideboardCount <= 15) {
    return cards;
  }

  // Need to trim
  let excess = sideboardCount - 15;
  const trimmedSideboard = sideboardCards.map(card => {
    if (excess <= 0) return card;

    if (card.quantity <= excess) {
      excess -= card.quantity;
      return { ...card, quantity: 0 };
    } else {
      const newQuantity = card.quantity - excess;
      excess = 0;
      return { ...card, quantity: newQuantity };
    }
  }).filter(card => card.quantity > 0);

  return [...otherCards, ...trimmedSideboard];
}

/**
 * Move cards from commander zone to mainboard
 */
export function fixMoveCommanderToMainboard(cards: CardInDeck[]): CardInDeck[] {
  return cards.map(card => {
    if (card.zone === 'commander') {
      return { ...card, zone: 'mainboard' as CardZone };
    }
    return card;
  });
}
