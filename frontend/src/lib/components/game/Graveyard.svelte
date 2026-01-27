<script lang="ts">
  import type { GameCard } from "$lib/types";
  import GameCardComponent from "./GameCard.svelte";

  interface Props {
    cards: GameCard[];
    onCardClick?: (card: GameCard) => void;
    onCardContextMenu?: (card: GameCard, event: MouseEvent) => void;
    onCardDrop?: (card: GameCard) => void;
    expanded?: boolean;
  }

  let {
    cards,
    onCardClick,
    onCardContextMenu,
    onCardDrop,
    expanded = false,
  }: Props = $props();

  let isExpanded = $state(expanded);
  let isDragOver = $state(false);

  const topCard = $derived(cards.length > 0 ? cards[cards.length - 1] : null);

  function toggleExpand() {
    isExpanded = !isExpanded;
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    isDragOver = true;
  }

  function handleDragLeave() {
    isDragOver = false;
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    isDragOver = false;
    const cardData = event.dataTransfer?.getData("application/json");
    if (cardData) {
      const card = JSON.parse(cardData) as GameCard;
      onCardDrop?.(card);
    }
  }
</script>

<div
  class="graveyard-zone"
  class:drag-over={isDragOver}
  class:expanded={isExpanded}
  ondragover={handleDragOver}
  ondragleave={handleDragLeave}
  ondrop={handleDrop}
  role="region"
  aria-label="Graveyard"
>
  <button class="zone-header" onclick={toggleExpand}>
    <span class="label">Graveyard</span>
    <span class="count">({cards.length})</span>
    <span class="expand-icon">{isExpanded ? "−" : "+"}</span>
  </button>

  {#if isExpanded}
    <div class="expanded-view">
      {#if cards.length === 0}
        <div class="empty-zone">Empty</div>
      {:else}
        <div class="card-grid">
          {#each cards as card (card.instanceId)}
            <GameCardComponent
              {card}
              size="small"
              onclick={onCardClick}
              oncontextmenu={onCardContextMenu}
              draggable={true}
            />
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="collapsed-view">
      {#if topCard}
        <div class="top-card-preview">
          <GameCardComponent
            card={topCard}
            size="small"
            onclick={onCardClick}
            oncontextmenu={onCardContextMenu}
            showOverlay={false}
          />
        </div>
      {:else}
        <div class="empty-zone-small">
          <span>Empty</span>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .graveyard-zone {
    display: flex;
    flex-direction: column;
    background: hsl(var(--card));
    border: 2px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    overflow: hidden;
    transition: all var(--transition-fast);
    min-width: 120px;
  }

  .graveyard-zone.drag-over {
    border-color: hsl(var(--destructive));
    background: hsl(var(--destructive) / 0.1);
  }

  .graveyard-zone.expanded {
    min-width: 300px;
  }

  .zone-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: none;
    border: none;
    border-bottom: 1px solid hsl(var(--border));
    cursor: pointer;
    text-align: left;
    transition: background var(--transition-fast);
  }

  .zone-header:hover {
    background: hsl(var(--accent));
  }

  .label {
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .count {
    font-size: 0.7rem;
    color: hsl(var(--muted-foreground));
  }

  .expand-icon {
    margin-left: auto;
    font-size: 1rem;
    color: hsl(var(--muted-foreground));
    font-weight: 300;
  }

  .collapsed-view {
    padding: 0.75rem;
    display: flex;
    justify-content: center;
  }

  .top-card-preview {
    opacity: 0.8;
  }

  .expanded-view {
    padding: 0.75rem;
    max-height: 300px;
    overflow-y: auto;
  }

  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 0.5rem;
  }

  .empty-zone {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    font-style: italic;
  }

  .empty-zone-small {
    width: 80px;
    height: 112px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed hsl(var(--border));
    border-radius: var(--radius-md);
    color: hsl(var(--muted-foreground));
    font-size: 0.75rem;
  }
</style>
