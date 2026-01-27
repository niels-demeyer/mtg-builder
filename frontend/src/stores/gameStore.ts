import { writable, derived } from "svelte/store";
import type {
  Deck,
  CardInDeck,
  GameState,
  GameCard,
  GameZone,
  GameAction,
  GameActionType,
  GamePhase,
  PlayerState,
  GameStoreState,
  OpeningHandEvaluation,
  DeckFormat,
  ManaPool,
} from "$lib/types";

// Empty mana pool
const emptyManaPool: ManaPool = { W: 0, U: 0, B: 0, R: 0, G: 0, C: 0 };

// Mana color type
export type ManaColor = "W" | "U" | "B" | "R" | "G" | "C";

// Parsed mana cost structure
export interface ParsedManaCost {
  generic: number;        // Generic mana (can be paid with any color)
  W: number;              // White mana required
  U: number;              // Blue mana required
  B: number;              // Black mana required
  R: number;              // Red mana required
  G: number;              // Green mana required
  C: number;              // Colorless mana required (only payable with colorless)
  total: number;          // Total mana value
}

// Parse a mana cost string like "{2}{W}{U}" into structured data
export function parseManaCost(manaCost: string | undefined): ParsedManaCost {
  const result: ParsedManaCost = { generic: 0, W: 0, U: 0, B: 0, R: 0, G: 0, C: 0, total: 0 };

  if (!manaCost) return result;

  // Match all mana symbols in the cost string
  const symbols = manaCost.match(/\{[^}]+\}/g) || [];

  for (const symbol of symbols) {
    const content = symbol.slice(1, -1); // Remove { and }

    // Check for colored mana
    if (content === "W") { result.W++; result.total++; }
    else if (content === "U") { result.U++; result.total++; }
    else if (content === "B") { result.B++; result.total++; }
    else if (content === "R") { result.R++; result.total++; }
    else if (content === "G") { result.G++; result.total++; }
    else if (content === "C") { result.C++; result.total++; }
    // Check for generic mana (numbers)
    else if (/^\d+$/.test(content)) {
      const num = parseInt(content, 10);
      result.generic += num;
      result.total += num;
    }
    // X costs are treated as 0 for now
    else if (content === "X") {
      // X is variable, don't add to cost
    }
    // Hybrid mana like {W/U} - for now treat as first color
    else if (content.includes("/")) {
      result.total++;
      // We'll handle hybrid specially in payment
    }
  }

  return result;
}

// Check if the player can pay a mana cost with their current pool
export function canPayManaCost(pool: ManaPool, cost: ParsedManaCost): boolean {
  // First check if we have enough colored mana
  if (pool.W < cost.W) return false;
  if (pool.U < cost.U) return false;
  if (pool.B < cost.B) return false;
  if (pool.R < cost.R) return false;
  if (pool.G < cost.G) return false;
  if (pool.C < cost.C) return false;

  // Calculate remaining mana after paying colored costs
  const remainingPool = {
    W: pool.W - cost.W,
    U: pool.U - cost.U,
    B: pool.B - cost.B,
    R: pool.R - cost.R,
    G: pool.G - cost.G,
    C: pool.C - cost.C,
  };

  // Total remaining mana available for generic cost
  const totalRemaining = remainingPool.W + remainingPool.U + remainingPool.B +
                         remainingPool.R + remainingPool.G + remainingPool.C;

  return totalRemaining >= cost.generic;
}

// Result of paying mana - the new pool after payment
export interface ManaPaymentResult {
  success: boolean;
  newPool: ManaPool;
  error?: string;
}

