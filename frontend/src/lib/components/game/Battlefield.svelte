<script lang="ts">
  import type { GameCard } from "$lib/types";
  import GameCardComponent from "./GameCard.svelte";

  interface Props {
    cards: GameCard[];
    onCardClick?: (card: GameCard) => void;
    onCardDoubleClick?: (card: GameCard) => void;
    onCardContextMenu?: (card: GameCard, event: MouseEvent) => void;
    onCardDragStart?: (card: GameCard, event: DragEvent) => void;
    onCardDrop?: (card: GameCard) => void;
    groupByType?: boolean;
  }

  let {
    cards,
    onCardClick,
    onCardDoubleClick,
    onCardContextMenu,
    onCardDragStart,
    onCardDrop,
    groupByType = true,
  }: Props = $props();

  let isDragOver = $state(false);

  // Hover preview state
  let hoveredCard = $state<GameCard | null>(null);
  let previewX = $state(0);
  let previewY = $state(0);
  let previewPosition = $state<"above" | "below">("above");

  function handleCardHover(card: GameCard, event: MouseEvent) {
    hoveredCard = card;
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    // Center horizontally above/below the card
    previewX = rect.left + rect.width / 2;
    // Determine if preview should be above or below
    const screenMiddleY = window.innerHeight / 2;
    if (rect.top < screenMiddleY) {
      // Card is in upper half, show preview below
      previewPosition = "below";
      previewY = rect.bottom + 12;
    } else {
      // Card is in lower half, show preview above
      previewPosition = "above";
      previewY = rect.top - 12;
    }
  }

  function handleCardLeave() {
    hoveredCard = null;
  }

  // Calculate preview style (keeping it in viewport bounds)
  const previewStyle = $derived.by(() => {
    const previewWidth = 240;
    const previewHeight = 335; // approximate height for card aspect ratio
    const padding = 16;
    const maxX = window.innerWidth - previewWidth / 2 - padding;
    const minX = previewWidth / 2 + padding;
    const clampedX = Math.max(minX, Math.min(maxX, previewX));

    if (previewPosition === "below") {
      return `left: ${clampedX}px; top: ${previewY}px; transform: translateX(-50%);`;
    } else {
      return `left: ${clampedX}px; top: ${previewY}px; transform: translateX(-50%) translateY(-100%);`;
    }
  });

  // Group cards by type
  const groupedCards = $derived.by(() => {
    if (!groupByType) {
      return { All: cards };
    }

    const groups: Record<string, GameCard[]> = {
      Creatures: [],
      Lands: [],
      Artifacts: [],
      Enchantments: [],
      Planeswalkers: [],
      Other: [],
    };

    cards.forEach((card) => {
      const typeLine = card.type_line.toLowerCase();
      if (typeLine.includes("creature")) {
        groups.Creatures.push(card);
      } else if (typeLine.includes("land")) {
        groups.Lands.push(card);
      } else if (typeLine.includes("artifact")) {
        groups.Artifacts.push(card);
      } else if (typeLine.includes("enchantment")) {
        groups.Enchantments.push(card);
      } else if (typeLine.includes("planeswalker")) {
        groups.Planeswalkers.push(card);
      } else {
        groups.Other.push(card);
      }
    });

    // Remove empty groups
    return Object.fromEntries(
      Object.entries(groups).filter(([_, cards]) => cards.length > 0)
    );
  });

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
  class="battlefield-zone"
  class:drag-over={isDragOver}
  ondragover={handleDragOver}
  ondragleave={handleDragLeave}
  ondrop={handleDrop}
  role="region"
  aria-label="Battlefield"
>
  <div class="battlefield-header">
    <span class="label">Battlefield</span>
    <span class="count">({cards.length} permanents)</span>
  </div>

  <div class="battlefield-content">
    {#if cards.length === 0}
      <div class="empty-battlefield">
        <span>Drop cards here to play them</span>
      </div>
    {:else}
      {#each Object.entries(groupedCards) as [group, groupCards] (group)}
        <div class="card-group">
          <div class="group-label">{group}</div>
          <div class="group-cards">
            {#each groupCards as card (card.instanceId)}
              <div
                class="card-wrapper"
                onmouseenter={(e) => handleCardHover(card, e)}
                onmouseleave={handleCardLeave}
              >
                <GameCardComponent
                  {card}
                  size="small"
                  onclick={onCardClick}
                  ondblclick={onCardDoubleClick}
                  oncontextmenu={onCardContextMenu}
                  ondragstart={onCardDragStart}
                />
              </div>
            {/each}
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- Hover Preview -->
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
  .battlefield-zone {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 1rem;
    background: hsl(var(--card));
    border: 2px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    min-height: 300px;
    flex: 1;
    transition: all var(--transition-fast);
  }

  .battlefield-zone.drag-over {
    border-color: hsl(var(--primary));
    background: hsl(var(--primary) / 0.05);
  }

  .battlefield-header {
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

  .battlefield-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    flex: 1;
    overflow-y: auto;
  }

  .empty-battlefield {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    min-height: 200px;
    border: 2px dashed hsl(var(--border));
    border-radius: var(--radius-md);
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
  }

  .card-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .group-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .group-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .card-wrapper {
    position: relative;
  }

  /* Hover Preview - Large card displayed above/below battlefield cards */
  .hover-preview {
    position: fixed;
    z-index: 1000;
    pointer-events: none;
    animation: previewFadeIn 0.1s ease-out;
  }

  @keyframes previewFadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .preview-image {
    width: 240px;
    height: auto;
    border-radius: 12px;
    box-shadow:
      0 0 0 2px hsl(var(--border)),
      0 20px 60px rgba(0, 0, 0, 0.5),
      0 0 40px rgba(0, 0, 0, 0.3);
  }
</style>
