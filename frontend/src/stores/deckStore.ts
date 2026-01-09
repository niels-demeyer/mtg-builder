import { writable } from "svelte/store";
import type {
  Deck,
  DeckStoreState,
  CardInDeck,
  DeckUpdates,
  ScryfallCard,
} from "$lib/types";

function createDeckStore() {
  const initialState: DeckStoreState = {
    decks: [],
    currentDeck: null,
    loading: false,
    error: null,
  };

  const { subscribe, update } = writable<DeckStoreState>(initialState);

  return {
    subscribe,

    // Load decks from localStorage
    loadDecks: (): void => {
      const saved = localStorage.getItem("mtg-decks");
      if (saved) {
        update((state) => ({ ...state, decks: JSON.parse(saved) as Deck[] }));
      }
    },

    // Save decks to localStorage
    saveToStorage: (decks: Deck[]): void => {
      localStorage.setItem("mtg-decks", JSON.stringify(decks));
    },

    // Create a new deck
    createDeck: (
      name: string,
      format: string = "Standard",
      description: string = ""
    ): Deck => {
      const newDeck: Deck = {
        id: crypto.randomUUID(),
        name,
        format,
        description,
        cards: [],
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
      card: Omit<CardInDeck, "quantity">,
      quantity: number = 1
    ): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const existingIndex = state.currentDeck.cards.findIndex(
          (c) => c.id === card.id
        );
        let cards: CardInDeck[];

        if (existingIndex >= 0) {
          cards = state.currentDeck.cards.map((c, i) =>
            i === existingIndex ? { ...c, quantity: c.quantity + quantity } : c
          );
        } else {
          cards = [...state.currentDeck.cards, { ...card, quantity }];
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

    // Remove card from current deck
    removeCard: (cardId: string): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const cards = state.currentDeck.cards.filter((c) => c.id !== cardId);

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
    updateCardQuantity: (cardId: string, quantity: number): void => {
      update((state) => {
        if (!state.currentDeck) return state;

        const cards =
          quantity <= 0
            ? state.currentDeck.cards.filter((c) => c.id !== cardId)
            : state.currentDeck.cards.map((c) =>
                c.id === cardId ? { ...c, quantity } : c
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
  };
}

export const deckStore = createDeckStore();
