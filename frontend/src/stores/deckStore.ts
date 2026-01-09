import { writable, derived } from "svelte/store";
import type {
  Deck,
  DeckStoreState,
  CardInDeck,
  DeckUpdates,
  ScryfallCard,
  DeckFolder,
  CardZone,
  DisplayMode,
  PileSortBy,
  DeckStats,
  DeckFormat,
} from "$lib/types";

// Helper function to calculate deck statistics
function calculateDeckStats(cards: CardInDeck[]): DeckStats {
  const mainboardCards = cards.filter(
    (c) => c.zone === "mainboard" || c.zone === "commander"
  );
  const sideboardCards = cards.filter((c) => c.zone === "sideboard");
  const maybeboardCards = cards.filter((c) => c.zone === "maybeboard");
  const consideringCards = cards.filter((c) => c.zone === "considering");

  const manaCurve: Record<number, number> = {};
  const colorDistribution: Record<string, number> = {
    W: 0,
    U: 0,
    B: 0,
    R: 0,
    G: 0,
    C: 0,
  };
  const typeDistribution: Record<string, number> = {};

  let totalCmc = 0;
  let landCount = 0;
  let creatureCount = 0;
  let spellCount = 0;

  mainboardCards.forEach((card) => {
    // Mana curve (exclude lands)
    if (!card.type_line.toLowerCase().includes("land")) {
      const cmcBucket = Math.min(card.cmc, 7); // Group 7+ together
      manaCurve[cmcBucket] = (manaCurve[cmcBucket] || 0) + card.quantity;
      totalCmc += card.cmc * card.quantity;
    }

    // Color distribution
    if (card.colors && card.colors.length > 0) {
      card.colors.forEach((color) => {
        colorDistribution[color] =
          (colorDistribution[color] || 0) + card.quantity;
      });
    } else if (!card.type_line.toLowerCase().includes("land")) {
      colorDistribution["C"] = (colorDistribution["C"] || 0) + card.quantity;
    }

    // Type distribution
    const mainType =
      card.type_line.split("—")[0].trim().split(" ").pop() || "Other";
    typeDistribution[mainType] =
      (typeDistribution[mainType] || 0) + card.quantity;

    // Count by type
    const typeLower = card.type_line.toLowerCase();
    if (typeLower.includes("land")) {
      landCount += card.quantity;
    } else if (typeLower.includes("creature")) {
      creatureCount += card.quantity;
    } else {
      spellCount += card.quantity;
    }
  });

  const mainboardCount = mainboardCards.reduce((sum, c) => sum + c.quantity, 0);
  const nonLandCount = mainboardCount - landCount;

  return {
    totalCards: cards.reduce((sum, c) => sum + c.quantity, 0),
    mainboardCount,
    sideboardCount: sideboardCards.reduce((sum, c) => sum + c.quantity, 0),
    maybeboardCount: maybeboardCards.reduce((sum, c) => sum + c.quantity, 0),
    consideringCount: consideringCards.reduce((sum, c) => sum + c.quantity, 0),
    manaCurve,
    colorDistribution,
    typeDistribution,
    averageCmc: nonLandCount > 0 ? totalCmc / nonLandCount : 0,
    landCount,
    creatureCount,
    spellCount,
  };
}

