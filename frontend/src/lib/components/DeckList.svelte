<script lang="ts">
  import { deckStore } from '../../stores/deckStore';
  import type { Deck } from '$lib/types';

  interface Props {
    onNavigate: (view: string) => void;
    onEdit: (deck: Deck) => void;
  }

  let { onNavigate, onEdit }: Props = $props();

  let decks = $derived($deckStore.decks);

  function handleEdit(deck: Deck): void {
    deckStore.selectDeck(deck.id);
    onEdit(deck);
  }

  function handleDelete(deckId: string): void {
    if (confirm('Are you sure you want to delete this deck?')) {
      deckStore.deleteDeck(deckId);
    }
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }
</script>

<div class="deck-list-page">
  <header class="page-header">
    <h1>My Decks</h1>
    <button class="new-deck-btn" onclick={() => onNavigate('new-deck')}>
      + New Deck
    </button>
  </header>

  {#if decks.length === 0}
    <div class="empty-state">
      <p>You haven't created any decks yet.</p>
      <button class="create-btn" onclick={() => onNavigate('new-deck')}>
        Create Your First Deck
      </button>
    </div>
  {:else}
    <div class="deck-grid">
      {#each decks as deck}
        <div class="deck-card">
          <div class="deck-info">
            <h3>{deck.name}</h3>
            <span class="format-badge">{deck.format}</span>
            {#if deck.description}
              <p class="description">{deck.description}</p>
            {/if}
            <div class="meta">
              <span>{deck.cards.reduce((sum, c) => sum + c.quantity, 0)} cards</span>
              <span>Updated {formatDate(deck.updatedAt)}</span>
            </div>
          </div>
          <div class="deck-actions">
            <button class="edit-btn" onclick={() => handleEdit(deck)}>Edit</button>
            <button class="delete-btn" onclick={() => handleDelete(deck.id)}>Delete</button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .deck-list-page {
    padding: 3rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2.5rem;
  }

  .page-header h1 {
    margin: 0;
    color: var(--color-text);
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.025em;
  }

  .new-deck-btn {
    padding: 0.75rem 1.5rem;
    background: var(--color-primary);
    color: var(--color-bg);
    border: none;
    border-radius: var(--radius-md);
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .new-deck-btn:hover {
    background: var(--color-primary-hover);
    box-shadow: var(--shadow-glow);
  }

  .empty-state {
    text-align: center;
    padding: 5rem 2rem;
    background: var(--color-bg-tertiary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--radius-lg);
  }

  .empty-state p {
    font-size: 1.125rem;
    color: var(--color-text-secondary);
    margin-bottom: 1.5rem;
  }

  .create-btn {
    padding: 1rem 2rem;
    background: var(--color-primary);
    color: var(--color-bg);
    border: none;
    border-radius: var(--radius-md);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .create-btn:hover {
    background: var(--color-primary-hover);
    box-shadow: var(--shadow-glow);
  }

  .deck-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.25rem;
  }

  .deck-card {
    background: var(--color-bg-tertiary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all var(--transition-fast);
  }

  .deck-card:hover {
    border-color: var(--color-border);
  }

  .deck-info h3 {
    margin: 0 0 0.75rem 0;
    color: var(--color-text);
    font-size: 1.125rem;
    font-weight: 600;
  }

  .format-badge {
    display: inline-block;
    padding: 0.25rem 0.625rem;
    background: var(--color-primary-muted);
    color: var(--color-primary);
    border-radius: var(--radius-sm);
    font-size: 0.8rem;
    font-weight: 600;
  }

  .description {
    color: var(--color-text-secondary);
    font-size: 0.9rem;
    margin: 0.75rem 0;
    line-height: 1.5;
  }

  .meta {
    display: flex;
    gap: 1.25rem;
    font-size: 0.8rem;
    color: var(--color-text-muted);
    margin-top: 0.75rem;
  }

  .deck-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1.25rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--color-border-subtle);
  }

  .edit-btn {
    flex: 1;
    padding: 0.625rem;
    background: var(--color-primary);
    color: var(--color-bg);
    border: none;
    border-radius: var(--radius-sm);
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .edit-btn:hover {
    background: var(--color-primary-hover);
  }

  .delete-btn {
    padding: 0.625rem 1rem;
    background: var(--color-danger-muted);
    color: var(--color-danger);
    border: none;
    border-radius: var(--radius-sm);
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .delete-btn:hover {
    background: var(--color-danger);
    color: var(--color-bg);
  }
</style>
