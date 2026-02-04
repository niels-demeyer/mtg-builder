<script lang="ts">
  import OpeningHands from './game/OpeningHands.svelte';
  import GameBoard from './game/GameBoard.svelte';
  import { gameStore } from '../../stores/gameStore';
  import { deckStore } from '../../stores/deckStore';
  import type { Deck } from '$lib/types';

  // Training mode for practicing with decks
  let selectedMode = $state<string | null>(null);

  const trainingModes = [
    {
      id: 'goldfish',
      name: 'Goldfish Testing',
      description: 'Practice your deck against an imaginary opponent with no interaction.',
      icon: '🐟',
    },
    {
      id: 'opening-hands',
      name: 'Opening Hands',
      description: 'Practice evaluating and mulliganing opening hands.',
      icon: '✋',
    },
    {
      id: 'card-quiz',
      name: 'Card Quiz',
      description: 'Test your knowledge of cards in your deck.',
      icon: '❓',
    },
  ];

  // Get decks for goldfish mode
  let decks = $derived($deckStore.decks);
  let selectedDeckForGoldfish = $state<Deck | null>(null);
  let goldfishStarted = $state(false);

  function selectMode(modeId: string): void {
    selectedMode = modeId;
  }

  function goBack(): void {
    selectedMode = null;
    selectedDeckForGoldfish = null;
    goldfishStarted = false;
    gameStore.reset();
  }

  function startGoldfish(deck: Deck): void {
    selectedDeckForGoldfish = deck;
    gameStore.initGame(deck);
    gameStore.drawOpeningHand();
    gameStore.startGame();
    goldfishStarted = true;
  }
</script>

<div class="training" class:fullscreen={selectedMode === 'opening-hands' || goldfishStarted}>
  {#if !selectedMode}
    <header class="training-header">
      <h1>Training Mode</h1>
      <p>Improve your gameplay skills with these practice modes</p>
    </header>

    <div class="mode-grid">
      {#each trainingModes as mode}
        <button class="mode-card" onclick={() => selectMode(mode.id)}>
          <span class="mode-icon">{mode.icon}</span>
          <h3>{mode.name}</h3>
          <p>{mode.description}</p>
        </button>
      {/each}
    </div>
  {:else if selectedMode === 'goldfish'}
    {#if !goldfishStarted}
      <div class="mode-content">
        <button class="back-btn" onclick={goBack}>← Back</button>
        <h1>🐟 Goldfish Testing</h1>
        <p class="subtitle">Select a deck to practice with</p>

        {#if decks.length === 0}
          <div class="no-decks">
            <p>No decks available. Create a deck first to practice.</p>
          </div>
        {:else}
          <div class="deck-grid">
            {#each decks as deck (deck.id)}
              <button class="deck-card" onclick={() => startGoldfish(deck)}>
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
    {:else}
      <div class="game-wrapper">
        <header class="game-header-bar">
          <button class="back-btn" onclick={goBack}>← Exit</button>
          <span class="game-title">🐟 Goldfish Mode - {selectedDeckForGoldfish?.name}</span>
        </header>
        <div class="game-area">
          <GameBoard showControls={true} showPhases={true} />
        </div>
      </div>
    {/if}
  {:else if selectedMode === 'opening-hands'}
    <OpeningHands onBack={goBack} />
  {:else if selectedMode === 'card-quiz'}
    <div class="mode-content">
      <button class="back-btn" onclick={goBack}>← Back</button>
      <h1>❓ Card Quiz</h1>
      <p class="coming-soon">Coming soon! This feature is under development.</p>
    </div>
  {/if}
</div>

<style>
  .training {
    padding: 3rem;
    max-width: 1000px;
    margin: 0 auto;
  }

  .training.fullscreen {
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

  .training-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .training-header h1 {
    margin: 0;
    color: hsl(var(--foreground));
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.025em;
  }

  .training-header p {
    color: hsl(var(--muted-foreground));
    margin-top: 0.5rem;
    font-size: 1rem;
  }

  .mode-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.25rem;
  }

  .mode-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 2.5rem 2rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-xl);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .mode-card:hover {
    border-color: hsl(var(--primary));
    transform: translateY(-4px);
    box-shadow: var(--shadow-glow);
  }

  .mode-icon {
    font-size: 3rem;
    margin-bottom: 1.25rem;
  }

  .mode-card h3 {
    margin: 0 0 0.625rem 0;
    color: hsl(var(--foreground));
    font-size: 1.125rem;
    font-weight: 600;
  }

  .mode-card p {
    margin: 0;
    color: hsl(var(--muted-foreground));
    font-size: 0.9rem;
    line-height: 1.5;
  }

  .mode-content {
    text-align: center;
    padding: 2rem;
  }

  .subtitle {
    margin-top: 0.5rem;
    margin-bottom: 2rem;
    color: hsl(var(--muted-foreground));
    font-size: 1rem;
  }

  .back-btn {
    margin-bottom: 2rem;
    padding: 0.625rem 1.25rem;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.95rem;
    color: hsl(var(--muted-foreground));
    transition: all var(--transition-fast);
  }

  .back-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .mode-content h1 {
    margin: 0;
    color: hsl(var(--foreground));
    font-size: 1.75rem;
    font-weight: 700;
  }

  .coming-soon {
    margin-top: 2rem;
    padding: 2.5rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    color: hsl(var(--muted-foreground));
    font-size: 1rem;
  }

  /* Deck selection grid for goldfish */
  .deck-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
    max-width: 900px;
    margin: 0 auto;
    text-align: left;
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
    padding: 3rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    color: hsl(var(--muted-foreground));
  }

  /* Game wrapper for goldfish mode */
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
    padding: 0.75rem 1rem;
    background: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
  }

  .game-header-bar .back-btn {
    margin-bottom: 0;
  }

  .game-title {
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .game-area {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
</style>
