<script lang="ts">
  import type { CardInDeck, CardZone } from '$lib/types';
  import { deckStore } from '../../stores/deckStore';

  interface Props {
    card: CardInDeck | null;
    onClose?: () => void;
    isModal?: boolean;
  }

  let { card, onClose, isModal = false }: Props = $props();

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

  // Helper to check if card is a creature
  function isCreature(typeLine: string): boolean {
    return typeLine.toLowerCase().includes('creature');
  }
</script>

<div class="card-preview" class:is-modal={isModal}>
  {#if card}
    <div class="preview-header">
      <h3 title={card.name}>{card.name}</h3>
      {#if onClose}
        <button class="close-btn" onclick={onClose} aria-label="Close preview">✕</button>
      {/if}
    </div>

    <div class="preview-content">
      <div class="preview-image">
        {#if card.image_uri}
          <img src={card.image_uri} alt={card.name} loading="lazy" />
        {:else}
          <div class="no-image">
            <span>No image available</span>
          </div>
        {/if}
      </div>

      <div class="card-info">
        <!-- Type Line -->
        <div class="info-section type-section">
          <span class="type-line">{card.type_line}</span>
          {#if card.power && card.toughness && isCreature(card.type_line)}
            <span class="power-toughness">{card.power}/{card.toughness}</span>
          {/if}
        </div>

        <!-- Stats Row -->
        <div class="stats-row">
          {#if card.mana_cost}
            <div class="stat">
              <span class="stat-label">Mana</span>
              <span class="stat-value mana-cost">{card.mana_cost}</span>
            </div>
          {/if}
          <div class="stat">
            <span class="stat-label">CMC</span>
            <span class="stat-value">{card.cmc}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Rarity</span>
            <span class="stat-value rarity rarity-{card.rarity}">{card.rarity}</span>
          </div>
        </div>

        <!-- Oracle Text -->
        {#if card.oracle_text}
          <div class="info-section oracle-section">
            <h4>Card Text</h4>
            <div class="oracle-text">
              {#each card.oracle_text.split('\n') as paragraph}
                <p>{paragraph}</p>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Flavor Text -->
        {#if card.flavor_text}
          <div class="info-section flavor-section">
            <div class="flavor-text">
              {#each card.flavor_text.split('\n') as paragraph}
                <p>{paragraph}</p>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>

    <!-- Zone Controls -->
    <div class="preview-section">
      <h4>Move to Zone</h4>
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

    <!-- Tags Section -->
    <div class="preview-section">
      <div class="section-header">
        <h4>Tags</h4>
        <button
          class="add-tag-btn"
          onclick={() => showTagInput = !showTagInput}
        >
          {showTagInput ? '− Cancel' : '+ Add'}
        </button>
      </div>

      <div class="tags-list">
        {#each card.tags as tag}
          <span class="tag">
            {tag}
            <button class="tag-remove" onclick={() => removeTag(tag)} aria-label="Remove {tag}">✕</button>
          </span>
        {/each}
        {#if card.tags.length === 0 && !showTagInput}
          <span class="no-tags">No tags assigned</span>
        {/if}
      </div>

      {#if showTagInput}
        <div class="tag-input-container">
          <input
            type="text"
            placeholder="Type custom tag and press Enter..."
            bind:value={newTag}
            onkeydown={handleTagKeydown}
          />
          <div class="predefined-tags">
            <span class="predefined-label">Quick add:</span>
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
      <div class="no-card-icon">🃏</div>
      <p>Select a card to view details</p>
    </div>
  {/if}
</div>

<style>
  .card-preview {
    background: hsl(var(--card));
    border-radius: var(--radius-lg);
    border: 1px solid hsl(var(--border));
    overflow: hidden;
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
  }

  .card-preview.is-modal {
    max-height: 90vh;
    max-width: 400px;
    width: 100%;
  }

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.875rem 1rem;
    border-bottom: 1px solid hsl(var(--border));
    background: hsl(var(--secondary) / 0.5);
    flex-shrink: 0;
  }

  .preview-header h3 {
    font-size: 1rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
  }

  .close-btn {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all var(--transition-fast);
    flex-shrink: 0;
    margin-left: 0.5rem;
    font-size: 0.875rem;
  }

  .close-btn:hover {
    background: hsl(var(--destructive) / 0.1);
    color: hsl(var(--destructive));
  }

  .preview-content {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .preview-image {
    padding: 1rem;
    display: flex;
    justify-content: center;
    flex-shrink: 0;
    background: hsl(var(--secondary) / 0.3);
  }

  .preview-image img {
    width: 100%;
    max-width: 280px;
    height: auto;
    aspect-ratio: 63/88;
    object-fit: contain;
    border-radius: var(--radius-md);
    box-shadow: 0 4px 12px hsl(0 0% 0% / 0.3);
  }

  .no-image {
    width: 100%;
    max-width: 280px;
    aspect-ratio: 63/88;
    background: hsl(var(--secondary));
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    text-align: center;
    padding: 1rem;
  }

  .card-info {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.875rem;
  }

  .info-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .type-section {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    padding: 0.625rem 0.75rem;
    background: hsl(var(--secondary) / 0.5);
    border-radius: var(--radius-sm);
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .type-line {
    font-size: 0.8125rem;
    color: hsl(var(--foreground));
    font-weight: 500;
  }

  .power-toughness {
    font-size: 0.875rem;
    font-weight: 700;
    color: hsl(var(--primary));
    background: hsl(var(--primary) / 0.1);
    padding: 0.25rem 0.625rem;
    border-radius: var(--radius-sm);
  }

  .stats-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .stat {
    flex: 1;
    min-width: 70px;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.5rem 0.625rem;
    background: hsl(var(--secondary) / 0.3);
    border-radius: var(--radius-sm);
    border: 1px solid hsl(var(--border) / 0.5);
  }

  .stat-label {
    font-size: 0.625rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .stat-value {
    font-size: 0.8125rem;
    color: hsl(var(--foreground));
    font-weight: 500;
  }

  .stat-value.mana-cost {
    font-family: monospace;
    letter-spacing: 0.025em;
  }

  .stat-value.rarity {
    text-transform: capitalize;
    font-weight: 600;
  }

  .rarity-common { color: hsl(var(--muted-foreground)); }
  .rarity-uncommon { color: #8eb4c9; }
  .rarity-rare { color: #f0d060; }
  .rarity-mythic { color: #f07030; }

  .oracle-section h4 {
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
  }

  .oracle-text {
    font-size: 0.875rem;
    line-height: 1.6;
    color: hsl(var(--foreground));
    background: hsl(var(--secondary) / 0.5);
    padding: 1rem;
    border-radius: var(--radius-md);
    border: 1px solid hsl(var(--border));
    max-height: none;
  }

  .oracle-text p {
    margin: 0;
  }

  .oracle-text p + p {
    margin-top: 0.5rem;
  }

  .flavor-section {
    margin-top: -0.5rem;
  }

  .flavor-text {
    font-size: 0.8125rem;
    font-style: italic;
    line-height: 1.5;
    color: hsl(var(--muted-foreground));
    padding: 0.75rem 1rem;
    border-left: 2px solid hsl(var(--border));
  }

  .flavor-text p {
    margin: 0;
  }

  .flavor-text p + p {
    margin-top: 0.375rem;
  }

  .preview-section {
    padding: 0.875rem 1rem;
    border-top: 1px solid hsl(var(--border));
  }

  .preview-section h4 {
    font-size: 0.6875rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0 0 0.625rem 0;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.625rem;
  }

  .section-header h4 {
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
    padding: 0.5rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 500;
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
    font-weight: 500;
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
    min-height: 1.5rem;
  }

  .tag {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.3rem 0.5rem;
    background: hsl(var(--accent));
    border-radius: var(--radius-full);
    font-size: 0.6875rem;
    font-weight: 500;
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
    margin-top: 0.625rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .tag-input-container input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
  }

  .tag-input-container input::placeholder {
    color: hsl(var(--muted-foreground));
  }

  .tag-input-container input:focus {
    outline: none;
    border-color: hsl(var(--ring));
  }

  .predefined-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    align-items: center;
  }

  .predefined-label {
    font-size: 0.6875rem;
    color: hsl(var(--muted-foreground));
    margin-right: 0.25rem;
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
    border-color: hsl(var(--accent));
  }

  .no-card {
    padding: 3rem 1rem;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 200px;
  }

  .no-card-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .no-card p {
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    margin: 0;
  }

  /* Responsive styles for smaller panels */
  @container (max-width: 280px) {
    .preview-header h3 {
      font-size: 0.875rem;
    }

    .preview-image img {
      max-width: 180px;
    }

    .no-image {
      max-width: 180px;
    }

    .stats-row {
      flex-direction: column;
    }

    .stat {
      min-width: auto;
    }

    .zone-buttons {
      grid-template-columns: 1fr;
    }
  }

  /* For very narrow viewports */
  @media (max-width: 400px) {
    .card-preview.is-modal {
      max-width: 100%;
      border-radius: 0;
      max-height: 100vh;
    }

    .preview-image {
      padding: 0.75rem;
    }

    .preview-image img {
      max-width: 200px;
    }

    .card-info {
      padding: 0.75rem;
    }

    .preview-section {
      padding: 0.75rem;
    }
  }
</style>
