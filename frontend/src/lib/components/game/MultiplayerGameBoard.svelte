<script lang="ts">
  import type { GameCard, PlayerState, GameBoardInfo } from "$lib/types";
  import {
    multiplayerStore,
    mpGame,
    mpMyPlayer,
    mpOpponents,
    mpIsMyTurn,
    mpActionError,
  } from "../../../stores/multiplayerStore";
  import GameBoard from "./GameBoard.svelte";
  import OpponentBoard from "./OpponentBoard.svelte";

  interface Props {
    showControls?: boolean;
    showPhases?: boolean;
  }

  let { showControls = true, showPhases = true }: Props = $props();

  let game = $derived($mpGame);
  let myPlayer = $derived($mpMyPlayer);
  let opponents = $derived($mpOpponents);
  let isMyTurn = $derived($mpIsMyTurn);
  let actionError = $derived($mpActionError);

  // Build GameBoardInfo from multiplayer game state
  const gameInfo = $derived.by((): GameBoardInfo | undefined => {
    if (!game) return undefined;
    return {
      turnNumber: game.turn_number,
      phase: game.phase,
      deckName: myPlayer?.name ?? "Unknown",
      format: game.format,
      started: game.started,
    };
  });

  // Build the actions adapter from the multiplayer store
  const actions = $derived(multiplayerStore.getActions());

  let selectedOpponentCard = $state<GameCard | null>(null);

  function handleOpponentCardClick(card: GameCard) {
    selectedOpponentCard = card;
  }
</script>

{#if game && myPlayer}
  <div class="multiplayer-board">
    <!-- Opponent boards at the top -->
    {#if opponents.length > 0}
      <div class="opponents-row" class:two={opponents.length === 2} class:three={opponents.length === 3}>
        {#each opponents as opponent (opponent.id)}
          <OpponentBoard
            player={opponent}
            isActivePlayer={game.active_player_id === opponent.id}
            onCardClick={handleOpponentCardClick}
          />
        {/each}
      </div>
    {/if}

    <!-- Turn indicator -->
    <div class="turn-bar">
      <span class="turn-info">
        Turn {game.turn_number}
        {#if isMyTurn}
          <span class="your-turn">Your Turn</span>
        {:else}
          {@const activePlayer = game.players.find(p => p.id === game.active_player_id)}
          <span class="other-turn">{activePlayer?.name ?? 'Unknown'}'s Turn</span>
        {/if}
      </span>
      <span class="game-code-pill">Code: {game.game_code}</span>
    </div>

    <!-- Your game board -->
    <div class="my-board">
      <GameBoard
        {showControls}
        {showPhases}
        player={myPlayer}
        {gameInfo}
        {actions}
      />
    </div>

    <!-- Action error toast -->
    {#if actionError}
      <div class="action-error-toast">
        {actionError}
      </div>
    {/if}

    <!-- Opponent card preview -->
    {#if selectedOpponentCard}
      <div class="opponent-preview">
        <button class="close-preview" onclick={() => (selectedOpponentCard = null)}>&times;</button>
        <img src={selectedOpponentCard.image_uri} alt={selectedOpponentCard.name} />
        <div class="preview-name">{selectedOpponentCard.name}</div>
      </div>
    {/if}
  </div>
{:else}
  <div class="loading-state">
    <p>Waiting for game data...</p>
  </div>
{/if}

<style>
  .multiplayer-board {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }

  .opponents-row {
    display: flex;
    gap: 0.75rem;
    padding: 0.75rem;
    overflow-x: auto;
    overflow-y: auto;
    flex-shrink: 0;
    height: 30vh;
    min-height: 160px;
    max-height: 35vh;
  }

  .turn-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.375rem 1rem;
    background: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
    border-top: 1px solid hsl(var(--border));
    flex-shrink: 0;
  }

  .turn-info {
    font-size: 0.875rem;
    color: hsl(var(--foreground));
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .your-turn {
    padding: 0.125rem 0.5rem;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
  }

  .other-turn {
    padding: 0.125rem 0.5rem;
    background: hsl(var(--secondary));
    color: hsl(var(--muted-foreground));
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
  }

  .game-code-pill {
    padding: 0.125rem 0.5rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 500;
    color: hsl(var(--muted-foreground));
    font-family: monospace;
  }

  .my-board {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .action-error-toast {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    padding: 0.75rem 1.5rem;
    background: hsl(var(--destructive));
    color: white;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 400;
    animation: toastIn 0.2s ease-out;
  }

  @keyframes toastIn {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }

  .opponent-preview {
    position: fixed;
    top: 1rem;
    right: 1rem;
    width: 240px;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    z-index: 150;
    overflow: hidden;
  }

  .opponent-preview img {
    width: 100%;
    display: block;
  }

  .preview-name {
    padding: 0.5rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    text-align: center;
  }

  .close-preview {
    position: absolute;
    top: 0.25rem;
    right: 0.25rem;
    width: 24px;
    height: 24px;
    border: none;
    border-radius: 50%;
    background: hsl(var(--background) / 0.8);
    color: hsl(var(--foreground));
    font-size: 1rem;
    cursor: pointer;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-preview:hover {
    background: hsl(var(--destructive));
    color: white;
  }

  .loading-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: hsl(var(--muted-foreground));
  }
</style>
