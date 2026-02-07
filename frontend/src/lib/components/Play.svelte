<script lang="ts">
  import CommanderLobby from './game/CommanderLobby.svelte';
  import MultiplayerGameBoard from './game/MultiplayerGameBoard.svelte';
  import { multiplayerStore, mpGame } from '../../stores/multiplayerStore';

  type PlayState = 'lobby' | 'playing';
  let playState = $state<PlayState>('lobby');

  let game = $derived($mpGame);

  // Watch for game starting
  $effect(() => {
    if (game?.started && playState === 'lobby') {
      playState = 'playing';
    }
  });

  function handleGameReady() {
    playState = 'playing';
  }

  function handleExit() {
    multiplayerStore.disconnect();
    playState = 'lobby';
  }
</script>

<div class="play-page" class:fullscreen={playState === 'playing'}>
  {#if playState === 'lobby'}
    <CommanderLobby onGameReady={handleGameReady} />
  {:else if playState === 'playing'}
    <div class="game-wrapper">
      <header class="game-header-bar">
        <button class="exit-btn" onclick={handleExit}>&larr; Exit Game</button>
        <span class="game-title">
          Commander Game
          {#if game?.game_code}
            <span class="code-badge">{game.game_code}</span>
          {/if}
        </span>
      </header>
      <div class="game-area">
        <MultiplayerGameBoard showControls={true} showPhases={true} />
      </div>
    </div>
  {/if}
</div>

<style>
  .play-page {
    padding: 2rem;
    max-width: 1000px;
    margin: 0 auto;
  }

  .play-page.fullscreen {
    padding: 0;
    max-width: none;
    height: 100vh;
    width: 100vw;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 50;
    background: hsl(var(--background));
    overflow: hidden;
  }

  .game-wrapper {
    height: 100vh;
    width: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .game-header-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem 1rem;
    background: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
    flex-shrink: 0;
  }

  .exit-btn {
    padding: 0.375rem 0.75rem;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.8rem;
    color: hsl(var(--muted-foreground));
    transition: all 0.15s;
  }

  .exit-btn:hover {
    background: hsl(var(--destructive));
    color: white;
    border-color: hsl(var(--destructive));
  }

  .game-title {
    font-weight: 600;
    color: hsl(var(--foreground));
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .code-badge {
    padding: 0.125rem 0.5rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-family: monospace;
    color: hsl(var(--muted-foreground));
  }

  .game-area {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
</style>
