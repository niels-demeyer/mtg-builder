/**
 * Multiplayer Game Store
 *
 * Manages multiplayer game state received from the server via WebSocket.
 * Sends actions to the server instead of mutating state locally.
 * Provides derived stores compatible with existing game components.
 */

import { writable, derived } from "svelte/store";
import {
  GameWSClient,
  type ConnectionStatus,
  type ServerMessage,
} from "$lib/wsClient";
import type {
  GameCard,
  GameZone,
  GamePhase,
  PlayerState,
  ManaPool,
  GameAction,
  MultiplayerGameState,
  MultiplayerStoreState,
  LobbyPlayer,
  GameBoardActions,
  GameBoardInfo,
} from "$lib/types";
import type { ManaColor } from "./gameStore";

const initialState: MultiplayerStoreState = {
  connectionStatus: "disconnected",
  gameCode: null,
  lobbyPlayers: [],
  isHost: false,
  game: null,
  myPlayerId: null,
  selectedCard: null,
  error: null,
  actionError: null,
};

function createMultiplayerStore() {
  const { subscribe, update, set } = writable<MultiplayerStoreState>(initialState);

  let wsClient: GameWSClient | null = null;
  let actionErrorTimeout: ReturnType<typeof setTimeout> | null = null;

  function clearActionError() {
    if (actionErrorTimeout) {
      clearTimeout(actionErrorTimeout);
    }
  }

  function setActionError(msg: string) {
    clearActionError();
    update((s) => ({ ...s, actionError: msg }));
    actionErrorTimeout = setTimeout(() => {
      update((s) => ({ ...s, actionError: null }));
    }, 3000);
  }

  function handleServerMessage(message: ServerMessage): void {
    const msgType = message.type;

    switch (msgType) {
      case "game_created":
        update((s) => ({
          ...s,
          gameCode: message.game_code,
          isHost: true,
          game: message.game_state,
          error: null,
        }));
        break;

      case "player_joined":
        update((s) => ({
          ...s,
          lobbyPlayers: message.players as LobbyPlayer[],
        }));
        break;

      case "player_left":
        update((s) => ({
          ...s,
          lobbyPlayers: message.players as LobbyPlayer[],
        }));
        break;

      case "game_state_update":
        update((s) => {
          const game = message.game_state as MultiplayerGameState;
          // Update lobby players from game state
          const lobbyPlayers: LobbyPlayer[] = game.players.map((p: any) => ({
            id: p.id,
            username: p.name,
            deck_name: "",
            ready: false,
          }));
          return {
            ...s,
            game,
            lobbyPlayers: s.game?.started ? s.lobbyPlayers : lobbyPlayers,
            gameCode: s.gameCode || game.game_code,
            error: null,
          };
        });
        break;

      case "action_rejected":
        setActionError(message.reason || "Action rejected");
        break;

      case "game_over":
        update((s) => ({
          ...s,
          error: `Game over: ${message.reason || ""}`,
        }));
        break;

      case "left_game":
        update((s) => ({
          ...s,
          gameCode: null,
          lobbyPlayers: [],
          isHost: false,
          game: null,
        }));
        break;

      case "error":
        update((s) => ({ ...s, error: message.message }));
        break;
    }
  }

  return {
    subscribe,

    connect(token: string, userId: string): void {
      if (wsClient) {
        wsClient.disconnect();
      }

      update((s) => ({
        ...s,
        myPlayerId: userId,
        connectionStatus: "connecting",
      }));

      wsClient = new GameWSClient({
        onMessage: handleServerMessage,
        onStatusChange: (status: ConnectionStatus) => {
          update((s) => ({ ...s, connectionStatus: status }));
        },
        onError: (error: string) => {
          update((s) => ({ ...s, error }));
        },
      });

      wsClient.connect(token);
    },

    createGame(deckId: string, maxPlayers: number = 4): void {
      wsClient?.send({
        type: "create_game",
        deck_id: deckId,
        max_players: maxPlayers,
      });
    },

    joinGame(gameCode: string, deckId: string): void {
      wsClient?.send({
        type: "join_game",
        game_code: gameCode,
        deck_id: deckId,
      });
    },

    leaveGame(): void {
      wsClient?.send({ type: "leave_game" });
    },

    // Game actions (all send to server)
    drawCard(): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "draw_card" },
      });
    },

    drawOpeningHand(): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "draw_opening_hand" },
      });
    },

    playCard(instanceId: string): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "play_card", instance_id: instanceId },
      });
    },

    moveCard(instanceId: string, toZone: GameZone): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "move_card", instance_id: instanceId, to_zone: toZone },
      });
    },

    discardCard(instanceId: string): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "discard_card", instance_id: instanceId },
      });
    },

    toggleTap(instanceId: string): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "tap_card", instance_id: instanceId },
      });
    },

    tapForMana(instanceId: string, color: ManaColor): void {
      wsClient?.send({
        type: "game_action",
        action: {
          action: "tap_for_mana",
          instance_id: instanceId,
          color,
        },
      });
    },

    untapAll(): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "untap_all" },
      });
    },

    nextTurn(): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "next_turn" },
      });
    },

    setPhase(phase: GamePhase): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "set_phase", phase },
      });
    },

    updateLife(change: number): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "update_life", change },
      });
    },

    addMana(color: ManaColor, amount: number = 1): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "add_mana", color, amount },
      });
    },

    removeMana(color: ManaColor, amount: number = 1): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "remove_mana", color, amount },
      });
    },

    clearManaPool(): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "clear_mana_pool" },
      });
    },

    shuffleLibrary(): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "shuffle_library" },
      });
    },

    mill(count: number): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "mill", count },
      });
    },

    addCounter(instanceId: string, counterType: string): void {
      wsClient?.send({
        type: "game_action",
        action: {
          action: "add_counter",
          instance_id: instanceId,
          counter_type: counterType,
        },
      });
    },

    removeCounter(instanceId: string, counterType: string): void {
      wsClient?.send({
        type: "game_action",
        action: {
          action: "remove_counter",
          instance_id: instanceId,
          counter_type: counterType,
        },
      });
    },

    mulligan(): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "mulligan" },
      });
    },

    keepHand(): void {
      wsClient?.send({
        type: "game_action",
        action: { action: "keep_hand" },
      });
    },

    selectCard(card: GameCard | null): void {
      update((s) => ({ ...s, selectedCard: card }));
    },

    disconnect(): void {
      clearActionError();
      wsClient?.disconnect();
      wsClient = null;
      set(initialState);
    },

    /**
     * Build a GameBoardActions adapter from this store's methods.
     * Used to pass into GameBoard.svelte for multiplayer mode.
     */
    getActions(): GameBoardActions {
      return {
        drawCard: () => this.drawCard(),
        moveCard: (id: string, zone: GameZone) => this.moveCard(id, zone),
        playCard: (id: string) => this.playCard(id),
        toggleTap: (id: string) => this.toggleTap(id),
        tapForMana: (id: string, color: string) =>
          this.tapForMana(id, color as ManaColor),
        untapAll: () => this.untapAll(),
        nextTurn: () => this.nextTurn(),
        setPhase: (phase: GamePhase) => this.setPhase(phase),
        updateLife: (change: number) => this.updateLife(change),
        addCounter: (id: string, type: string) => this.addCounter(id, type),
        removeCounter: (id: string, type: string) => this.removeCounter(id, type),
        shuffleLibrary: () => this.shuffleLibrary(),
        mill: (count: number) => this.mill(count),
        discardCard: (id: string) => this.discardCard(id),
        addMana: (color: string, amount?: number) =>
          this.addMana(color as ManaColor, amount),
        removeMana: (color: string, amount?: number) =>
          this.removeMana(color as ManaColor, amount),
        clearManaPool: () => this.clearManaPool(),
        selectCard: (card: GameCard | null) => this.selectCard(card),
      };
    },
  };
}

export const multiplayerStore = createMultiplayerStore();

// Derived stores for component consumption
export const mpGame = derived(multiplayerStore, ($s) => $s.game);
export const mpConnectionStatus = derived(
  multiplayerStore,
  ($s) => $s.connectionStatus
);
export const mpGameCode = derived(multiplayerStore, ($s) => $s.gameCode);
export const mpLobbyPlayers = derived(
  multiplayerStore,
  ($s) => $s.lobbyPlayers
);
export const mpActionError = derived(
  multiplayerStore,
  ($s) => $s.actionError
);

export const mpMyPlayer = derived(multiplayerStore, ($s): PlayerState | null => {
  if (!$s.game || !$s.myPlayerId) return null;
  return $s.game.players.find((p) => p.id === $s.myPlayerId) ?? null;
});

export const mpOpponents = derived(
  multiplayerStore,
  ($s): PlayerState[] => {
    if (!$s.game || !$s.myPlayerId) return [];
    return $s.game.players.filter((p) => p.id !== $s.myPlayerId);
  }
);

export const mpIsMyTurn = derived(multiplayerStore, ($s): boolean => {
  if (!$s.game || !$s.myPlayerId) return false;
  return $s.game.active_player_id === $s.myPlayerId;
});
