<script lang="ts">
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

  function selectMode(modeId: string): void {
    selectedMode = modeId;
  }

  function goBack(): void {
    selectedMode = null;
  }
</script>

<div class="training">
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
    <div class="mode-content">
      <button class="back-btn" onclick={goBack}>← Back</button>
      <h1>🐟 Goldfish Testing</h1>
      <p class="coming-soon">Coming soon! This feature is under development.</p>
    </div>
  {:else if selectedMode === 'opening-hands'}
    <div class="mode-content">
      <button class="back-btn" onclick={goBack}>← Back</button>
      <h1>✋ Opening Hands</h1>
      <p class="coming-soon">Coming soon! This feature is under development.</p>
    </div>
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

  .training-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .training-header h1 {
    margin: 0;
    color: var(--color-text);
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.025em;
  }

  .training-header p {
    color: var(--color-text-secondary);
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
    background: var(--color-bg-tertiary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--radius-xl);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .mode-card:hover {
    border-color: var(--color-primary);
    transform: translateY(-4px);
    box-shadow: var(--shadow-glow);
  }

  .mode-icon {
    font-size: 3rem;
    margin-bottom: 1.25rem;
  }

  .mode-card h3 {
    margin: 0 0 0.625rem 0;
    color: var(--color-text);
    font-size: 1.125rem;
    font-weight: 600;
  }

  .mode-card p {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
    line-height: 1.5;
  }

  .mode-content {
    text-align: center;
    padding: 2rem;
  }

  .back-btn {
    margin-bottom: 2rem;
    padding: 0.625rem 1.25rem;
    background: transparent;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.95rem;
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);
  }

  .back-btn:hover {
    background: var(--color-bg-hover);
    color: var(--color-text);
  }

  .mode-content h1 {
    margin: 0;
    color: var(--color-text);
    font-size: 1.75rem;
    font-weight: 700;
  }

  .coming-soon {
    margin-top: 2rem;
    padding: 2.5rem;
    background: var(--color-bg-tertiary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--radius-lg);
    color: var(--color-text-secondary);
    font-size: 1rem;
  }
</style>
