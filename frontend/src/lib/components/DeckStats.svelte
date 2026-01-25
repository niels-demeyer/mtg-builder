<script lang="ts">
  import { currentDeckStats, deckStore } from '../../stores/deckStore';
  import { validateDeck } from '$lib/deckValidation';

  let stats = $derived($currentDeckStats);
  let currentDeck = $derived($deckStore.currentDeck);
  let validationIssues = $derived(currentDeck ? validateDeck(currentDeck) : []);
  let errors = $derived(validationIssues.filter(i => i.severity === 'error'));
  let warnings = $derived(validationIssues.filter(i => i.severity === 'warning'));
  let showAllIssues = $state(false);

  const colorNames: Record<string, string> = {
    W: 'White',
    U: 'Blue',
    B: 'Black',
    R: 'Red',
    G: 'Green',
    C: 'Colorless'
  };

  const colorClasses: Record<string, string> = {
    W: 'mana-white',
    U: 'mana-blue',
    B: 'mana-black',
    R: 'mana-red',
    G: 'mana-green',
    C: 'mana-colorless'
  };

  function getManaCurveMax(): number {
    if (!stats) return 1;
    return Math.max(...Object.values(stats.manaCurve), 1);
  }

  function getColorTotal(): number {
    if (!stats) return 1;
    return Math.max(Object.values(stats.colorDistribution).reduce((a, b) => a + b, 0), 1);
  }
</script>

