<script lang="ts">
  import { currentDeckStats } from '../../stores/deckStore';

  let stats = $derived($currentDeckStats);

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
  </div>

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

  .stats-header {
    margin-bottom: 1rem;
  }

  .stats-header h3 {
    font-size: 0.875rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    margin: 0;
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
</style>
