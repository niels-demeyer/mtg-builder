<script lang="ts">
  import type { GameCard, GameZone } from "$lib/types";

  interface Props {
    card: GameCard;
    size?: "small" | "medium" | "large";
    showOverlay?: boolean;
    draggable?: boolean;
    onclick?: (card: GameCard) => void;
    ondblclick?: (card: GameCard) => void;
    oncontextmenu?: (card: GameCard, event: MouseEvent) => void;
    ondragstart?: (card: GameCard, event: DragEvent) => void;
    ondragend?: (card: GameCard, event: DragEvent) => void;
  }

  let {
    card,
    size = "medium",
    showOverlay = true,
    draggable = true,
    onclick,
    ondblclick,
    oncontextmenu,
    ondragstart,
    ondragend,
  }: Props = $props();

  let isHovered = $state(false);
  let previewX = $state(0);
  let previewY = $state(0);
  let previewPosition = $state<"above" | "below">("above");

  const sizeClasses = {
    small: "card-small",
    medium: "card-medium",
    large: "card-large",
  };

  function handleClick() {
    onclick?.(card);
  }

  function handleDblClick() {
    ondblclick?.(card);
  }

  function handleContextMenu(event: MouseEvent) {
    event.preventDefault();
    oncontextmenu?.(card, event);
  }

  function handleDragStart(event: DragEvent) {
    if (!draggable) {
      event.preventDefault();
      return;
    }
    event.dataTransfer?.setData("text/plain", card.instanceId);
    event.dataTransfer?.setData("application/json", JSON.stringify(card));
    ondragstart?.(card, event);
  }

  function handleDragEnd(event: DragEvent) {
    ondragend?.(card, event);
  }

  function handleMouseEnter(event: MouseEvent) {
    isHovered = true;
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    previewX = rect.left + rect.width / 2;
    const screenMiddleY = window.innerHeight / 2;
    if (rect.top < screenMiddleY) {
      previewPosition = "below";
      previewY = rect.bottom + 12;
    } else {
      previewPosition = "above";
      previewY = rect.top - 12;
    }
  }

  function handleMouseLeave() {
    isHovered = false;
  }

  // Keep preview in viewport bounds
  const previewStyle = $derived.by(() => {
    const previewWidth = 240;
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

  // Get counter display
  const countersDisplay = $derived(
    Object.entries(card.counters)
      .filter(([_, count]) => count > 0)
      .map(([type, count]) => `${count} ${type}`)
  );

  const hasCounters = $derived(countersDisplay.length > 0);

  const showPreview = $derived(isHovered && !card.faceDown && !!card.image_uri);

  // Portal action: moves element to document.body to escape CSS containing blocks
  // (transforms on ancestors break position:fixed)
  function portal(node: HTMLElement) {
    document.body.appendChild(node);
    return {
      destroy() {
        node.remove();
      },
    };
  }
</script>

<div
  class="game-card {sizeClasses[size]}"
  class:tapped={card.isTapped}
  class:face-down={card.faceDown}
  {draggable}
  role="button"
  tabindex="0"
  onclick={handleClick}
  ondblclick={handleDblClick}
  oncontextmenu={handleContextMenu}
  ondragstart={handleDragStart}
  ondragend={handleDragEnd}
  onmouseenter={handleMouseEnter}
  onmouseleave={handleMouseLeave}
  onkeydown={(e) => e.key === "Enter" && handleClick()}
>
  {#if card.faceDown}
    <div class="card-back">
      <div class="card-back-design"></div>
    </div>
  {:else}
    <img
      src={card.image_uri || "/card-placeholder.png"}
      alt={card.name}
      class="card-image"
      loading="lazy"
    />

    {#if showOverlay && (card.isTapped || hasCounters || card.isCommander)}
      <div class="card-overlay">
        {#if card.isCommander}
          <span class="commander-badge">CMD</span>
        {/if}
        {#if hasCounters}
          <div class="counters">
            {#each countersDisplay as counter}
              <span class="counter-badge">{counter}</span>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  {/if}
</div>

{#if showPreview}
  <div class="hover-preview" style={previewStyle} use:portal>
    <img
      src={card.image_uri}
      alt={card.name}
      class="preview-image"
    />
  </div>
{/if}

<style>
  .game-card {
    position: relative;
    border-radius: var(--radius-md);
    overflow: hidden;
    cursor: pointer;
    transition: transform var(--transition-fast), box-shadow var(--transition-fast);
    aspect-ratio: 63 / 88;
    background: hsl(var(--secondary));
    flex-shrink: 0;
  }

  .game-card:hover {
    box-shadow: 0 0 0 2px hsl(var(--primary) / 0.5);
  }

  .game-card:focus-visible {
    outline: 2px solid hsl(var(--primary));
    outline-offset: 2px;
  }

  .card-small {
    width: 80px;
  }

  .card-medium {
    width: 130px;
  }

  .card-large {
    width: 200px;
  }

  .card-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .tapped {
    transform: rotate(90deg);
    transform-origin: center center;
  }

  .tapped:hover {
    transform: rotate(90deg) scale(1.05);
  }

  .face-down .card-back {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .card-back-design {
    width: 70%;
    height: 80%;
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-md);
    background: radial-gradient(ellipse at center, rgba(255, 215, 0, 0.1) 0%, transparent 70%);
  }

  .card-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    display: flex;
    flex-direction: column;
    padding: 0.25rem;
    gap: 0.25rem;
  }

  .commander-badge {
    position: absolute;
    top: 0.25rem;
    right: 0.25rem;
    background: linear-gradient(135deg, #ffd700, #ff8c00);
    color: #000;
    font-size: 0.6rem;
    font-weight: 700;
    padding: 0.15rem 0.35rem;
    border-radius: var(--radius-sm);
    text-transform: uppercase;
  }

  .counters {
    position: absolute;
    bottom: 0.25rem;
    left: 0.25rem;
    right: 0.25rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem;
    justify-content: center;
  }

  .counter-badge {
    background: rgba(0, 0, 0, 0.8);
    color: #4ade80;
    font-size: 0.55rem;
    font-weight: 600;
    padding: 0.1rem 0.3rem;
    border-radius: var(--radius-sm);
    border: 1px solid #4ade80;
  }

  [draggable="true"] {
    cursor: grab;
  }

  [draggable="true"]:active {
    cursor: grabbing;
  }

  /* Hover Preview - :global because portal moves element to document.body */
  :global(.hover-preview) {
    position: fixed;
    z-index: 1000;
    pointer-events: none;
  }

  :global(.preview-image) {
    width: 240px;
    height: auto;
    border-radius: 12px;
    box-shadow:
      0 0 0 2px hsl(var(--border)),
      0 20px 60px rgba(0, 0, 0, 0.5),
      0 0 40px rgba(0, 0, 0, 0.3);
  }
</style>
