<script lang="ts">
  import { deckStore } from '../../stores/deckStore';
  import Button from './Button.svelte';

  interface Props {
    onNavigate: (view: string) => void;
  }

  let { onNavigate }: Props = $props();

  let recentDecks = $derived($deckStore.decks.slice(-3).reverse());

  async function makeHealthCall() {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/health');
      const data = await response.text();
      console.log('Response:', data);
      alert(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to connect to server');
    }
  }
</script>

<div class="home">
  <header class="hero">
    <div class="hero-badge">✦ Magic: The Gathering</div>
    <h1>Welcome to MTG Builder</h1>
    <p>Build, manage, and test your Magic: The Gathering decks with an intuitive deck building experience.</p>
  </header>

  <Button variant="primary" size="md" onclick={makeHealthCall}>
    Make Health Call
  </Button>

  <section class="quick-actions">
    <div class="section-header">
      <h2>Quick Actions</h2>
      <p>Get started with common tasks</p>
    </div>
    <div class="action-grid">
      <button class="action-card" onclick={() => onNavigate('new-deck')}>
        <div class="action-icon-wrapper">
          <span class="action-icon">+</span>
        </div>
        <div class="action-content">
          <span class="action-label">New Deck</span>
          <span class="action-desc">Create a new deck</span>
        </div>
      </button>
      <button class="action-card" onclick={() => onNavigate('decks')}>
        <div class="action-icon-wrapper secondary">
          <span class="action-icon">▤</span>
        </div>
        <div class="action-content">
          <span class="action-label">My Decks</span>
          <span class="action-desc">View your collection</span>
        </div>
      </button>
      <button class="action-card" onclick={() => onNavigate('explorer')}>
        <div class="action-icon-wrapper secondary">
          <span class="action-icon">◎</span>
        </div>
        <div class="action-content">
          <span class="action-label">Explore Cards</span>
          <span class="action-desc">Search all cards</span>
        </div>
      </button>
      <button class="action-card" onclick={() => onNavigate('training')}>
        <div class="action-icon-wrapper secondary">
          <span class="action-icon">◈</span>
        </div>
        <div class="action-content">
          <span class="action-label">Training</span>
          <span class="action-desc">Practice your skills</span>
        </div>
      </button>
    </div>
  </section>

  {#if recentDecks.length > 0}
    <section class="recent-decks">
      <div class="section-header">
        <h2>Recent Decks</h2>
        <button class="view-all-btn" onclick={() => onNavigate('decks')}>View all →</button>
      </div>
      <div class="deck-list">
        {#each recentDecks as deck}
          <div class="deck-card">
            <div class="deck-card-header">
              <h3>{deck.name}</h3>
              <span class="format-badge">{deck.format}</span>
            </div>
            <p class="card-count">{deck.cards.length} cards</p>
          </div>
        {/each}
      </div>
    </section>
  {/if}
</div>

<style>
  .home {
    padding: 2rem 3rem;
    max-width: 1000px;
    margin: 0 auto;
  }

  .hero {
    text-align: center;
    padding: 3rem 0 2.5rem;
  }

  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.875rem;
    background: hsl(var(--primary) / 0.1);
    color: hsl(var(--primary));
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 500;
    margin-bottom: 1rem;
    border: 1px solid hsl(var(--primary) / 0.2);
  }

  .hero h1 {
    font-size: 2.25rem;
    font-weight: 700;
    margin: 0 0 0.75rem 0;
    color: hsl(var(--foreground));
    letter-spacing: -0.035em;
    line-height: 1.2;
  }

  .hero p {
    font-size: 1rem;
    color: hsl(var(--muted-foreground));
    max-width: 480px;
    margin: 0 auto;
    line-height: 1.6;
  }

  .quick-actions {
    margin: 2rem 0;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1rem;
  }

  .section-header h2 {
    margin: 0;
    color: hsl(var(--foreground));
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .section-header p {
    font-size: 0.8125rem;
    color: hsl(var(--muted-foreground));
    margin: 0.25rem 0 0 0;
  }

  .view-all-btn {
    background: none;
    border: none;
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    cursor: pointer;
    transition: color var(--transition-fast);
  }

  .view-all-btn:hover {
    color: hsl(var(--foreground));
  }

  .action-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .action-card {
    display: flex;
    align-items: center;
    gap: 0.875rem;
    padding: 1rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition: all var(--transition-fast);
    text-align: left;
  }

  .action-card:hover {
    background: hsl(var(--accent));
    border-color: hsl(var(--border));
  }

  .action-card:focus-visible {
    outline: 2px solid hsl(var(--ring));
    outline-offset: 2px;
  }

  .action-icon-wrapper {
    width: 40px;
    height: 40px;
    background: hsl(var(--primary));
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .action-icon-wrapper.secondary {
    background: hsl(var(--muted));
  }

  .action-icon {
    font-size: 1.125rem;
    color: hsl(var(--primary-foreground));
  }

  .action-icon-wrapper.secondary .action-icon {
    color: hsl(var(--muted-foreground));
  }

  .action-content {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .action-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: hsl(var(--foreground));
  }

  .action-desc {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .recent-decks {
    margin: 2.5rem 0;
  }

  .deck-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .deck-card {
    padding: 1rem 1.25rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    transition: all var(--transition-fast);
  }

  .deck-card:hover {
    border-color: hsl(var(--primary) / 0.5);
  }

  .deck-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .deck-card h3 {
    margin: 0;
    color: hsl(var(--foreground));
    font-size: 0.875rem;
    font-weight: 500;
  }

  .format-badge {
    display: inline-flex;
    padding: 0.125rem 0.5rem;
    background: hsl(var(--muted));
    color: hsl(var(--muted-foreground));
    border-radius: var(--radius-sm);
    font-size: 0.6875rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }

  .card-count {
    color: hsl(var(--muted-foreground));
    font-size: 0.75rem;
    margin: 0.375rem 0 0 0;
  }
</style>
