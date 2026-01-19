<script lang="ts">
  import type { CardInDeck, CardZone } from '$lib/types';
  import { deckStore } from '../../stores/deckStore';

  interface Props {
    card: CardInDeck | null;
    onClose?: () => void;
  }

  let { card, onClose }: Props = $props();

  let showTagInput = $state(false);
  let newTag = $state('');

  const predefinedTags = ['Ramp', 'Removal', 'Win Con', 'Draw', 'Protection', 'Tutor', 'Board Wipe', 'Counter', 'Recursion'];

  function addTag(tag: string): void {
    if (card && !card.tags.includes(tag)) {
      deckStore.updateCardTags(card.id, [...card.tags, tag]);
    }
    newTag = '';
    showTagInput = false;
  }

  function removeTag(tag: string): void {
    if (card) {
      deckStore.updateCardTags(card.id, card.tags.filter(t => t !== tag));
    }
  }

  function handleTagKeydown(e: KeyboardEvent): void {
    if (e.key === 'Enter' && newTag.trim()) {
      addTag(newTag.trim());
    } else if (e.key === 'Escape') {
      showTagInput = false;
      newTag = '';
    }
  }

  function moveToZone(zone: CardZone): void {
    if (card && card.zone !== zone) {
      deckStore.moveCardToZone(card.id, card.zone, zone);
    }
  }

  function toggleCommander(): void {
    if (card) {
      deckStore.setCommander(card.id, !card.isCommander);
    }
  }

  const zones: { id: CardZone; label: string }[] = [
    { id: 'mainboard', label: 'Mainboard' },
    { id: 'sideboard', label: 'Sideboard' },
    { id: 'maybeboard', label: 'Maybeboard' },
    { id: 'considering', label: 'Considering' },
  ];
</script>

<div class="card-preview">
  {#if card}
    <div class="preview-header">
      <h3>{card.name}</h3>
      {#if onClose}
        <button class="close-btn" onclick={onClose}>✕</button>
      {/if}
    </div>

    <div class="preview-image">
      {#if card.image_uri}
        <img src={card.image_uri} alt={card.name} />
      {:else}
        <div class="no-image">
          <span>No image</span>
        </div>
      {/if}
    </div>

    <div class="preview-details">
      <div class="detail-row">
        <span class="detail-label">Type</span>
        <span class="detail-value">{card.type_line}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Mana Cost</span>
        <span class="detail-value mana">{card.mana_cost || 'None'}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">CMC</span>
        <span class="detail-value">{card.cmc}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Rarity</span>
        <span class="detail-value rarity-{card.rarity}">{card.rarity}</span>
      </div>
    </div>

    <div class="preview-section">
      <div class="section-header">
        <h4>Zone</h4>
      </div>
      <div class="zone-buttons">
        {#each zones as zone}
          <button 
            class="zone-btn"
            class:active={card.zone === zone.id}
            onclick={() => moveToZone(zone.id)}
          >
            {zone.label}
          </button>
        {/each}
      </div>
      
      <button 
        class="commander-btn"
        class:active={card.isCommander}
        onclick={toggleCommander}
      >
        {card.isCommander ? '★ Commander' : '☆ Set as Commander'}
      </button>
    </div>

    <div class="preview-section">
      <div class="section-header">
        <h4>Tags</h4>
        <button 
          class="add-tag-btn" 
          onclick={() => showTagInput = !showTagInput}
        >
          + Add
        </button>
      </div>

      <div class="tags-list">
        {#each card.tags as tag}
          <span class="tag">
            {tag}
            <button class="tag-remove" onclick={() => removeTag(tag)}>✕</button>
          </span>
        {/each}
        {#if card.tags.length === 0}
          <span class="no-tags">No tags</span>
        {/if}
      </div>

      {#if showTagInput}
        <div class="tag-input-container">
          <input
            type="text"
            placeholder="Enter tag..."
            bind:value={newTag}
            onkeydown={handleTagKeydown}
          />
          <div class="predefined-tags">
            {#each predefinedTags.filter(t => !card?.tags.includes(t)) as tag}
              <button class="predefined-tag" onclick={() => addTag(tag)}>
                {tag}
              </button>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="no-card">
      <p>Select a card to preview</p>
    </div>
  {/if}
</div>

<style>
  .card-preview {
    background: hsl(var(--card));
    border-radius: var(--radius-lg);
    border: 1px solid hsl(var(--border));
    overflow: hidden;
  }

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid hsl(var(--border));
  }

  .preview-header h3 {
    font-size: 0.9375rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .close-btn {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .close-btn:hover {
    background: hsl(var(--secondary));
    color: hsl(var(--foreground));
  }

  .preview-image {
    padding: 1rem;
    display: flex;
    justify-content: center;
  }

  .preview-image img {
    max-width: 100%;
    height: auto;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-md);
  }

  .no-image {
    width: 200px;
    height: 280px;
    background: hsl(var(--secondary));
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
  }

  .preview-details {
    padding: 0 1rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-label {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .detail-value {
    font-size: 0.8125rem;
    color: hsl(var(--foreground));
    text-align: right;
  }

  .detail-value.mana {
    font-family: monospace;
  }

  .rarity-common { color: hsl(var(--muted-foreground)); }
  .rarity-uncommon { color: #c0c0c0; }
  .rarity-rare { color: #ffd700; }
  .rarity-mythic { color: #ff8c00; }

  .preview-section {
    padding: 0.75rem 1rem;
    border-top: 1px solid hsl(var(--border));
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .section-header h4 {
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
  }

  .add-tag-btn {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
  }

  .add-tag-btn:hover {
    background: hsl(var(--secondary));
    color: hsl(var(--foreground));
  }

  .zone-buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.375rem;
    margin-bottom: 0.5rem;
  }

  .zone-btn {
    padding: 0.5rem;
    font-size: 0.75rem;
    background: hsl(var(--secondary));
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .zone-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .zone-btn.active {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border-color: hsl(var(--primary));
  }

  .commander-btn {
    width: 100%;
    padding: 0.5rem;
    font-size: 0.75rem;
    background: hsl(var(--secondary));
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .commander-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .commander-btn.active {
    background: hsl(45 100% 50% / 0.2);
    color: hsl(45 100% 70%);
    border-color: hsl(45 100% 50% / 0.5);
  }

  .tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
    margin-bottom: 0.5rem;
  }

  .tag {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: hsl(var(--accent));
    border-radius: var(--radius-full);
    font-size: 0.6875rem;
    color: hsl(var(--foreground));
  }

  .tag-remove {
    width: 14px;
    height: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    font-size: 0.625rem;
    border-radius: 50%;
    transition: all var(--transition-fast);
  }

  .tag-remove:hover {
    background: hsl(var(--destructive));
    color: hsl(var(--destructive-foreground));
  }

  .no-tags {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    font-style: italic;
  }

  .tag-input-container {
    margin-top: 0.5rem;
  }

  .tag-input-container input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
    margin-bottom: 0.5rem;
  }

  .tag-input-container input:focus {
    outline: none;
    border-color: hsl(var(--ring));
  }

  .predefined-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .predefined-tag {
    padding: 0.25rem 0.5rem;
    font-size: 0.6875rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-full);
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .predefined-tag:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .no-card {
    padding: 3rem 1rem;
    text-align: center;
  }

  .no-card p {
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
  }
</style>
