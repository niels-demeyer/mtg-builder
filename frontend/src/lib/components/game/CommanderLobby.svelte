<script lang="ts">
  import { multiplayerStore, mpConnectionStatus, mpGameCode, mpLobbyPlayers, mpGame } from '../../../stores/multiplayerStore';
  import { deckStore } from '../../../stores/deckStore';
  import { authStore } from '../../../stores/authStore';
  import type { Deck, LobbyPlayer } from '$lib/types';

  interface Props {
    onGameReady?: () => void;
  }

  let { onGameReady }: Props = $props();

  type LobbyState = 'menu' | 'creating' | 'joining' | 'waiting';
  let lobbyState = $state<LobbyState>('menu');
  let joinCodeInput = $state('');
  let joinError = $state<string | null>(null);

  let decks = $derived($deckStore.decks);
  let connectionStatus = $derived($mpConnectionStatus);
  let gameCode = $derived($mpGameCode);
  let lobbyPlayers = $derived($mpLobbyPlayers);
  let game = $derived($mpGame);

  // Watch for game start
  $effect(() => {
    if (game?.started && onGameReady) {
      onGameReady();
    }
  });

  function connectAndCreate(deck: Deck) {
    const token = localStorage.getItem('mtg_token');
    const userId = $authStore.user?.id;
    if (!token || !userId) return;

    multiplayerStore.connect(token, userId);

    // Wait for connection then create
    const unsub = mpConnectionStatus.subscribe((status) => {
      if (status === 'connected') {
        multiplayerStore.createGame(deck.id);
        lobbyState = 'waiting';
        unsub();
      } else if (status === 'error') {
        joinError = 'Failed to connect to game server';
        unsub();
      }
    });
  }

  function connectAndJoin(deck: Deck) {
    const code = joinCodeInput.trim().toUpperCase();
    if (!code) {
      joinError = 'Enter a game code';
      return;
    }

    const token = localStorage.getItem('mtg_token');
    const userId = $authStore.user?.id;
    if (!token || !userId) return;

    multiplayerStore.connect(token, userId);

    const unsub = mpConnectionStatus.subscribe((status) => {
      if (status === 'connected') {
        multiplayerStore.joinGame(code, deck.id);
        lobbyState = 'waiting';
        unsub();
      } else if (status === 'error') {
        joinError = 'Failed to connect to game server';
        unsub();
      }
    });
  }

  function handleDrawAndReady() {
    multiplayerStore.drawOpeningHand();
    // Small delay then keep
    setTimeout(() => {
      multiplayerStore.keepHand();
    }, 100);
  }

  function handleMulligan() {
    multiplayerStore.mulligan();
  }

  function handleKeep() {
    multiplayerStore.keepHand();
  }

  function goBack() {
    if (lobbyState === 'waiting') {
      multiplayerStore.leaveGame();
    }
    lobbyState = 'menu';
    joinCodeInput = '';
    joinError = null;
  }

  function copyGameCode() {
    if (gameCode) {
      navigator.clipboard.writeText(gameCode);
    }
  }
</script>

