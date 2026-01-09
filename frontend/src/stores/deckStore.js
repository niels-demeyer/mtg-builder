import { writable } from "svelte/store";

function createDeckStore() {
  const { subscribe, set, update } = writable({
    decks: [],
    currentDeck: null,
    loading: false,
    error: null,
  });

  return {
    subscribe,

    // Load decks from localStorage
    loadDecks: () => {
      const saved = localStorage.getItem("mtg-decks");
      if (saved) {
        update((state) => ({ ...state, decks: JSON.parse(saved) }));
      }
    },

    // Save decks to localStorage
    saveToStorage: (decks) => {
      localStorage.setItem("mtg-decks", JSON.stringify(decks));
    },

    // Create a new deck
    createDeck: (name, format = "Standard", description = "") => {
      const newDeck = {
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
    selectDeck: (deckId) => {
      update((state) => {
        const deck = state.decks.find((d) => d.id === deckId);
        return { ...state, currentDeck: deck || null };
      });
    },

    // Update current deck
    updateDeck: (updates) => {
      update((state) => {
        if (!state.currentDeck) return state;

        const updatedDeck = {
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
    addCard: (card, quantity = 1) => {
      update((state) => {
        if (!state.currentDeck) return state;

        const existingIndex = state.currentDeck.cards.findIndex(
          (c) => c.id === card.id
        );
        let cards;

        if (existingIndex >= 0) {
          cards = state.currentDeck.cards.map((c, i) =>
            i === existingIndex ? { ...c, quantity: c.quantity + quantity } : c
          );
        } else {
          cards = [...state.currentDeck.cards, { ...card, quantity }];
        }

        const updatedDeck = {
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
    removeCard: (cardId) => {
      update((state) => {
        if (!state.currentDeck) return state;

        const cards = state.currentDeck.cards.filter((c) => c.id !== cardId);

        const updatedDeck = {
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
    updateCardQuantity: (cardId, quantity) => {
      update((state) => {
        if (!state.currentDeck) return state;

        const cards =
          quantity <= 0
            ? state.currentDeck.cards.filter((c) => c.id !== cardId)
            : state.currentDeck.cards.map((c) =>
                c.id === cardId ? { ...c, quantity } : c
              );

        const updatedDeck = {
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
    deleteDeck: (deckId) => {
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
    clearCurrentDeck: () => {
      update((state) => ({ ...state, currentDeck: null }));
    },
  };
}

export const deckStore = createDeckStore();
