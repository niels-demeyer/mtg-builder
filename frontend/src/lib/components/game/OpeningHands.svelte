<script lang="ts">
  import type { Deck, OpeningHandEvaluation } from "$lib/types";
  import { gameStore, currentGame, currentPlayer } from "../../../stores/gameStore";
  import { deckStore } from "../../../stores/deckStore";
  import Hand from "./Hand.svelte";
  import GameBoard from "./GameBoard.svelte";
  import GameCardComponent from "./GameCard.svelte";

  interface Props {
    onBack?: () => void;
  }

  let { onBack }: Props = $props();

  let mode = $state<"select" | "opening" | "play">("select");
  let selectedDeckId = $state<string | null>(null);
  let handEvaluation = $state<OpeningHandEvaluation | null>(null);

  // Get decks from store
  let decks = $derived($deckStore.decks);
  let selectedDeck = $derived(decks.find((d) => d.id === selectedDeckId) || null);

  function selectDeck(deck: Deck) {
    selectedDeckId = deck.id;
    gameStore.initGame(deck);
    gameStore.drawOpeningHand();
    handEvaluation = gameStore.evaluateOpeningHand();
    mode = "opening";
  }

  function handleMulligan() {
    if (!$currentGame || $currentGame.mulliganCount >= 6) return;
    gameStore.mulligan();
    handEvaluation = gameStore.evaluateOpeningHand();
  }

  function handleKeep() {
    gameStore.startGame();
    mode = "play";
  }

  function handleNewHand() {
    if (!selectedDeck) return;
    gameStore.initGame(selectedDeck);
    gameStore.drawOpeningHand();
    handEvaluation = gameStore.evaluateOpeningHand();
  }

  function handleReset() {
    gameStore.reset();
    mode = "select";
    selectedDeckId = null;
    handEvaluation = null;
  }

  function handleCardClick(card: any) {
    gameStore.selectCard(card);
  }

  // Get score color
  function getScoreColor(score: number): string {
    if (score >= 70) return "var(--color-success, hsl(142 76% 36%))";
    if (score >= 40) return "var(--color-warning, hsl(38 92% 50%))";
    return "var(--color-danger, hsl(0 84% 60%))";
  }

  // Get score label
  function getScoreLabel(score: number): string {
    if (score >= 70) return "Strong Keep";
    if (score >= 55) return "Reasonable Keep";
    if (score >= 40) return "Borderline";
    return "Consider Mulligan";
  }
</script>