function createDeckStore() {
  const initialState: DeckStoreState = {
    decks: [],
    folders: [],
    currentDeck: null,
    displayMode: "list",
    pileSortBy: "cmc",
    selectedZone: "mainboard",
    loading: false,
    error: null,
  };

  const { subscribe, update, set } = writable<DeckStoreState>(initialState);

  // Migrate old deck format to new format
  function migrateDeck(deck: Deck): Deck {
    const migratedCards = deck.cards.map((card) => ({
      ...card,
      zone: card.zone || ("mainboard" as CardZone),
      tags: card.tags || [],
    }));
    return {
      ...deck,
      format: (deck.format || "Standard") as DeckFormat,
      cards: migratedCards,
    };
  }

  return {
    subscribe,

    // Load decks and folders from localStorage
    loadDecks: (): void => {
      const savedDecks = localStorage.getItem("mtg-decks");
      const savedFolders = localStorage.getItem("mtg-folders");

      let decks: Deck[] = [];
      let folders: DeckFolder[] = [];

      if (savedDecks) {
        const parsed = JSON.parse(savedDecks) as Deck[];
        decks = parsed.map(migrateDeck);
      }

      if (savedFolders) {
        folders = JSON.parse(savedFolders) as DeckFolder[];
      }

      update((state) => ({ ...state, decks, folders }));
    },

    // Save decks to localStorage
    saveToStorage: (decks: Deck[]): void => {
      localStorage.setItem("mtg-decks", JSON.stringify(decks));
    },

    // Save folders to localStorage
    saveFoldersToStorage: (folders: DeckFolder[]): void => {
      localStorage.setItem("mtg-folders", JSON.stringify(folders));
    },

    // Create a new folder
    createFolder: (
      name: string,
      color?: string,
      parentId?: string
    ): DeckFolder => {
      const newFolder: DeckFolder = {
        id: crypto.randomUUID(),
        name,
        color,
        parentId,
        order: 0,
      };

      update((state) => {
        const folders = [...state.folders, newFolder];
        localStorage.setItem("mtg-folders", JSON.stringify(folders));
        return { ...state, folders };
      });

      return newFolder;
    },

    // Delete a folder
    deleteFolder: (folderId: string): void => {
      update((state) => {
        const folders = state.folders.filter((f) => f.id !== folderId);
        // Remove folder reference from decks
        const decks = state.decks.map((d) =>
          d.folderId === folderId ? { ...d, folderId: undefined } : d
        );
        localStorage.setItem("mtg-folders", JSON.stringify(folders));
        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return { ...state, folders, decks };
      });
    },

    // Set display mode
    setDisplayMode: (mode: DisplayMode): void => {
      update((state) => ({ ...state, displayMode: mode }));
    },

    // Set pile sort
    setPileSortBy: (sortBy: PileSortBy): void => {
      update((state) => ({ ...state, pileSortBy: sortBy }));
    },

    // Set selected zone
    setSelectedZone: (zone: CardZone): void => {
      update((state) => ({ ...state, selectedZone: zone }));
    },

    // Create a new deck
    createDeck: (
      name: string,
      format: DeckFormat = "Standard",
      description: string = "",
      folderId?: string
    ): Deck => {
      const newDeck: Deck = {
        id: crypto.randomUUID(),
        name,
        format,
        description,
        cards: [],
        folderId,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      update((state) => {
        const decks = [...state.decks, newDeck];
        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return { ...state, decks, currentDeck: newDeck };
      });

      return newDeck;
    },

    // Select a deck for editing
    selectDeck: (deckId: string): void => {
      update((state) => {
        const deck = state.decks.find((d) => d.id === deckId);
        return { ...state, currentDeck: deck || null };
      });
    },

    // Update current deck
    updateDeck: (updates: DeckUpdates): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const updatedDeck: Deck = {
          ...state.currentDeck,
          ...updates,
          updatedAt: new Date().toISOString(),
        };

        const decks = state.decks.map((d) =>
          d.id === updatedDeck.id ? updatedDeck : d
        );

        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return { ...state, decks, currentDeck: updatedDeck };
      });
    },

    // Add card to current deck
    addCard: (
      card: Omit<CardInDeck, "quantity" | "zone" | "tags">,
      quantity: number = 1,
      zone: CardZone = "mainboard",
      tags: string[] = []
    ): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const existingIndex = state.currentDeck.cards.findIndex(
          (c) => c.id === card.id && c.zone === zone
        );
        let cards: CardInDeck[];

        if (existingIndex >= 0) {
          cards = state.currentDeck.cards.map((c, i) =>
            i === existingIndex ? { ...c, quantity: c.quantity + quantity } : c
          );
        } else {
          cards = [
            ...state.currentDeck.cards,
            { ...card, quantity, zone, tags },
          ];
        }

        const updatedDeck: Deck = {
          ...state.currentDeck,
          cards,
          updatedAt: new Date().toISOString(),
        };

        const decks = state.decks.map((d) =>
          d.id === updatedDeck.id ? updatedDeck : d
        );

        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return { ...state, decks, currentDeck: updatedDeck };
      });
    },

    // Move card between zones
    moveCardToZone: (
      cardId: string,
      fromZone: CardZone,
      toZone: CardZone
    ): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const cards = state.currentDeck.cards.map((c) =>
          c.id === cardId && c.zone === fromZone ? { ...c, zone: toZone } : c
        );

        const updatedDeck: Deck = {
          ...state.currentDeck,
          cards,
          updatedAt: new Date().toISOString(),
        };

        const decks = state.decks.map((d) =>
          d.id === updatedDeck.id ? updatedDeck : d
        );

        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return { ...state, decks, currentDeck: updatedDeck };
      });
    },

    // Update card tags
    updateCardTags: (cardId: string, tags: string[]): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const cards = state.currentDeck.cards.map((c) =>
          c.id === cardId ? { ...c, tags } : c
        );

        const updatedDeck: Deck = {
          ...state.currentDeck,
          cards,
          updatedAt: new Date().toISOString(),
        };

        const decks = state.decks.map((d) =>
          d.id === updatedDeck.id ? updatedDeck : d
        );

        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return { ...state, decks, currentDeck: updatedDeck };
      });
    },

    // Set commander
    setCommander: (cardId: string, isCommander: boolean): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const cards = state.currentDeck.cards.map((c) => ({
          ...c,
          isCommander:
            c.id === cardId ? isCommander : isCommander ? false : c.isCommander,
          zone:
            c.id === cardId && isCommander ? ("commander" as CardZone) : c.zone,
        }));

        const updatedDeck: Deck = {
          ...state.currentDeck,
          cards,
          updatedAt: new Date().toISOString(),
        };

        const decks = state.decks.map((d) =>
          d.id === updatedDeck.id ? updatedDeck : d
        );

        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return { ...state, decks, currentDeck: updatedDeck };
      });
    },

    // Remove card from current deck
    removeCard: (cardId: string, zone?: CardZone): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const cards = zone
          ? state.currentDeck.cards.filter(
              (c) => !(c.id === cardId && c.zone === zone)
            )
          : state.currentDeck.cards.filter((c) => c.id !== cardId);

        const updatedDeck: Deck = {
          ...state.currentDeck,
          cards,
          updatedAt: new Date().toISOString(),
        };

        const decks = state.decks.map((d) =>
          d.id === updatedDeck.id ? updatedDeck : d
        );

        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return { ...state, decks, currentDeck: updatedDeck };
      });
    },

    // Update card quantity
    updateCardQuantity: (
      cardId: string,
      quantity: number,
      zone?: CardZone
    ): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const cards =
          quantity <= 0
            ? state.currentDeck.cards.filter((c) =>
                zone ? !(c.id === cardId && c.zone === zone) : c.id !== cardId
              )
            : state.currentDeck.cards.map((c) =>
                (zone ? c.id === cardId && c.zone === zone : c.id === cardId)
                  ? { ...c, quantity }
                  : c
              );

        const updatedDeck: Deck = {
          ...state.currentDeck,
          cards,
          updatedAt: new Date().toISOString(),
        };

        const decks = state.decks.map((d) =>
          d.id === updatedDeck.id ? updatedDeck : d
        );

        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return { ...state, decks, currentDeck: updatedDeck };
      });
    },

    // Delete a deck
    deleteDeck: (deckId: string): void => {
      update((state) => {
        const decks = state.decks.filter((d) => d.id !== deckId);
        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        return {
          ...state,
          decks,
          currentDeck:
            state.currentDeck?.id === deckId ? null : state.currentDeck,
        };
      });
    },

    // Clear current deck selection
    clearCurrentDeck: (): void => {
      update((state) => ({ ...state, currentDeck: null }));
    },

    // Get deck statistics
    getDeckStats: (deck: Deck): DeckStats => {
      return calculateDeckStats(deck.cards);
    },
  };
}

export const deckStore = createDeckStore();

// Derived store for current deck stats
export const currentDeckStats = derived(deckStore, ($store) =>
  $store.currentDeck ? calculateDeckStats($store.currentDeck.cards) : null
);