// Pay a mana cost from the pool, using a specific allocation for generic mana
// genericAllocation specifies how to pay the generic mana portion
export function payManaCost(
  pool: ManaPool,
  cost: ParsedManaCost,
  genericAllocation?: Partial<ManaPool>
): ManaPaymentResult {
  if (!canPayManaCost(pool, cost)) {
    return { success: false, newPool: pool, error: "Not enough mana" };
  }

  // Start with colored mana payment
  const newPool: ManaPool = {
    W: pool.W - cost.W,
    U: pool.U - cost.U,
    B: pool.B - cost.B,
    R: pool.R - cost.R,
    G: pool.G - cost.G,
    C: pool.C - cost.C,
  };

  // Pay generic mana
  let genericRemaining = cost.generic;

  if (genericAllocation) {
    // Use specified allocation
    for (const color of ["W", "U", "B", "R", "G", "C"] as ManaColor[]) {
      const amount = genericAllocation[color] || 0;
      if (amount > 0) {
        newPool[color] -= amount;
        genericRemaining -= amount;
      }
    }
  }

  // Auto-pay remaining generic with available mana (colorless first, then others)
  if (genericRemaining > 0) {
    const payOrder: ManaColor[] = ["C", "W", "U", "B", "R", "G"];
    for (const color of payOrder) {
      while (genericRemaining > 0 && newPool[color] > 0) {
        newPool[color]--;
        genericRemaining--;
      }
    }
  }

  if (genericRemaining > 0) {
    return { success: false, newPool: pool, error: "Not enough mana for generic cost" };
  }

  return { success: true, newPool };
}

// Land mana production patterns
const landManaProduction: Record<string, ManaColor[]> = {
  // Basic lands
  "plains": ["W"],
  "island": ["U"],
  "swamp": ["B"],
  "mountain": ["R"],
  "forest": ["G"],
  "wastes": ["C"],
  // Common dual land patterns (detected by name)
  "hallowed fountain": ["W", "U"],
  "watery grave": ["U", "B"],
  "blood crypt": ["B", "R"],
  "stomping ground": ["R", "G"],
  "temple garden": ["G", "W"],
  "godless shrine": ["W", "B"],
  "steam vents": ["U", "R"],
  "overgrown tomb": ["B", "G"],
  "sacred foundry": ["R", "W"],
  "breeding pool": ["G", "U"],
  // Check lands
  "glacial fortress": ["W", "U"],
  "drowned catacomb": ["U", "B"],
  "dragonskull summit": ["B", "R"],
  "rootbound crag": ["R", "G"],
  "sunpetal grove": ["G", "W"],
  "isolated chapel": ["W", "B"],
  "sulfur falls": ["U", "R"],
  "woodland cemetery": ["B", "G"],
  "clifftop retreat": ["R", "W"],
  "hinterland harbor": ["G", "U"],
  // Pathways (MDFC)
  "brightclimb pathway": ["W", "B"],
  "clearwater pathway": ["U", "B"],
  "cragcrown pathway": ["R", "G"],
  "needleverge pathway": ["R", "W"],
  "riverglide pathway": ["U", "R"],
  "blightstep pathway": ["B", "R"],
  "barkchannel pathway": ["G", "U"],
  "branchloft pathway": ["G", "W"],
  "darkbore pathway": ["B", "G"],
  "hengegate pathway": ["W", "U"],
  // Triomes
  "indatha triome": ["W", "B", "G"],
  "ketria triome": ["U", "R", "G"],
  "raugrin triome": ["U", "R", "W"],
  "savai triome": ["R", "W", "B"],
  "zagoth triome": ["B", "G", "U"],
  "spara's headquarters": ["G", "W", "U"],
  "raffine's tower": ["W", "U", "B"],
  "xander's lounge": ["U", "B", "R"],
  "ziatora's proving ground": ["B", "R", "G"],
  "jetmir's garden": ["R", "G", "W"],
  // Command Tower produces all colors
  "command tower": ["W", "U", "B", "R", "G"],
  // City of Brass / Mana Confluence
  "city of brass": ["W", "U", "B", "R", "G"],
  "mana confluence": ["W", "U", "B", "R", "G"],
  // Fetch lands don't tap for mana
};

// Detect what mana a land can produce
export function detectLandMana(card: GameCard): ManaColor[] {
  const name = card.name.toLowerCase();
  const typeLine = card.type_line.toLowerCase();
  const oracleText = (card.oracle_text || "").toLowerCase();

  // Check known lands first
  if (landManaProduction[name]) {
    return landManaProduction[name];
  }

  // Check basic land types in type line
  const colors: ManaColor[] = [];
  if (typeLine.includes("plains")) colors.push("W");
  if (typeLine.includes("island")) colors.push("U");
  if (typeLine.includes("swamp")) colors.push("B");
  if (typeLine.includes("mountain")) colors.push("R");
  if (typeLine.includes("forest")) colors.push("G");

  if (colors.length > 0) return colors;

  // Parse oracle text for mana production
  if (oracleText.includes("add {w}") || oracleText.includes("add one mana of any color")) colors.push("W");
  if (oracleText.includes("add {u}") || oracleText.includes("add one mana of any color")) colors.push("U");
  if (oracleText.includes("add {b}") || oracleText.includes("add one mana of any color")) colors.push("B");
  if (oracleText.includes("add {r}") || oracleText.includes("add one mana of any color")) colors.push("R");
  if (oracleText.includes("add {g}") || oracleText.includes("add one mana of any color")) colors.push("G");
  if (oracleText.includes("add {c}")) colors.push("C");

  // Check for "any color" text
  if (oracleText.includes("any color") && colors.length === 0) {
    return ["W", "U", "B", "R", "G"];
  }

  // Default to colorless if we can't determine
  if (colors.length === 0) {
    colors.push("C");
  }

  return [...new Set(colors)]; // Remove duplicates
}

