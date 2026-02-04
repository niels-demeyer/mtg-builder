<script lang="ts">
  import type { GameCard } from "$lib/types";
  import GameCardComponent from "./GameCard.svelte";

  interface Props {
    cards: GameCard[];
    onCardClick?: (card: GameCard) => void;
    onCardDoubleClick?: (card: GameCard) => void;
    onCardContextMenu?: (card: GameCard, event: MouseEvent) => void;
    onCardDragStart?: (card: GameCard, event: DragEvent) => void;
    onCardDragEnd?: (card: GameCard, event: DragEvent) => void;
    maxSpread?: number;
  }

  let {
    cards,
    onCardClick,
    onCardDoubleClick,
    onCardContextMenu,
    onCardDragStart,
    onCardDragEnd,
    maxSpread = 40,
  }: Props = $props();

  // Hover preview state
  let hoveredCard = $state<GameCard | null>(null);
  let previewX = $state(0);

  function handleCardHover(card: GameCard, event: MouseEvent) {
    hoveredCard = card;
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    // Center the preview above the card
    previewX = rect.left + rect.width / 2;
  }

  function handleCardLeave() {
    hoveredCard = null;
  }

  // Calculate preview horizontal position (keeping it in viewport bounds)
  const previewStyle = $derived.by(() => {
    const previewWidth = 280;
    const padding = 16;
    const maxX = window.innerWidth - previewWidth / 2 - padding;
    const minX = previewWidth / 2 + padding;
    const clampedX = Math.max(minX, Math.min(maxX, previewX));
    return `left: ${clampedX}px; transform: translateX(-50%);`;
  });

  // Calculate card positions in a fan layout
  function getCardStyle(index: number, total: number): string {
    if (total === 1) return "transform: translateX(0) rotate(0deg);";

    const spread = Math.min(maxSpread, 60 / total);
    const totalSpread = spread * (total - 1);
    const startAngle = -totalSpread / 2;
    const angle = startAngle + spread * index;

    const offsetX = Math.sin((angle * Math.PI) / 180) * 20;
    const offsetY = Math.abs(angle) * 0.5;

    return `transform: translateX(${offsetX}px) translateY(${offsetY}px) rotate(${angle * 0.3}deg);`;
  }

</script>

<div class="hand-zone">
  <div class="hand-label">
    <span class="label">Hand</span>
    <span class="count">({cards.length})</span>
  </div>

  <div class="hand-cards" class:empty={cards.length === 0}>
    {#if cards.length === 0}
      <div class="empty-hand">No cards in hand</div>
    {:else}
      {#each cards as card, index (card.instanceId)}
        <div
          class="hand-card"
          style={getCardStyle(index, cards.length)}
          onmouseenter={(e) => handleCardHover(card, e)}
          onmouseleave={handleCardLeave}
          role="listitem"
        >
          <GameCardComponent
            {card}
            size="medium"
            onclick={onCardClick}
            ondblclick={onCardDoubleClick}
            oncontextmenu={onCardContextMenu}
            ondragstart={onCardDragStart}
            ondragend={onCardDragEnd}
          />
        </div>
      {/each}
    {/if}
  </div>

  <!-- Hover Preview - Large card image above the hand -->
  {#if hoveredCard}
    <div class="hover-preview" style={previewStyle}>
      <img
        src={hoveredCard.image_uri || "/card-placeholder.png"}
        alt={hoveredCard.name}
        class="preview-image"
      />
    </div>
  {/if}
</div>

<style>
  .hand-zone {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    background: hsl(var(--card));
    border: 2px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    min-height: 220px;
  }

  .hand-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid hsl(var(--border));
  }

  .label {
    font-size: 0.875rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .count {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .hand-cards {
    display: flex;
    align-items: flex-end;
    justify-content: center;
    flex-wrap: nowrap;
    gap: -20px;
    padding: 1rem 0;
    min-height: 180px;
    overflow-x: auto;
  }

  .hand-cards.empty {
    align-items: center;
    justify-content: center;
  }

  .hand-card {
    position: relative;
    transition: transform var(--transition-fast), z-index 0s;
    margin: 0 -15px;
  }

  .hand-card:hover {
    z-index: 20;
    transform: translateY(-30px) scale(1.1) !important;
  }

  .hand-card:first-child {
    margin-left: 0;
  }

  .hand-card:last-child {
    margin-right: 0;
  }

  .empty-hand {
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    font-style: italic;
  }

  /* Hover Preview - Large card displayed above the hand */
  .hover-preview {
    position: fixed;
    bottom: 240px;
    z-index: 1000;
    pointer-events: none;
    animation: previewFadeIn 0.1s ease-out;
  }

  @keyframes previewFadeIn {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }

  .preview-image {
    width: 280px;
    height: auto;
    border-radius: 12px;
    box-shadow:
      0 0 0 2px hsl(var(--border)),
      0 20px 60px rgba(0, 0, 0, 0.5),
      0 0 40px rgba(0, 0, 0, 0.3);
  }

  @media (max-width: 768px) {
    .hover-preview {
      bottom: 260px;
    }

    .preview-image {
      width: 220px;
    }
  }
</style>