<div class="deck-stats">
  <div class="stats-header">
    <h3>Deck Stats</h3>
    {#if currentDeck}
      <span class="format-badge">{currentDeck.format}</span>
    {/if}
  </div>

  {#if validationIssues.length > 0}
    <div class="validation-section" class:has-errors={errors.length > 0}>
      <div class="validation-header">
        <h4>
          {#if errors.length > 0}
            <span class="validation-icon error">!</span>
            {errors.length} {errors.length === 1 ? 'Issue' : 'Issues'}
          {:else}
            <span class="validation-icon warning">i</span>
            {warnings.length} {warnings.length === 1 ? 'Warning' : 'Warnings'}
          {/if}
        </h4>
        {#if validationIssues.length > 2}
          <button class="show-all-btn" onclick={() => showAllIssues = !showAllIssues}>
            {showAllIssues ? 'Show less' : 'Show all'}
          </button>
        {/if}
      </div>
      <div class="validation-issues">
        {#each showAllIssues ? validationIssues : validationIssues.slice(0, 2) as issue}
          <div class="validation-issue {issue.severity}">
            <span class="issue-icon">{issue.severity === 'error' ? '✕' : '!'}</span>
            <div class="issue-content">
              <span class="issue-message">{issue.message}</span>
              {#if issue.cards && issue.cards.length > 0}
                <span class="issue-cards">
                  {issue.cards.slice(0, 3).join(', ')}{issue.cards.length > 3 ? ` +${issue.cards.length - 3} more` : ''}
                </span>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {:else if currentDeck && currentDeck.cards.length > 0}
    <div class="validation-section valid">
      <div class="validation-valid">
        <span class="validation-icon valid">✓</span>
        <span>Deck is valid for {currentDeck.format}</span>
      </div>
    </div>
  {/if}

  {#if stats}
    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-value">{stats.mainboardCount}</span>
        <span class="stat-label">Mainboard</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{stats.sideboardCount}</span>
        <span class="stat-label">Sideboard</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{stats.averageCmc.toFixed(2)}</span>
        <span class="stat-label">Avg CMC</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{stats.landCount}</span>
        <span class="stat-label">Lands</span>
      </div>
    </div>

    <div class="stats-section">
      <h4>Mana Curve</h4>
      <div class="mana-curve">
        {#each Array.from({ length: 8 }) as _, i}
          <div class="curve-bar">
            <div 
              class="bar-fill" 
              style="height: {((stats.manaCurve[i] || 0) / getManaCurveMax()) * 100}%"
            >
              <span class="bar-count">{stats.manaCurve[i] || 0}</span>
            </div>
            <span class="bar-label">{i === 7 ? '7+' : i}</span>
          </div>
        {/each}
      </div>
    </div>

    <div class="stats-section">
      <h4>Color Distribution</h4>
      <div class="color-distribution">
        {#each Object.entries(stats.colorDistribution) as [color, count]}
          {#if count > 0}
            <div class="color-bar">
              <div class="color-info">
                <span class="color-pip {colorClasses[color]}"></span>
                <span class="color-name">{colorNames[color]}</span>
              </div>
              <div class="color-bar-track">
                <div 
                  class="color-bar-fill {colorClasses[color]}"
                  style="width: {(count / getColorTotal()) * 100}%"
                ></div>
              </div>
              <span class="color-count">{count}</span>
            </div>
          {/if}
        {/each}
      </div>
    </div>

    <div class="stats-section">
      <h4>Card Types</h4>
      <div class="type-distribution">
        <div class="type-row">
          <span class="type-label">Creatures</span>
          <span class="type-count">{stats.creatureCount}</span>
        </div>
        <div class="type-row">
          <span class="type-label">Spells</span>
          <span class="type-count">{stats.spellCount}</span>
        </div>
        <div class="type-row">
          <span class="type-label">Lands</span>
          <span class="type-count">{stats.landCount}</span>
        </div>
      </div>
    </div>

    {#if stats.maybeboardCount > 0 || stats.consideringCount > 0}
      <div class="stats-section">
        <h4>Other Zones</h4>
        <div class="type-distribution">
          {#if stats.maybeboardCount > 0}
            <div class="type-row">
              <span class="type-label">Maybeboard</span>
              <span class="type-count">{stats.maybeboardCount}</span>
            </div>
          {/if}
          {#if stats.consideringCount > 0}
            <div class="type-row">
              <span class="type-label">Considering</span>
              <span class="type-count">{stats.consideringCount}</span>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  {:else}
    <p class="no-stats">Add cards to see statistics</p>
  {/if}
</div>

<style>
  .deck-stats {
    background: hsl(var(--card));
    border-radius: var(--radius-lg);
    padding: 1rem;
    border: 1px solid hsl(var(--border));
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.25rem;
  }

  .stat-card {
    background: hsl(var(--secondary));
    padding: 0.75rem;
    border-radius: var(--radius-md);
    text-align: center;
  }

  .stat-value {
    display: block;
    font-size: 1.25rem;
    font-weight: 700;
    color: hsl(var(--foreground));
  }

  .stat-label {
    font-size: 0.6875rem;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .stats-section {
    margin-bottom: 1.25rem;
  }

  .stats-section:last-child {
    margin-bottom: 0;
  }

  .stats-section h4 {
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    margin: 0 0 0.75rem 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .mana-curve {
    display: flex;
    align-items: flex-end;
    gap: 0.375rem;
    height: 80px;
    padding: 0.5rem 0;
  }

  .curve-bar {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
  }

  .bar-fill {
    width: 100%;
    background: hsl(var(--primary) / 0.3);
    border-radius: var(--radius-sm) var(--radius-sm) 0 0;
    min-height: 4px;
    position: relative;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    transition: height var(--transition-normal);
  }

  .bar-count {
    font-size: 0.625rem;
    color: hsl(var(--foreground));
    padding-top: 0.25rem;
  }

  .bar-label {
    font-size: 0.625rem;
    color: hsl(var(--muted-foreground));
    margin-top: 0.25rem;
  }

  .color-distribution {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .color-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .color-info {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    width: 80px;
  }

  .color-pip {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }

  .color-pip.mana-white { background: var(--mana-white); }
  .color-pip.mana-blue { background: var(--mana-blue); }
  .color-pip.mana-black { background: var(--mana-black); border: 1px solid hsl(var(--border)); }
  .color-pip.mana-red { background: var(--mana-red); }
  .color-pip.mana-green { background: var(--mana-green); }
  .color-pip.mana-colorless { background: hsl(var(--muted)); }

  .color-name {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .color-bar-track {
    flex: 1;
    height: 8px;
    background: hsl(var(--secondary));
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .color-bar-fill {
    height: 100%;
    border-radius: var(--radius-full);
    transition: width var(--transition-normal);
  }

  .color-bar-fill.mana-white { background: var(--mana-white); }
  .color-bar-fill.mana-blue { background: var(--mana-blue); }
  .color-bar-fill.mana-black { background: hsl(var(--muted-foreground)); }
  .color-bar-fill.mana-red { background: var(--mana-red); }
  .color-bar-fill.mana-green { background: var(--mana-green); }
  .color-bar-fill.mana-colorless { background: hsl(var(--muted)); }

  .color-count {
    font-size: 0.75rem;
    color: hsl(var(--foreground));
    width: 24px;
    text-align: right;
  }

  .type-distribution {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .type-row {
    display: flex;
    justify-content: space-between;
    padding: 0.375rem 0.5rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-sm);
  }

  .type-label {
    font-size: 0.8125rem;
    color: hsl(var(--muted-foreground));
  }

  .type-count {
    font-size: 0.8125rem;
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .no-stats {
    text-align: center;
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    padding: 2rem 1rem;
  }

  /* Stats Header with Format Badge */
  .stats-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .stats-header h3 {
    font-size: 0.875rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    margin: 0;
  }

  .format-badge {
    font-size: 0.6875rem;
    padding: 0.25rem 0.5rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-full);
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  /* Validation Section */
  .validation-section {
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-md);
    border-left: 3px solid hsl(40 80% 50%);
  }

  .validation-section.has-errors {
    border-left-color: hsl(0 70% 50%);
    background: hsl(0 70% 50% / 0.08);
  }

  .validation-section.valid {
    border-left-color: hsl(142 70% 45%);
    background: hsl(142 70% 45% / 0.08);
  }

  .validation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .validation-header h4 {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.8125rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    margin: 0;
    text-transform: none;
    letter-spacing: normal;
  }

  .validation-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    font-size: 0.6875rem;
    font-weight: 700;
  }

  .validation-icon.error {
    background: hsl(0 70% 50%);
    color: white;
  }

  .validation-icon.warning {
    background: hsl(40 80% 50%);
    color: hsl(40 80% 15%);
  }

  .validation-icon.valid {
    background: hsl(142 70% 45%);
    color: white;
  }

  .show-all-btn {
    background: transparent;
    border: none;
    color: hsl(var(--primary));
    font-size: 0.75rem;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
  }

  .show-all-btn:hover {
    background: hsl(var(--accent));
  }

  .validation-issues {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .validation-issue {
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem;
    background: hsl(var(--background));
    border-radius: var(--radius-sm);
    font-size: 0.8125rem;
  }

  .validation-issue.error {
    border-left: 2px solid hsl(0 70% 50%);
  }

  .validation-issue.warning {
    border-left: 2px solid hsl(40 80% 50%);
  }

  .issue-icon {
    flex-shrink: 0;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.625rem;
    font-weight: 700;
    border-radius: 50%;
  }

  .validation-issue.error .issue-icon {
    background: hsl(0 70% 50% / 0.15);
    color: hsl(0 70% 45%);
  }

  .validation-issue.warning .issue-icon {
    background: hsl(40 80% 50% / 0.15);
    color: hsl(40 80% 35%);
  }

  .issue-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 0;
  }

  .issue-message {
    color: hsl(var(--foreground));
    line-height: 1.3;
  }

  .issue-cards {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    font-style: italic;
  }

  .validation-valid {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    color: hsl(142 70% 35%);
  }
</style>