// Helper to generate unique IDs
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
}

// Convert deck card to game card instance
function cardToGameCard(card: CardInDeck, zone: GameZone): GameCard {
  return {
    instanceId: generateId(),
    cardId: card.id,
    name: card.name,
    mana_cost: card.mana_cost,
    cmc: card.cmc,
    type_line: card.type_line,
    oracle_text: card.oracle_text,
    power: card.power,
    toughness: card.toughness,
    colors: card.colors,
    rarity: card.rarity,
    image_uri: card.image_uri,
    zone,
    isTapped: false,
    counters: {},
    faceDown: false,
    isCommander: card.isCommander,
  };
}

// Expand deck cards (respecting quantity) into game cards
function expandDeckToGameCards(
  cards: CardInDeck[],
  zone: GameZone
): GameCard[] {
  const gameCards: GameCard[] = [];
  cards.forEach((card) => {
    for (let i = 0; i < card.quantity; i++) {
      gameCards.push(cardToGameCard(card, zone));
    }
  });
  return gameCards;
}

// Fisher-Yates shuffle
function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

// Initial state
const initialState: GameStoreState = {
  game: null,
  selectedCard: null,
  isLoading: false,
  error: null,
};

// Create the store
function createGameStore() {
  const { subscribe, set, update } = writable<GameStoreState>(initialState);

  // Add action to game history
  function addAction(
    state: GameStoreState,
    type: GameActionType,
    cardInstanceId?: string,
    fromZone?: GameZone,
    toZone?: GameZone,
    details?: string
  ): GameStoreState {
    if (!state.game) return state;

    const action: GameAction = {
      id: generateId(),
      timestamp: Date.now(),
      type,
      cardInstanceId,
      fromZone,
      toZone,
      details,
    };

    return {
      ...state,
      game: {
        ...state.game,
        history: [...state.game.history, action],
      },
    };
  }

  return {
    subscribe,

    // Initialize a new game from a deck
    initGame(deck: Deck): void {
      update((state) => {
        const mainboardCards = deck.cards.filter(
          (c) => c.zone === "mainboard" || c.zone === "commander"
        );
        const commanderCards = mainboardCards.filter((c) => c.isCommander);
        const libraryCards = mainboardCards.filter((c) => !c.isCommander);

        // Create game cards and shuffle library
        const library = shuffleArray(
          expandDeckToGameCards(libraryCards, "library")
        );
        const command = expandDeckToGameCards(commanderCards, "command");

        const player: PlayerState = {
          id: generateId(),
          name: "Player 1",
          life: deck.format === "Commander" || deck.format === "Brawl" ? 40 : 20,
          poison: 0,
          commanderDamage: {},
          manaPool: { ...emptyManaPool },
          library,
          hand: [],
          battlefield: [],
          graveyard: [],
          exile: [],
          command,
        };

        const game: GameState = {
          id: generateId(),
          deckId: deck.id,
          deckName: deck.name,
          format: deck.format,
          player,
          turnNumber: 0,
          phase: "main1",
          history: [],
          mulliganCount: 0,
          started: false,
        };

        return { ...state, game, selectedCard: null, error: null };
      });
    },

    // Draw opening hand (7 cards minus mulligan count)
    drawOpeningHand(): void {
      update((state) => {
        if (!state.game) return state;

        const handSize = 7 - state.game.mulliganCount;
        const library = [...state.game.player.library];
        const hand: GameCard[] = [];

        for (let i = 0; i < Math.min(handSize, library.length); i++) {
          const card = library.shift()!;
          card.zone = "hand";
          hand.push(card);
        }

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              library,
              hand,
            },
          },
        };

        // Add action to history
        newState = addAction(
          newState,
          "draw",
          undefined,
          undefined,
          undefined,
          `Drew opening hand of ${handSize} cards`
        );

        return newState;
      });
    },

    // Mulligan - shuffle hand back, draw one fewer
    mulligan(): void {
      update((state) => {
        if (!state.game) return state;

        // Put hand back into library
        const hand = state.game.player.hand.map((c) => ({
          ...c,
          zone: "library" as GameZone,
        }));
        const library = shuffleArray([...state.game.player.library, ...hand]);

        // Increment mulligan count
        const mulliganCount = state.game.mulliganCount + 1;

        // Draw new hand
        const handSize = Math.max(0, 7 - mulliganCount);
        const newHand: GameCard[] = [];

        for (let i = 0; i < Math.min(handSize, library.length); i++) {
          const card = library.shift()!;
          card.zone = "hand";
          newHand.push(card);
        }

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            mulliganCount,
            player: {
              ...state.game.player,
              library,
              hand: newHand,
            },
          },
        };

        newState = addAction(
          newState,
          "mulligan",
          undefined,
          undefined,
          undefined,
          `Mulligan to ${handSize} cards`
        );

        return newState;
      });
    },

    // Start the game (keep hand, proceed to turn 1)
    startGame(): void {
      update((state) => {
        if (!state.game) return state;

        return {
          ...state,
          game: {
            ...state.game,
            started: true,
            turnNumber: 1,
            phase: "main1",
          },
        };
      });
    },

    // Draw a card
    drawCard(): void {
      update((state) => {
        if (!state.game || state.game.player.library.length === 0) return state;

        const library = [...state.game.player.library];
        const card = library.shift()!;
        card.zone = "hand";

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              library,
              hand: [...state.game.player.hand, card],
            },
          },
        };

        newState = addAction(newState, "draw", card.instanceId, "library", "hand");
        return newState;
      });
    },

    // Move card between zones
    moveCard(instanceId: string, toZone: GameZone): void {
      update((state) => {
        if (!state.game) return state;

        const player = { ...state.game.player };
        let card: GameCard | undefined;
        let fromZone: GameZone | undefined;

        // Find and remove card from current zone
        const zones: GameZone[] = [
          "library",
          "hand",
          "battlefield",
          "graveyard",
          "exile",
          "command",
        ];

        for (const zone of zones) {
          const zoneArray = player[zone] as GameCard[];
          const index = zoneArray.findIndex((c) => c.instanceId === instanceId);
          if (index !== -1) {
            card = { ...zoneArray[index], zone: toZone };
            fromZone = zone;
            player[zone] = zoneArray.filter((c) => c.instanceId !== instanceId);
            break;
          }
        }

        if (!card || !fromZone) return state;

        // Add card to new zone
        (player[toZone] as GameCard[]).push(card);

        // Untap if moving to hand or library
        if (toZone === "hand" || toZone === "library") {
          card.isTapped = false;
        }

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player,
          },
        };

        const actionType: GameActionType =
          toZone === "graveyard"
            ? "destroy"
            : toZone === "exile"
            ? "exile"
            : toZone === "hand"
            ? "return"
            : "play";

        newState = addAction(newState, actionType, instanceId, fromZone, toZone);
        return newState;
      });
    },

    // Play card from hand to battlefield (without mana payment)
    playCard(instanceId: string): void {
      this.moveCard(instanceId, "battlefield");
    },

    // Play card from hand to battlefield with mana payment
    playCardWithMana(
      instanceId: string,
      genericAllocation?: Partial<ManaPool>
    ): { success: boolean; error?: string } {
      let result: { success: boolean; error?: string } = { success: false, error: "" };

      update((state) => {
        if (!state.game) {
          result = { success: false, error: "No game in progress" };
          return state;
        }

        // Find the card in hand
        const card = state.game.player.hand.find((c) => c.instanceId === instanceId);
        if (!card) {
          result = { success: false, error: "Card not found in hand" };
          return state;
        }

        // Check if it's a land (lands don't cost mana)
        const isLand = card.type_line.toLowerCase().includes("land");
        if (isLand) {
          // Lands are free to play, just move them
          result = { success: true };
          // We'll handle the actual move after this update
          return state;
        }

        // Parse the mana cost
        const cost = parseManaCost(card.mana_cost);

        // If no mana cost, play for free
        if (cost.total === 0) {
          result = { success: true };
          return state;
        }

        // Try to pay the mana cost
        const paymentResult = payManaCost(
          state.game.player.manaPool,
          cost,
          genericAllocation
        );

        if (!paymentResult.success) {
          result = { success: false, error: paymentResult.error || "Payment failed" };
          return state;
        }

        // Update mana pool and move card
        const hand = state.game.player.hand.filter((c) => c.instanceId !== instanceId);
        const movedCard = { ...card, zone: "battlefield" as GameZone, isTapped: false };
        const battlefield = [...state.game.player.battlefield, movedCard];

        result = { success: true };

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              hand,
              battlefield,
              manaPool: paymentResult.newPool,
            },
          },
        };

        newState = addAction(newState, "play", instanceId, "hand", "battlefield");
        return newState;
      });

      // If we need to handle land separately (since we returned early from update)
      if (result.success) {
        // Check if we already moved it in the update
        let needsMove = false;
        const unsubscribe = subscribe((state) => {
          if (state.game) {
            const stillInHand = state.game.player.hand.some((c) => c.instanceId === instanceId);
            needsMove = stillInHand;
          }
        });
        unsubscribe();

        if (needsMove) {
          this.moveCard(instanceId, "battlefield");
        }
      }

      return result;
    },

    // Get a card from hand by instance ID
    getCardFromHand(instanceId: string): GameCard | undefined {
      let result: GameCard | undefined;
      const unsubscribe = subscribe((state) => {
        if (state.game) {
          result = state.game.player.hand.find((c) => c.instanceId === instanceId);
        }
      });
      unsubscribe();
      return result;
    },

    // Check if player can afford to play a card
    canAffordCard(instanceId: string): boolean {
      let result = false;
      const unsubscribe = subscribe((state) => {
        if (!state.game) return;

        const card = state.game.player.hand.find((c) => c.instanceId === instanceId);
        if (!card) return;

        // Lands are free
        if (card.type_line.toLowerCase().includes("land")) {
          result = true;
          return;
        }

        const cost = parseManaCost(card.mana_cost);
        result = canPayManaCost(state.game.player.manaPool, cost);
      });
      unsubscribe();
      return result;
    },

    // Discard card from hand
    discardCard(instanceId: string): void {
      update((state) => {
        if (!state.game) return state;

        const hand = state.game.player.hand;
        const index = hand.findIndex((c) => c.instanceId === instanceId);
        if (index === -1) return state;

        const card = { ...hand[index], zone: "graveyard" as GameZone };
        const newHand = hand.filter((c) => c.instanceId !== instanceId);
        const graveyard = [...state.game.player.graveyard, card];

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              hand: newHand,
              graveyard,
            },
          },
        };

        newState = addAction(
          newState,
          "discard",
          instanceId,
          "hand",
          "graveyard"
        );
        return newState;
      });
    },

    // Tap/untap a card on the battlefield
    toggleTap(instanceId: string): void {
      update((state) => {
        if (!state.game) return state;

        const battlefield = state.game.player.battlefield.map((c) => {
          if (c.instanceId === instanceId) {
            return { ...c, isTapped: !c.isTapped };
          }
          return c;
        });

        const card = battlefield.find((c) => c.instanceId === instanceId);
        if (!card) return state;

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              battlefield,
            },
          },
        };

        newState = addAction(
          newState,
          card.isTapped ? "tap" : "untap",
          instanceId
        );
        return newState;
      });
    },

    // Untap all permanents
    untapAll(): void {
      update((state) => {
        if (!state.game) return state;

        const battlefield = state.game.player.battlefield.map((c) => ({
          ...c,
          isTapped: false,
        }));

        return {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              battlefield,
            },
          },
        };
      });
    },

    // Shuffle library
    shuffleLibrary(): void {
      update((state) => {
        if (!state.game) return state;

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              library: shuffleArray(state.game.player.library),
            },
          },
        };

        newState = addAction(
          newState,
          "shuffle",
          undefined,
          undefined,
          undefined,
          "Shuffled library"
        );
        return newState;
      });
    },

    // Mill cards (top of library to graveyard)
    mill(count: number): void {
      update((state) => {
        if (!state.game) return state;

        const library = [...state.game.player.library];
        const graveyard = [...state.game.player.graveyard];

        for (let i = 0; i < Math.min(count, library.length); i++) {
          const card = library.shift()!;
          card.zone = "graveyard";
          graveyard.push(card);
        }

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              library,
              graveyard,
            },
          },
        };

        newState = addAction(
          newState,
          "mill",
          undefined,
          "library",
          "graveyard",
          `Milled ${count} cards`
        );
        return newState;
      });
    },

    // Update life total
    updateLife(change: number): void {
      update((state) => {
        if (!state.game) return state;

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              life: state.game.player.life + change,
            },
          },
        };

        newState = addAction(
          newState,
          "life_change",
          undefined,
          undefined,
          undefined,
          `Life ${change >= 0 ? "+" : ""}${change} (${newState.game!.player.life})`
        );
        return newState;
      });
    },

    // Add counter to card
    addCounter(instanceId: string, counterType: string): void {
      update((state) => {
        if (!state.game) return state;

        const battlefield = state.game.player.battlefield.map((c) => {
          if (c.instanceId === instanceId) {
            return {
              ...c,
              counters: {
                ...c.counters,
                [counterType]: (c.counters[counterType] || 0) + 1,
              },
            };
          }
          return c;
        });

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              battlefield,
            },
          },
        };

        newState = addAction(
          newState,
          "counter_add",
          instanceId,
          undefined,
          undefined,
          `Added ${counterType} counter`
        );
        return newState;
      });
    },

    // Remove counter from card
    removeCounter(instanceId: string, counterType: string): void {
      update((state) => {
        if (!state.game) return state;

        const battlefield = state.game.player.battlefield.map((c) => {
          if (c.instanceId === instanceId) {
            const count = c.counters[counterType] || 0;
            const newCounters = { ...c.counters };
            if (count <= 1) {
              delete newCounters[counterType];
            } else {
              newCounters[counterType] = count - 1;
            }
            return { ...c, counters: newCounters };
          }
          return c;
        });

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              battlefield,
            },
          },
        };

        newState = addAction(
          newState,
          "counter_remove",
          instanceId,
          undefined,
          undefined,
          `Removed ${counterType} counter`
        );
        return newState;
      });
    },

    // Add mana to the pool
    addMana(color: ManaColor, amount: number = 1): void {
      update((state) => {
        if (!state.game) return state;

        const manaPool = { ...state.game.player.manaPool };
        manaPool[color] = (manaPool[color] || 0) + amount;

        return {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              manaPool,
            },
          },
        };
      });
    },

    // Remove mana from the pool
    removeMana(color: ManaColor, amount: number = 1): void {
      update((state) => {
        if (!state.game) return state;

        const manaPool = { ...state.game.player.manaPool };
        manaPool[color] = Math.max(0, (manaPool[color] || 0) - amount);

        return {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              manaPool,
            },
          },
        };
      });
    },

    // Clear the mana pool
    clearManaPool(): void {
      update((state) => {
        if (!state.game) return state;

        return {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              manaPool: { ...emptyManaPool },
            },
          },
        };
      });
    },

    // Tap a land and add mana
    tapLandForMana(instanceId: string, color: ManaColor): void {
      update((state) => {
        if (!state.game) return state;

        const battlefield = state.game.player.battlefield.map((c) => {
          if (c.instanceId === instanceId && !c.isTapped) {
            return { ...c, isTapped: true };
          }
          return c;
        });

        const card = state.game.player.battlefield.find(
          (c) => c.instanceId === instanceId
        );
        if (!card || card.isTapped) return state;

        const manaPool = { ...state.game.player.manaPool };
        manaPool[color] = (manaPool[color] || 0) + 1;

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              battlefield,
              manaPool,
            },
          },
        };

        newState = addAction(
          newState,
          "tap",
          instanceId,
          undefined,
          undefined,
          `Tapped for {${color}}`
        );
        return newState;
      });
    },

    // Set phase
    setPhase(phase: GamePhase): void {
      update((state) => {
        if (!state.game) return state;

        return {
          ...state,
          game: {
            ...state.game,
            phase,
          },
        };
      });
    },

    // Next turn
    nextTurn(): void {
      update((state) => {
        if (!state.game) return state;

        return {
          ...state,
          game: {
            ...state.game,
            turnNumber: state.game.turnNumber + 1,
            phase: "untap",
          },
        };
      });
    },

    // Select card for preview
    selectCard(card: GameCard | null): void {
      update((state) => ({ ...state, selectedCard: card }));
    },

    // Scry (look at top N cards)
    getTopCards(count: number): GameCard[] {
      let result: GameCard[] = [];
      const unsubscribe = subscribe((state) => {
        if (state.game) {
          result = state.game.player.library.slice(0, count);
        }
      });
      unsubscribe();
      return result;
    },

    // Reorder top of library (for scry)
    reorderTopCards(cardIds: string[], toBottom: string[]): void {
      update((state) => {
        if (!state.game) return state;

        const library = [...state.game.player.library];
        const topCount = cardIds.length + toBottom.length;
        const remaining = library.slice(topCount);

        // Cards staying on top (in order)
        const onTop = cardIds
          .map((id) =>
            library.slice(0, topCount).find((c) => c.instanceId === id)
          )
          .filter(Boolean) as GameCard[];

        // Cards going to bottom (in order)
        const goToBottom = toBottom
          .map((id) =>
            library.slice(0, topCount).find((c) => c.instanceId === id)
          )
          .filter(Boolean) as GameCard[];

        const newLibrary = [...onTop, ...remaining, ...goToBottom];

        let newState: GameStoreState = {
          ...state,
          game: {
            ...state.game,
            player: {
              ...state.game.player,
              library: newLibrary,
            },
          },
        };

        newState = addAction(
          newState,
          "scry",
          undefined,
          undefined,
          undefined,
          `Scried ${topCount} cards`
        );
        return newState;
      });
    },

    // Reset game
    reset(): void {
      set(initialState);
    },

    // Evaluate opening hand quality
    evaluateOpeningHand(): OpeningHandEvaluation | null {
      let result: OpeningHandEvaluation | null = null;
      const unsubscribe = subscribe((state) => {
        if (!state.game) return;

        const hand = state.game.player.hand;
        const landCount = hand.filter((c) =>
          c.type_line.toLowerCase().includes("land")
        ).length;
        const nonLandCount = hand.length - landCount;

        const nonLandCards = hand.filter(
          (c) => !c.type_line.toLowerCase().includes("land")
        );
        const averageCmc =
          nonLandCards.length > 0
            ? nonLandCards.reduce((sum, c) => sum + c.cmc, 0) / nonLandCards.length
            : 0;

        const hasEarlyPlay = nonLandCards.some((c) => c.cmc <= 2);
        const hasMidGame = nonLandCards.some((c) => c.cmc >= 3 && c.cmc <= 4);

        const colorCoverage = [
          ...new Set(hand.flatMap((c) => c.colors || [])),
        ];

        // Calculate keep score
        let keepScore = 50;

        // Land count scoring (ideal is 2-3 for 7 card hand)
        if (landCount === 2 || landCount === 3) keepScore += 25;
        else if (landCount === 1 || landCount === 4) keepScore += 10;
        else if (landCount === 0 || landCount >= 5) keepScore -= 20;

        // Early plays
        if (hasEarlyPlay) keepScore += 15;

        // Mid game
        if (hasMidGame) keepScore += 10;

        // Curve considerations
        if (averageCmc <= 3) keepScore += 5;
        else if (averageCmc >= 5) keepScore -= 10;

        keepScore = Math.max(0, Math.min(100, keepScore));

        const suggestions: string[] = [];
        if (landCount === 0) suggestions.push("No lands - consider mulliganing");
        if (landCount >= 5) suggestions.push("Land-heavy hand - consider mulliganing");
        if (!hasEarlyPlay && landCount >= 2)
          suggestions.push("No early plays - may be slow to start");
        if (landCount >= 2 && landCount <= 4 && hasEarlyPlay)
          suggestions.push("Good curve and land count - likely a keep");

        result = {
          keepScore,
          landCount,
          nonLandCount,
          averageCmc,
          hasEarlyPlay,
          hasMidGame,
          colorCoverage,
          suggestions,
        };
      });
      unsubscribe();
      return result;
    },
  };
}

export const gameStore = createGameStore();

// Derived stores for convenience
export const currentGame = derived(gameStore, ($store) => $store.game);
export const currentPlayer = derived(gameStore, ($store) => $store.game?.player);
export const selectedGameCard = derived(
  gameStore,
  ($store) => $store.selectedCard
);
export const isGameStarted = derived(
  gameStore,
  ($store) => $store.game?.started ?? false
);
