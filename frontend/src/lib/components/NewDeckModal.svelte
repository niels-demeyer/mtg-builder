<script lang="ts">
  import { deckStore } from '../../stores/deckStore';
  import type { Deck, DeckFormat } from '$lib/types';

  interface Props {
    onComplete: (deck: Deck) => void;
    onCancel: () => void;
  }

  let { onComplete, onCancel }: Props = $props();

  let name = $state('');
  let format = $state<DeckFormat>('Standard');
  let description = $state('');

  const formats = [
    'Standard',
    'Modern',
    'Pioneer',
    'Legacy',
    'Vintage',
    'Commander',
    'Pauper',
    'Historic',
    'Alchemy',
    'Brawl',
  ];

  async function handleSubmit(event: Event): Promise<void> {
    event.preventDefault();
    if (!name.trim()) return;

    const deck = await deckStore.createDeck(name.trim(), format, description.trim());
    onComplete(deck);
  }

  function handleBackdropClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) {
      onCancel();
    }
  }

  function handleBackdropKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      onCancel();
    }
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div 
  class="modal-backdrop" 
  onclick={handleBackdropClick}
  onkeydown={handleBackdropKeydown}
  role="presentation"
>
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <header class="modal-header">
      <h2 id="modal-title">Create New Deck</h2>
      <button class="close-btn" onclick={onCancel}>✕</button>
    </header>

    <form onsubmit={handleSubmit}>
      <div class="form-group">
        <label for="deck-name">Deck Name</label>
        <input
          id="deck-name"
          type="text"
          placeholder="Enter deck name..."
          bind:value={name}
          required
        />
      </div>

      <div class="form-group">
        <label for="deck-format">Format</label>
        <select id="deck-format" bind:value={format}>
          {#each formats as fmt}
            <option value={fmt}>{fmt}</option>
          {/each}
        </select>
      </div>

      <div class="form-group">
        <label for="deck-description">Description (optional)</label>
        <textarea
          id="deck-description"
          placeholder="Describe your deck strategy..."
          bind:value={description}
          rows="3"
        ></textarea>
      </div>

      <div class="modal-actions">
        <button type="button" class="cancel-btn" onclick={onCancel}>
          Cancel
        </button>
        <button type="submit" class="submit-btn" disabled={!name.trim()}>
          Create Deck
        </button>
      </div>
    </form>
  </div>
</div>

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: var(--color-bg-tertiary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    width: 100%;
    max-width: 480px;
    box-shadow: var(--shadow-lg);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid var(--color-border-subtle);
  }

  .modal-header h2 {
    margin: 0;
    color: var(--color-text);
    font-size: 1.25rem;
    font-weight: 600;
  }

  .close-btn {
    width: 32px;
    height: 32px;
    background: var(--color-bg-hover);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);
  }

  .close-btn:hover {
    background: var(--color-border);
    color: var(--color-text);
  }

  form {
    padding: 1.5rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--color-text-secondary);
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    font-family: inherit;
    background: var(--color-bg-secondary);
    color: var(--color-text);
  }

  .form-group input::placeholder,
  .form-group textarea::placeholder {
    color: var(--color-text-muted);
  }

  .form-group input:focus,
  .form-group select:focus,
  .form-group textarea:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px var(--color-primary-muted);
  }

  .form-group select {
    cursor: pointer;
  }

  .form-group select option {
    background: var(--color-bg-secondary);
    color: var(--color-text);
  }

  .form-group textarea {
    resize: vertical;
    min-height: 80px;
  }

  .modal-actions {
    display: flex;
    gap: 0.75rem;
    margin-top: 1.5rem;
  }

  .cancel-btn {
    flex: 1;
    padding: 0.75rem;
    background: var(--color-bg-hover);
    border: none;
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);
  }

  .cancel-btn:hover {
    background: var(--color-border);
    color: var(--color-text);
  }

  .submit-btn {
    flex: 1;
    padding: 0.75rem;
    background: var(--color-primary);
    color: var(--color-bg);
    border: none;
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .submit-btn:hover:not(:disabled) {
    background: var(--color-primary-hover);
    box-shadow: var(--shadow-glow);
  }

  .submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
