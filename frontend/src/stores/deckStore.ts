import { writable, derived } from "svelte/store";
import type {
  Deck,
  DeckStoreState,
  CardInDeck,
  DeckUpdates,
  DeckFolder,
  CardZone,
  DisplayMode,
  PileSortBy,
  DeckStats,
  DeckFormat,
  CardFace,
} from "$lib/types";
import { apiFetch, API_BASE } from "$lib/api";
import {
  type FixType,
  fixSingletonDuplicates,
  fix4ofDuplicates,
  fixSideboardSize,
  fixMoveCommanderToMainboard,
} from "$lib/deckValidation";

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

// Check if user is authenticated
function isAuthenticated(): boolean {
  return !!localStorage.getItem("auth-token");
}

// Pending save state
let pendingSave: { deckId: string; cards: CardInDeck[] } | null = null;
let saveTimeout: ReturnType<typeof setTimeout> | null = null;

// Immediately save to backend
async function saveToBackend(deckId: string, cards: CardInDeck[]): Promise<void> {
  if (!isAuthenticated()) return;
  try {
    const response = await apiFetch(`/decks/${deckId}`, {
      method: "PUT",
      body: JSON.stringify({ cards }),
    });
    if (!response.ok) {
      console.error("Failed to save deck:", await response.text());
    } else {
      pendingSave = null;
    }
  } catch (e) {
    console.error("Failed to save deck to backend:", e);
  }
}

// Debounce helper for saving to backend
function debouncedSave(deckId: string, cards: CardInDeck[]): void {
  pendingSave = { deckId, cards };
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }
  saveTimeout = setTimeout(() => {
    saveToBackend(deckId, cards);
  }, 1000); // Save after 1 second of inactivity
}

// Flush pending saves (call on page unload)
export function flushPendingSave(): void {
  if (saveTimeout) {
    clearTimeout(saveTimeout);
    saveTimeout = null;
  }
  if (pendingSave && isAuthenticated()) {
    // Use sendBeacon for reliable delivery on page unload
    const token = localStorage.getItem("auth-token");
    const url = `${API_BASE}/decks/${pendingSave.deckId}`;
    const data = JSON.stringify({ cards: pendingSave.cards });

    // sendBeacon doesn't support custom headers, so we fall back to sync XHR
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url, false); // synchronous
    xhr.setRequestHeader("Content-Type", "application/json");
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }
    try {
      xhr.send(data);
    } catch (e) {
      console.error("Failed to flush save:", e);
    }
    pendingSave = null;
  }
}

