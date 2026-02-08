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
    collapsed?: boolean;
  }

  let {
    cards,
    onCardClick,
    onCardDoubleClick,
    onCardContextMenu,
    onCardDragStart,
    onCardDragEnd,
    maxSpread = 40,
    collapsed = false,
  }: Props = $props();

  let isCollapsed = $state(collapsed);

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

<div class="hand-zone" class:collapsed={isCollapsed}>
  <button class="hand-label" onclick={() => (isCollapsed = !isCollapsed)}>
    <span class="label">Hand</span>
    <span class="count">({cards.length})</span>
    <span class="toggle-icon">{isCollapsed ? "\u25B2" : "\u25BC"}</span>
  </button>

  {#if !isCollapsed}
    <div class="hand-cards" class:empty={cards.length === 0}>
      {#if cards.length === 0}
        <div class="empty-hand">No cards in hand</div>
      {:else}
        {#each cards as card, index (card.instanceId)}
          <div
            class="hand-card"
            style={getCardStyle(index, cards.length)}
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
    flex-shrink: 0;
  }

  .hand-zone.collapsed {
    padding: 0.5rem 1rem;
  }

  .hand-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid hsl(var(--border));
    background: none;
    border-left: none;
    border-right: none;
    border-top: none;
    cursor: pointer;
    width: 100%;
    transition: color var(--transition-fast);
  }

  .hand-label:hover .label,
  .hand-label:hover .count {
    color: hsl(var(--primary));
  }

  .collapsed .hand-label {
    padding-bottom: 0;
    border-bottom: none;
  }

  .toggle-icon {
    margin-left: auto;
    font-size: 0.625rem;
    color: hsl(var(--muted-foreground));
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

</style>
