<script lang="ts">
  import type { GameCard } from "$lib/types";

  interface Props {
    cards: GameCard[];
    onDraw?: () => void;
    onShuffle?: () => void;
    onMill?: (count: number) => void;
    onCardDrop?: (card: GameCard) => void;
  }

  let { cards, onDraw, onShuffle, onMill, onCardDrop }: Props = $props();

  let isDragOver = $state(false);
  let showMenu = $state(false);
  let millCount = $state(1);

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

  function handleClick() {
    onDraw?.();
  }

  function handleContextMenu(event: MouseEvent) {
    event.preventDefault();
    showMenu = !showMenu;
  }

  function handleMill() {
    onMill?.(millCount);
    showMenu = false;
  }

  function handleShuffle() {
    onShuffle?.();
    showMenu = false;
  }

  // Close menu when clicking outside
  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest(".library-zone")) {
      showMenu = false;
    }
  }
</script>

<svelte:window onclick={handleClickOutside} />

<div
  class="library-zone"
  class:drag-over={isDragOver}
  role="button"
  tabindex="0"
  ondragover={handleDragOver}
  ondragleave={handleDragLeave}
  ondrop={handleDrop}
  onclick={handleClick}
  oncontextmenu={handleContextMenu}
  onkeydown={(e) => e.key === "Enter" && handleClick()}
>
  <div class="library-stack">
    {#if cards.length > 0}
      <!-- Visual stack effect -->
      <div class="stack-layer layer-3"></div>
      <div class="stack-layer layer-2"></div>
      <div class="stack-layer layer-1"></div>
      <div class="top-card">
        <div class="card-back">
          <div class="card-back-inner"></div>
        </div>
      </div>
    {:else}
      <div class="empty-library">
        <span>Empty</span>
      </div>
    {/if}
  </div>

  <div class="library-info">
    <span class="card-count">{cards.length}</span>
    <span class="label">Library</span>
  </div>

  {#if showMenu}
    <div class="context-menu">
      <button class="menu-item" onclick={handleShuffle}>
        Shuffle
      </button>
      <div class="menu-divider"></div>
      <div class="mill-controls">
        <span>Mill</span>
        <input
          type="number"
          min="1"
          max={cards.length}
          bind:value={millCount}
          onclick={(e) => e.stopPropagation()}
        />
        <button class="mill-btn" onclick={handleMill}>Go</button>
      </div>
    </div>
  {/if}
</div>

<style>
  .library-zone {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: hsl(var(--card));
    border: 2px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition: all var(--transition-fast);
    min-width: 120px;
  }

  .library-zone:hover {
    border-color: hsl(var(--primary) / 0.5);
    background: hsl(var(--card-hover));
  }

  .library-zone.drag-over {
    border-color: hsl(var(--primary));
    background: hsl(var(--primary) / 0.1);
  }

  .library-stack {
    position: relative;
    width: 90px;
    height: 126px;
  }

  .stack-layer {
    position: absolute;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: var(--radius-md);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .layer-3 {
    top: 6px;
    left: 3px;
    opacity: 0.4;
  }

  .layer-2 {
    top: 4px;
    left: 2px;
    opacity: 0.6;
  }

  .layer-1 {
    top: 2px;
    left: 1px;
    opacity: 0.8;
  }

  .top-card {
    position: absolute;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
  }

  .card-back {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: var(--radius-md);
    border: 1px solid rgba(255, 255, 255, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .card-back-inner {
    width: 70%;
    height: 80%;
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
    background: radial-gradient(ellipse at center, rgba(255, 215, 0, 0.15) 0%, transparent 70%);
  }

  .empty-library {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed hsl(var(--border));
    border-radius: var(--radius-md);
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
  }

  .library-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.125rem;
  }

  .card-count {
    font-size: 1.25rem;
    font-weight: 700;
    color: hsl(var(--primary));
  }

  .label {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .context-menu {
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-top: 0.5rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 100;
    min-width: 140px;
    overflow: hidden;
  }

  .menu-item {
    width: 100%;
    padding: 0.625rem 1rem;
    background: none;
    border: none;
    color: hsl(var(--foreground));
    text-align: left;
    cursor: pointer;
    font-size: 0.875rem;
    transition: background var(--transition-fast);
  }

  .menu-item:hover {
    background: hsl(var(--accent));
  }

  .menu-divider {
    height: 1px;
    background: hsl(var(--border));
  }

  .mill-controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    color: hsl(var(--foreground));
  }

  .mill-controls input {
    width: 40px;
    padding: 0.25rem;
    background: hsl(var(--background));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--foreground));
    text-align: center;
    font-size: 0.875rem;
  }

  .mill-btn {
    padding: 0.25rem 0.5rem;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .mill-btn:hover {
    opacity: 0.9;
  }
</style>