// Register beforeunload handler
if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", flushPendingSave);
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

  // Convert backend deck response to frontend Deck type
  function fromBackendDeck(backendDeck: {
    id: string;
    name: string;
    format?: string;
    description?: string | null;
    cards?: Array<{
      id: string;
      name: string;
      mana_cost?: string | null;
      cmc?: number;
      type_line?: string;
      colors?: string[] | null;
      rarity?: string;
      image_uri?: string | null;
      card_faces?: CardFace[];
      quantity?: number;
      zone?: string;
      tags?: string[];
      isCommander?: boolean;
    }>;
    createdAt?: string | null;
    updatedAt?: string | null;
  }): Deck {
    return {
      id: backendDeck.id,
      name: backendDeck.name,
      format: (backendDeck.format || "Standard") as DeckFormat,
      description: backendDeck.description || "",
      cards: (backendDeck.cards || []).map((card) => ({
        id: card.id,
        name: card.name,
        mana_cost: card.mana_cost || undefined,
        cmc: card.cmc || 0,
        type_line: card.type_line || "",
        colors: card.colors || undefined,
        rarity: card.rarity || "common",
        image_uri: card.image_uri || undefined,
        card_faces: card.card_faces,
        quantity: card.quantity || 1,
        zone: (card.zone || "mainboard") as CardZone,
        tags: card.tags || [],
        isCommander: card.isCommander || false,
      })),
      createdAt: backendDeck.createdAt || new Date().toISOString(),
      updatedAt: backendDeck.updatedAt || new Date().toISOString(),
    };
  }

  return {
    subscribe,

    // Load decks from backend (if authenticated) or localStorage
    loadDecks: async (): Promise<void> => {
      update((state) => ({ ...state, loading: true, error: null }));

      // Always load folders from localStorage (not stored in backend yet)
      const savedFolders = localStorage.getItem("mtg-folders");
      let folders: DeckFolder[] = [];
      if (savedFolders) {
        folders = JSON.parse(savedFolders) as DeckFolder[];
      }

      if (isAuthenticated()) {
        try {
          const response = await apiFetch("/decks");
          if (response.ok) {
            const backendDecks = await response.json();
            const decks = backendDecks.map(fromBackendDeck);
            update((state) => ({ ...state, decks, folders, loading: false }));
            return;
          }
        } catch (e) {
          console.error("Failed to load decks from backend:", e);
        }
      }

      // Fallback to localStorage
      const savedDecks = localStorage.getItem("mtg-decks");
      let decks: Deck[] = [];
      if (savedDecks) {
        const parsed = JSON.parse(savedDecks) as Deck[];
        decks = parsed.map(migrateDeck);
      }

      update((state) => ({ ...state, decks, folders, loading: false }));
    },

    // Save decks to localStorage (backup)
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
    createDeck: async (
      name: string,
      format: DeckFormat = "Standard",
      description: string = "",
      folderId?: string
    ): Promise<Deck> => {
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

      if (isAuthenticated()) {
        try {
          const response = await apiFetch("/decks", {
            method: "POST",
            body: JSON.stringify({
              name,
              format,
              description,
              cards: [],
            }),
          });
          if (response.ok) {
            const backendDeck = await response.json();
            const deck = fromBackendDeck(backendDeck);
            deck.folderId = folderId; // Keep folder info locally

            update((state) => {
              const decks = [...state.decks, deck];
              localStorage.setItem("mtg-decks", JSON.stringify(decks));
              return { ...state, decks, currentDeck: deck };
            });

            return deck;
          }
        } catch (e) {
          console.error("Failed to create deck on backend:", e);
        }
      }

      // Fallback to local storage
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

        // Sync with backend
        if (isAuthenticated()) {
          apiFetch(`/decks/${updatedDeck.id}`, {
            method: "PUT",
            body: JSON.stringify({
              name: updates.name,
              format: updates.format,
              description: updates.description,
              cards: updates.cards,
            }),
          }).catch((e) => console.error("Failed to update deck on backend:", e));
        }

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

        // Debounced sync with backend
        debouncedSave(updatedDeck.id, cards);

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
        debouncedSave(updatedDeck.id, cards);

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
        debouncedSave(updatedDeck.id, cards);

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
        debouncedSave(updatedDeck.id, cards);

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
        debouncedSave(updatedDeck.id, cards);

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
        debouncedSave(updatedDeck.id, cards);

        return { ...state, decks, currentDeck: updatedDeck };
      });
    },

    // Delete a deck
    deleteDeck: async (deckId: string): Promise<void> => {
      if (isAuthenticated()) {
        try {
          await apiFetch(`/decks/${deckId}`, {
            method: "DELETE",
          });
        } catch (e) {
          console.error("Failed to delete deck on backend:", e);
        }
      }

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

    // Apply a validation fix to the current deck
    applyValidationFix: (fixType: FixType): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        let fixedCards: CardInDeck[];

        switch (fixType) {
          case "remove_duplicates_singleton":
            fixedCards = fixSingletonDuplicates(state.currentDeck.cards);
            break;
          case "remove_duplicates_4of":
            fixedCards = fix4ofDuplicates(state.currentDeck.cards);
            break;
          case "trim_sideboard":
            fixedCards = fixSideboardSize(state.currentDeck.cards);
            break;
          case "move_to_mainboard":
            fixedCards = fixMoveCommanderToMainboard(state.currentDeck.cards);
            break;
          default:
            return state;
        }

        const updatedDeck: Deck = {
          ...state.currentDeck,
          cards: fixedCards,
          updatedAt: new Date().toISOString(),
        };

        const decks = state.decks.map((d) =>
          d.id === updatedDeck.id ? updatedDeck : d
        );

        localStorage.setItem("mtg-decks", JSON.stringify(decks));
        debouncedSave(updatedDeck.id, fixedCards);

        return { ...state, decks, currentDeck: updatedDeck };
      });
    },
  };
}

export const deckStore = createDeckStore();

// Derived store for current deck stats
export const currentDeckStats = derived(deckStore, ($store) =>
  $store.currentDeck ? calculateDeckStats($store.currentDeck.cards) : null
);