<div class="lobby">
  {#if lobbyState === 'menu'}
    <div class="lobby-menu">
      <h1>Commander Lobby</h1>
      <p class="subtitle">Play Commander with friends</p>

      <div class="menu-buttons">
        <button class="menu-btn create" onclick={() => (lobbyState = 'creating')}>
          <span class="btn-icon">+</span>
          <span class="btn-text">Create Game</span>
          <span class="btn-desc">Host a new Commander game</span>
        </button>
        <button class="menu-btn join" onclick={() => (lobbyState = 'joining')}>
          <span class="btn-icon">&rarr;</span>
          <span class="btn-text">Join Game</span>
          <span class="btn-desc">Join with a game code</span>
        </button>
      </div>
    </div>

  {:else if lobbyState === 'creating'}
    <div class="deck-select">
      <button class="back-btn" onclick={goBack}>&larr; Back</button>
      <h2>Select Your Deck</h2>
      <p class="subtitle">Choose a Commander deck to play</p>

      {#if decks.length === 0}
        <div class="no-decks">
          <p>No decks available. Create a Commander deck first.</p>
        </div>
      {:else}
        <div class="deck-grid">
          {#each decks as deck (deck.id)}
            <button class="deck-card" onclick={() => connectAndCreate(deck)}>
              {#if deck.thumbnail}
                <img src={deck.thumbnail} alt="" class="deck-thumb" />
              {:else}
                <div class="deck-thumb-placeholder">
                  <span>{deck.name.charAt(0)}</span>
                </div>
              {/if}
              <div class="deck-info">
                <h3>{deck.name}</h3>
                <span class="format">{deck.format}</span>
                <span class="card-count">
                  {deck.cards.filter((c) => c.zone === "mainboard" || c.zone === "commander").reduce((sum, c) => sum + c.quantity, 0)} cards
                </span>
              </div>
            </button>
          {/each}
        </div>
      {/if}
    </div>

  {:else if lobbyState === 'joining'}
    <div class="join-form">
      <button class="back-btn" onclick={goBack}>&larr; Back</button>
      <h2>Join a Game</h2>
      <p class="subtitle">Enter the game code shared by the host</p>

      <div class="code-input-row">
        <input
          type="text"
          class="code-input"
          placeholder="GAME CODE"
          maxlength="6"
          bind:value={joinCodeInput}
          onkeydown={(e) => e.key === 'Enter' && (lobbyState = 'joining')}
        />
      </div>

      {#if joinError}
        <p class="error-text">{joinError}</p>
      {/if}

      <h3>Select Your Deck</h3>
      <div class="deck-grid">
        {#each decks as deck (deck.id)}
          <button class="deck-card" onclick={() => connectAndJoin(deck)}>
            {#if deck.thumbnail}
              <img src={deck.thumbnail} alt="" class="deck-thumb" />
            {:else}
              <div class="deck-thumb-placeholder">
                <span>{deck.name.charAt(0)}</span>
              </div>
            {/if}
            <div class="deck-info">
              <h3>{deck.name}</h3>
              <span class="format">{deck.format}</span>
            </div>
          </button>
        {/each}
      </div>
    </div>

  {:else if lobbyState === 'waiting'}
    <div class="waiting-room">
      <button class="back-btn" onclick={goBack}>&larr; Leave Game</button>

      <h2>Waiting for Players</h2>

      {#if gameCode}
        <div class="game-code-display">
          <span class="code-label">Game Code</span>
          <div class="code-value-row">
            <span class="code-value">{gameCode}</span>
            <button class="copy-btn" onclick={copyGameCode} title="Copy code">Copy</button>
          </div>
          <p class="code-hint">Share this code with other players</p>
        </div>
      {/if}

      <div class="connection-status" class:connected={connectionStatus === 'connected'} class:error={connectionStatus === 'error'}>
        {connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting...' : connectionStatus === 'error' ? 'Connection Error' : 'Disconnected'}
      </div>

      <div class="players-list">
        <h3>Players ({lobbyPlayers.length}/4)</h3>
        {#each lobbyPlayers as player (player.id)}
          <div class="player-row">
            <span class="player-name">{player.username}</span>
            {#if player.deck_name}
              <span class="player-deck">{player.deck_name}</span>
            {/if}
            <span class="ready-badge" class:ready={player.ready}>
              {player.ready ? 'Ready' : 'Waiting'}
            </span>
          </div>
        {:else}
          <p class="empty-players">Waiting for players to join...</p>
        {/each}
      </div>

      {#if lobbyPlayers.length >= 2}
        <div class="ready-actions">
          <button class="ready-btn" onclick={handleDrawAndReady}>
            Draw Hand & Ready Up
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .lobby {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }

  .lobby-menu {
    text-align: center;
  }

  .lobby h1, .lobby h2 {
    margin: 0 0 0.25rem 0;
    color: hsl(var(--foreground));
    font-weight: 700;
  }

  .lobby h1 {
    font-size: 2rem;
  }

  .lobby h2 {
    font-size: 1.5rem;
  }

  .subtitle {
    color: hsl(var(--muted-foreground));
    margin: 0 0 2rem 0;
  }

  .menu-buttons {
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    margin-top: 2rem;
  }

  .menu-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem 3rem;
    background: hsl(var(--card));
    border: 2px solid hsl(var(--border));
    border-radius: var(--radius-xl);
    cursor: pointer;
    transition: all 0.2s;
    min-width: 200px;
  }

  .menu-btn:hover {
    border-color: hsl(var(--primary));
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }

  .btn-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    color: hsl(var(--primary));
  }

  .btn-text {
    font-size: 1.125rem;
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .btn-desc {
    font-size: 0.8rem;
    color: hsl(var(--muted-foreground));
    margin-top: 0.25rem;
  }

  .back-btn {
    margin-bottom: 1.5rem;
    padding: 0.5rem 1rem;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    cursor: pointer;
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    transition: all 0.15s;
  }

  .back-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .deck-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.75rem;
    text-align: left;
    margin-top: 1rem;
  }

  .deck-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
  }

  .deck-card:hover {
    border-color: hsl(var(--primary));
    transform: translateY(-2px);
  }

  .deck-thumb {
    width: 50px;
    height: 70px;
    object-fit: cover;
    border-radius: var(--radius-sm);
  }

  .deck-thumb-placeholder {
    width: 50px;
    height: 70px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: hsl(var(--secondary));
    border-radius: var(--radius-sm);
    font-size: 1.25rem;
    font-weight: 700;
    color: hsl(var(--muted-foreground));
  }

  .deck-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .deck-info h3 {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .format {
    font-size: 0.7rem;
    color: hsl(var(--primary));
    font-weight: 500;
  }

  .card-count {
    font-size: 0.7rem;
    color: hsl(var(--muted-foreground));
  }

  .no-decks {
    padding: 2rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    color: hsl(var(--muted-foreground));
    text-align: center;
  }

  /* Join form */
  .code-input-row {
    display: flex;
    justify-content: center;
    margin-bottom: 1rem;
  }

  .code-input {
    padding: 0.75rem 1rem;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: 0.25em;
    text-align: center;
    text-transform: uppercase;
    width: 220px;
    background: hsl(var(--card));
    border: 2px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    color: hsl(var(--foreground));
  }

  .code-input:focus {
    outline: none;
    border-color: hsl(var(--primary));
  }

  .error-text {
    color: hsl(var(--destructive));
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }

  /* Waiting room */
  .waiting-room {
    text-align: center;
  }

  .game-code-display {
    margin: 1.5rem 0;
    padding: 1.5rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-xl);
  }

  .code-label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
  }

  .code-value-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
  }

  .code-value {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    color: hsl(var(--primary));
  }

  .copy-btn {
    padding: 0.375rem 0.75rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    transition: all 0.15s;
  }

  .copy-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .code-hint {
    margin: 0.5rem 0 0 0;
    font-size: 0.8rem;
    color: hsl(var(--muted-foreground));
  }

  .connection-status {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 500;
    background: hsl(var(--secondary));
    color: hsl(var(--muted-foreground));
    margin-bottom: 1.5rem;
  }

  .connection-status.connected {
    background: hsl(142 76% 36% / 0.15);
    color: hsl(142 76% 36%);
  }

  .connection-status.error {
    background: hsl(var(--destructive) / 0.15);
    color: hsl(var(--destructive));
  }

  .players-list {
    text-align: left;
    max-width: 500px;
    margin: 0 auto;
  }

  .players-list h3 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    color: hsl(var(--foreground));
  }

  .player-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    margin-bottom: 0.5rem;
  }

  .player-name {
    font-weight: 600;
    color: hsl(var(--foreground));
    font-size: 0.9rem;
  }

  .player-deck {
    color: hsl(var(--muted-foreground));
    font-size: 0.8rem;
    flex: 1;
  }

  .ready-badge {
    padding: 0.2rem 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.7rem;
    font-weight: 600;
    background: hsl(var(--secondary));
    color: hsl(var(--muted-foreground));
  }

  .ready-badge.ready {
    background: hsl(142 76% 36% / 0.15);
    color: hsl(142 76% 36%);
  }

  .empty-players {
    color: hsl(var(--muted-foreground));
    font-style: italic;
    padding: 1rem;
    text-align: center;
  }

  .ready-actions {
    margin-top: 1.5rem;
  }

  .ready-btn {
    padding: 0.75rem 2rem;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border: none;
    border-radius: var(--radius-lg);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
  }

  .ready-btn:hover {
    opacity: 0.9;
    transform: translateY(-2px);
  }

  .join-form h3 {
    margin: 1.5rem 0 0.5rem 0;
    font-size: 1.125rem;
    color: hsl(var(--foreground));
  }
</style>
