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
  let previewPosition = $state<"left" | "right">("left");

  function handleCardHover(card: GameCard, event: MouseEvent) {
    hoveredCard = card;
    // Position preview on opposite side of where the card is
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const screenMiddle = window.innerWidth / 2;
    previewPosition = rect.left < screenMiddle ? "right" : "left";
  }

  function handleCardLeave() {
    hoveredCard = null;
  }

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

  // Parse mana symbols for display
  function parseManaSymbols(manaCost: string | undefined): string[] {
    if (!manaCost) return [];
    const matches = manaCost.match(/\{[^}]+\}/g);
    return matches || [];
  }

  // Get mana symbol color class
  function getManaClass(symbol: string): string {
    const s = symbol.toLowerCase();
    if (s.includes("w")) return "mana-w";
    if (s.includes("u")) return "mana-u";
    if (s.includes("b")) return "mana-b";
    if (s.includes("r")) return "mana-r";
    if (s.includes("g")) return "mana-g";
    if (s.includes("c")) return "mana-c";
    return "mana-generic";
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

  <!-- Hover Preview Panel -->
  {#if hoveredCard}
    <div class="hover-preview" class:preview-left={previewPosition === "left"} class:preview-right={previewPosition === "right"}>
      <div class="preview-card">
        <img
          src={hoveredCard.image_uri || "/card-placeholder.png"}
          alt={hoveredCard.name}
          class="preview-image"
        />
      </div>
      <div class="preview-details">
        <div class="preview-header">
          <h3 class="preview-name">{hoveredCard.name}</h3>
          {#if hoveredCard.mana_cost}
            <div class="preview-mana">
              {#each parseManaSymbols(hoveredCard.mana_cost) as symbol}
                <span class="mana-symbol {getManaClass(symbol)}">{symbol.replace(/[{}]/g, "")}</span>
              {/each}
            </div>
          {/if}
        </div>
        <p class="preview-type">{hoveredCard.type_line}</p>
        {#if hoveredCard.oracle_text}
          <div class="preview-text">
            {#each hoveredCard.oracle_text.split("\n") as line}
              <p>{line}</p>
            {/each}
          </div>
        {/if}
        {#if hoveredCard.power !== undefined && hoveredCard.toughness !== undefined}
          <div class="preview-pt">
            <span>{hoveredCard.power}/{hoveredCard.toughness}</span>
          </div>
        {/if}
        <div class="preview-actions">
          <span class="action-hint">Click to select</span>
          <span class="action-hint">Double-click to play</span>
          <span class="action-hint">Right-click for options</span>
        </div>
      </div>
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

  /* Hover Preview Panel */
  .hover-preview {
    position: fixed;
    bottom: 240px;
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    z-index: 1000;
    max-width: 500px;
    animation: fadeIn 0.15s ease-out;
  }

  .hover-preview.preview-left {
    left: 1rem;
  }

  .hover-preview.preview-right {
    right: 1rem;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .preview-card {
    flex-shrink: 0;
  }

  .preview-image {
    width: 200px;
    height: auto;
    border-radius: var(--radius-md);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .preview-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 200px;
    max-width: 260px;
  }

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .preview-name {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
    color: hsl(var(--foreground));
    line-height: 1.2;
  }

  .preview-mana {
    display: flex;
    gap: 0.2rem;
    flex-shrink: 0;
  }

  .mana-symbol {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    font-size: 0.7rem;
    font-weight: 700;
  }

  .mana-w { background: #f9faf4; color: #1a1a1a; }
  .mana-u { background: #0e68ab; color: white; }
  .mana-b { background: #150b00; color: white; border: 1px solid #444; }
  .mana-r { background: #d3202a; color: white; }
  .mana-g { background: #00733e; color: white; }
  .mana-c { background: #ccc; color: #1a1a1a; }
  .mana-generic { background: #888; color: white; }

  .preview-type {
    margin: 0;
    font-size: 0.85rem;
    color: hsl(var(--muted-foreground));
    font-style: italic;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid hsl(var(--border));
  }

  .preview-text {
    flex: 1;
    overflow-y: auto;
    max-height: 150px;
  }

  .preview-text p {
    margin: 0 0 0.5rem 0;
    font-size: 0.85rem;
    color: hsl(var(--foreground));
    line-height: 1.4;
  }

  .preview-text p:last-child {
    margin-bottom: 0;
  }

  .preview-pt {
    display: flex;
    justify-content: flex-end;
    padding-top: 0.5rem;
    border-top: 1px solid hsl(var(--border));
  }

  .preview-pt span {
    font-size: 1.1rem;
    font-weight: 700;
    color: hsl(var(--primary));
    background: hsl(var(--background));
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-sm);
  }

  .preview-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid hsl(var(--border));
    margin-top: auto;
  }

  .action-hint {
    font-size: 0.7rem;
    color: hsl(var(--muted-foreground));
    background: hsl(var(--background));
    padding: 0.2rem 0.5rem;
    border-radius: var(--radius-sm);
  }

  @media (max-width: 768px) {
    .hover-preview {
      left: 50% !important;
      right: auto !important;
      transform: translateX(-50%);
      bottom: 260px;
      flex-direction: column;
      max-width: calc(100vw - 2rem);
    }

    .preview-image {
      width: 150px;
      margin: 0 auto;
    }

    .preview-details {
      max-width: none;
    }
  }
</style>