<div class="opening-hands">
  {#if mode === "select"}
    <!-- Deck Selection -->
    <div class="select-view">
      <header class="header">
        {#if onBack}
          <button class="back-btn" onclick={onBack}>← Back</button>
        {/if}
        <h1>Opening Hands</h1>
        <p>Select a deck to practice evaluating opening hands</p>
      </header>

      {#if decks.length === 0}
        <div class="no-decks">
          <p>No decks available. Create a deck first to practice opening hands.</p>
        </div>
      {:else}
        <div class="deck-grid">
          {#each decks as deck (deck.id)}
            <button class="deck-card" onclick={() => selectDeck(deck)}>
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
  {:else if mode === "opening" && $currentGame && $currentPlayer}
    <!-- Opening Hand Evaluation -->
    <div class="opening-view">
      <header class="header">
        <button class="back-btn" onclick={handleReset}>← Back</button>
        <div class="header-info">
          <h1>{selectedDeck?.name}</h1>
          <span class="format-badge">{selectedDeck?.format}</span>
        </div>
        <div class="mulligan-info">
          {#if $currentGame.mulliganCount > 0}
            <span class="mulligan-count">Mulligan {$currentGame.mulliganCount}</span>
          {/if}
          <span class="cards-in-hand">{$currentPlayer.hand.length} cards</span>
        </div>
      </header>

      <!-- Hand Display -->
      <div class="hand-display">
        <div class="hand-container">
          {#each $currentPlayer.hand as card (card.instanceId)}
            <div class="opening-card">
              <GameCardComponent
                {card}
                size="large"
                onclick={handleCardClick}
                draggable={false}
              />
            </div>
          {/each}
        </div>
      </div>

      <!-- Hand Evaluation -->
      {#if handEvaluation}
        <div class="evaluation-panel">
          <div class="score-section">
            <div
              class="score-circle"
              style="--score-color: {getScoreColor(handEvaluation.keepScore)}"
            >
              <span class="score-value">{handEvaluation.keepScore}</span>
            </div>
            <div class="score-info">
              <span class="score-label" style="color: {getScoreColor(handEvaluation.keepScore)}">
                {getScoreLabel(handEvaluation.keepScore)}
              </span>
              <span class="score-hint">Hand Quality Score</span>
            </div>
          </div>

          <div class="stats-grid">
            <div class="stat">
              <span class="stat-value">{handEvaluation.landCount}</span>
              <span class="stat-label">Lands</span>
            </div>
            <div class="stat">
              <span class="stat-value">{handEvaluation.nonLandCount}</span>
              <span class="stat-label">Spells</span>
            </div>
            <div class="stat">
              <span class="stat-value">{handEvaluation.averageCmc.toFixed(1)}</span>
              <span class="stat-label">Avg CMC</span>
            </div>
            <div class="stat">
              <span class="stat-value">{handEvaluation.hasEarlyPlay ? "Yes" : "No"}</span>
              <span class="stat-label">Early Play</span>
            </div>
          </div>

          {#if handEvaluation.suggestions.length > 0}
            <div class="suggestions">
              {#each handEvaluation.suggestions as suggestion}
                <p class="suggestion">{suggestion}</p>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      <!-- Action Buttons -->
      <div class="action-bar">
        <button
          class="action-btn mulligan"
          onclick={handleMulligan}
          disabled={$currentGame.mulliganCount >= 6}
        >
          Mulligan
          {#if $currentGame.mulliganCount < 6}
            (to {6 - $currentGame.mulliganCount})
          {/if}
        </button>
        <button class="action-btn new-hand" onclick={handleNewHand}>
          New Hand
        </button>
        <button class="action-btn keep" onclick={handleKeep}>
          Keep & Play
        </button>
      </div>
    </div>
  {:else if mode === "play"}
    <!-- Goldfish Play Mode -->
    <div class="play-view">
      <header class="play-header">
        <button class="back-btn" onclick={handleReset}>← Exit Game</button>
        <span class="header-title">Goldfish Mode</span>
      </header>
      <div class="game-container">
        <GameBoard showControls={true} showPhases={true} />
      </div>
    </div>
  {/if}
</div>

<style>
  .opening-hands {
    height: 100vh;
    width: 100%;
    display: flex;
    flex-direction: column;
    background: hsl(var(--background));
    overflow: hidden;
  }

  /* Header */
  .header {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.5rem 2rem;
    background: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
  }

  .header h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: hsl(var(--foreground));
  }

  .header p {
    margin: 0.25rem 0 0 0;
    color: hsl(var(--muted-foreground));
    font-size: 0.9rem;
  }

  .header-info {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex: 1;
  }

  .format-badge {
    padding: 0.25rem 0.75rem;
    background: hsl(var(--primary) / 0.1);
    color: hsl(var(--primary));
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .mulligan-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .mulligan-count {
    padding: 0.25rem 0.75rem;
    background: hsl(38 92% 50% / 0.15);
    color: hsl(38 92% 50%);
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
    font-weight: 500;
  }

  .cards-in-hand {
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
  }

  .back-btn {
    padding: 0.5rem 1rem;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    font-size: 0.875rem;
    transition: all var(--transition-fast);
  }

  .back-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  /* Deck Selection */
  .select-view {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .select-view .header {
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
  }

  .select-view .header .back-btn {
    margin-bottom: 1rem;
  }

  .deck-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
    padding: 2rem;
    overflow-y: auto;
  }

  .deck-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    cursor: pointer;
    text-align: left;
    transition: all var(--transition-fast);
  }

  .deck-card:hover {
    border-color: hsl(var(--primary));
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }

  .deck-thumb {
    width: 60px;
    height: 84px;
    object-fit: cover;
    border-radius: var(--radius-sm);
  }

  .deck-thumb-placeholder {
    width: 60px;
    height: 84px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: hsl(var(--secondary));
    border-radius: var(--radius-sm);
    font-size: 1.5rem;
    font-weight: 700;
    color: hsl(var(--muted-foreground));
  }

  .deck-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .deck-info h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .deck-info .format {
    font-size: 0.75rem;
    color: hsl(var(--primary));
    font-weight: 500;
  }

  .deck-info .card-count {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .no-decks {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    padding: 4rem;
    color: hsl(var(--muted-foreground));
  }

  /* Opening Hand View */
  .opening-view {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .hand-display {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    overflow-x: auto;
  }

  .hand-container {
    display: flex;
    gap: 1rem;
    padding: 1rem;
  }

  .opening-card {
    transition: transform var(--transition-fast);
  }

  .opening-card:hover {
    transform: translateY(-20px) scale(1.05);
    z-index: 10;
  }

  /* Evaluation Panel */
  .evaluation-panel {
    padding: 1.5rem 2rem;
    background: hsl(var(--card));
    border-top: 1px solid hsl(var(--border));
    display: flex;
    align-items: center;
    gap: 2rem;
    flex-wrap: wrap;
  }

  .score-section {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .score-circle {
    width: 70px;
    height: 70px;
    border-radius: 50%;
    background: hsl(var(--background));
    border: 4px solid var(--score-color);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .score-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: hsl(var(--foreground));
  }

  .score-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .score-label {
    font-size: 1rem;
    font-weight: 600;
  }

  .score-hint {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .stats-grid {
    display: flex;
    gap: 1.5rem;
    padding: 0 1.5rem;
    border-left: 1px solid hsl(var(--border));
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.125rem;
  }

  .stat-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: hsl(var(--foreground));
  }

  .stat-label {
    font-size: 0.7rem;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .suggestions {
    flex: 1;
    min-width: 200px;
  }

  .suggestion {
    margin: 0;
    padding: 0.375rem 0;
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    border-bottom: 1px solid hsl(var(--border));
  }

  .suggestion:last-child {
    border-bottom: none;
  }

  /* Action Bar */
  .action-bar {
    display: flex;
    gap: 1rem;
    padding: 1rem 2rem;
    background: hsl(var(--card));
    border-top: 1px solid hsl(var(--border));
    justify-content: center;
  }

  .action-btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: var(--radius-md);
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .action-btn.mulligan {
    background: hsl(38 92% 50% / 0.15);
    color: hsl(38 92% 50%);
  }

  .action-btn.mulligan:hover:not(:disabled) {
    background: hsl(38 92% 50% / 0.25);
  }

  .action-btn.new-hand {
    background: hsl(var(--secondary));
    color: hsl(var(--foreground));
  }

  .action-btn.new-hand:hover {
    background: hsl(var(--accent));
  }

  .action-btn.keep {
    background: hsl(142 76% 36%);
    color: white;
  }

  .action-btn.keep:hover {
    background: hsl(142 76% 30%);
  }

  /* Play View */
  .play-view {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .play-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
  }

  .header-title {
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .game-container {
    flex: 1;
    overflow: hidden;
  }

  @media (max-width: 768px) {
    .header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .hand-container {
      flex-wrap: wrap;
      justify-content: center;
    }

    .evaluation-panel {
      flex-direction: column;
      align-items: flex-start;
    }

    .stats-grid {
      border-left: none;
      border-top: 1px solid hsl(var(--border));
      padding: 1rem 0 0 0;
    }

    .action-bar {
      flex-direction: column;
    }

    .action-btn {
      width: 100%;
    }
  }
</style>
