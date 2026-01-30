<script lang="ts">
  import type { GameCard, GameZone, GamePhase, ManaPool } from "$lib/types";
  import {
    gameStore,
    currentGame,
    currentPlayer,
    detectLandMana,
    parseManaCost,
    canPayManaCost,
    type ManaColor,
    type ParsedManaCost,
  } from "../../../stores/gameStore";
  import Library from "./Library.svelte";
  import Hand from "./Hand.svelte";
  import Battlefield from "./Battlefield.svelte";
  import Graveyard from "./Graveyard.svelte";
  import ExilePile from "./ExilePile.svelte";
  import GameCardComponent from "./GameCard.svelte";
  import ManaPaymentModal from "./ManaPaymentModal.svelte";

  interface Props {
    showControls?: boolean;
    showPhases?: boolean;
  }

  let { showControls = true, showPhases = true }: Props = $props();

  let selectedCard = $state<GameCard | null>(null);
  let contextMenuCard = $state<GameCard | null>(null);
  let contextMenuPosition = $state({ x: 0, y: 0 });
  let showContextMenu = $state(false);

  // Mana selection modal state (for tapping lands)
  let showManaModal = $state(false);
  let manaModalCard = $state<GameCard | null>(null);
  let manaModalColors = $state<ManaColor[]>([]);

  // Mana payment modal state (for playing cards)
  let showPaymentModal = $state(false);
  let paymentModalCard = $state<GameCard | null>(null);
  let paymentError = $state<string | null>(null);

  // Phase labels for display
  const phaseLabels: Record<GamePhase, string> = {
    untap: "Untap",
    upkeep: "Upkeep",
    draw: "Draw",
    main1: "Main 1",
    combat_begin: "Begin Combat",
    combat_attackers: "Declare Attackers",
    combat_blockers: "Declare Blockers",
    combat_damage: "Combat Damage",
    combat_end: "End Combat",
    main2: "Main 2",
    end: "End Step",
    cleanup: "Cleanup",
  };

  // Mana color display info
  const manaColorInfo: Record<ManaColor, { name: string; bg: string; text: string }> = {
    W: { name: "White", bg: "#f9faf4", text: "#1a1a1a" },
    U: { name: "Blue", bg: "#0e68ab", text: "#ffffff" },
    B: { name: "Black", bg: "#150b00", text: "#ffffff" },
    R: { name: "Red", bg: "#d3202a", text: "#ffffff" },
    G: { name: "Green", bg: "#00733e", text: "#ffffff" },
    C: { name: "Colorless", bg: "#888888", text: "#ffffff" },
  };

  // Calculate total mana in pool
  const totalMana = $derived.by(() => {
    if (!$currentPlayer?.manaPool) return 0;
    const pool = $currentPlayer.manaPool;
    return pool.W + pool.U + pool.B + pool.R + pool.G + pool.C;
  });

  function handleCardClick(card: GameCard) {
    selectedCard = card;
    gameStore.selectCard(card);
  }

  function handleCardDoubleClick(card: GameCard) {
    // Double-click to play card from hand
    if (card.zone === "hand") {
      tryPlayCard(card);
    } else if (card.zone === "battlefield") {
      const typeLine = card.type_line.toLowerCase();

      // Check if it's a land
      if (typeLine.includes("land")) {
        if (card.isTapped) {
          // Already tapped, just untap
          gameStore.toggleTap(card.instanceId);
        } else {
          // Tap for mana
          const colors = detectLandMana(card);
          if (colors.length === 1) {
            // Single color, tap directly
            gameStore.tapLandForMana(card.instanceId, colors[0]);
          } else if (colors.length > 1) {
            // Multiple colors, show modal
            manaModalCard = card;
            manaModalColors = colors;
            showManaModal = true;
          } else {
            // Unknown, just tap without adding mana
            gameStore.toggleTap(card.instanceId);
          }
        }
      } else {
        // Non-land, just tap/untap
        gameStore.toggleTap(card.instanceId);
      }
    }
  }

  function selectManaColor(color: ManaColor) {
    if (manaModalCard) {
      gameStore.tapLandForMana(manaModalCard.instanceId, color);
    }
    closeManaModal();
  }

  function closeManaModal() {
    showManaModal = false;
    manaModalCard = null;
    manaModalColors = [];
  }

  // Try to play a card from hand, handling mana payment
  function tryPlayCard(card: GameCard) {
    const isLand = card.type_line.toLowerCase().includes("land");

    // Lands are free to play
    if (isLand) {
      gameStore.playCard(card.instanceId);
      return;
    }

    // Free spells (0 mana cost)
    const cost = parseManaCost(card.mana_cost);
    if (cost.total === 0) {
      gameStore.playCard(card.instanceId);
      return;
    }

    // Use the reusable payment initiation
    initiatePayment(card);
  }

  // Handle mana payment confirmation from modal
  function handlePaymentConfirm(genericAllocation: Partial<ManaPool>) {
    if (!paymentModalCard) return;

    const result = gameStore.playCardWithMana(
      paymentModalCard.instanceId,
      genericAllocation
    );

    if (!result.success) {
      paymentError = result.error || "Failed to play card";
      setTimeout(() => { paymentError = null; }, 2000);
    }

    closePaymentModal();
  }

  function closePaymentModal() {
    showPaymentModal = false;
    paymentModalCard = null;
  }

  // Check if a card requires mana payment (not a land and has a cost)
  function requiresManaPayment(card: GameCard): boolean {
    const isLand = card.type_line.toLowerCase().includes("land");
    if (isLand) return false;
    const cost = parseManaCost(card.mana_cost);
    return cost.total > 0;
  }

  // Initiate mana payment for a card (shows modal or auto-pays)
  function initiatePayment(card: GameCard) {
    if (!$currentPlayer) return;

    const cost = parseManaCost(card.mana_cost);

    // Check if we can afford it
    if (!canPayManaCost($currentPlayer.manaPool, cost)) {
      paymentError = "Not enough mana to cast this spell";
      setTimeout(() => { paymentError = null; }, 2000);
      return;
    }

    // If no generic mana, or exact mana available, we can auto-pay
    if (cost.generic === 0) {
      const result = gameStore.playCardWithMana(card.instanceId);
      if (!result.success) {
        paymentError = result.error || "Failed to play card";
        setTimeout(() => { paymentError = null; }, 2000);
      }
      return;
    }

    // Calculate available mana after paying colored costs
    const pool = $currentPlayer.manaPool;
    const remainingPool: ManaPool = {
      W: pool.W - cost.W,
      U: pool.U - cost.U,
      B: pool.B - cost.B,
      R: pool.R - cost.R,
      G: pool.G - cost.G,
      C: pool.C - cost.C,
    };

    // Count how many colors have remaining mana
    const colorsWithMana = (["W", "U", "B", "R", "G", "C"] as ManaColor[])
      .filter((c) => remainingPool[c] > 0);
    const totalRemaining = colorsWithMana.reduce((sum, c) => sum + remainingPool[c], 0);

    // If only one color has enough, or total equals generic cost exactly, auto-pay
    if (totalRemaining === cost.generic || colorsWithMana.length <= 1) {
      const result = gameStore.playCardWithMana(card.instanceId);
      if (!result.success) {
        paymentError = result.error || "Failed to play card";
        setTimeout(() => { paymentError = null; }, 2000);
      }
      return;
    }

    // Multiple colors available - show modal
    paymentModalCard = card;
    showPaymentModal = true;
  }

  function handleCardContextMenu(card: GameCard, event: MouseEvent) {
    contextMenuCard = card;
    contextMenuPosition = { x: event.clientX, y: event.clientY };
    showContextMenu = true;
  }

  function closeContextMenu() {
    showContextMenu = false;
    contextMenuCard = null;
  }

  function moveCardTo(zone: GameZone) {
    if (!contextMenuCard) {
      closeContextMenu();
      return;
    }

    // If moving from hand to battlefield, trigger mana payment
    if (zone === "battlefield" && contextMenuCard.zone === "hand") {
      const card = contextMenuCard;
      closeContextMenu();
      tryPlayCard(card);
      return;
    }

    gameStore.moveCard(contextMenuCard.instanceId, zone);
    closeContextMenu();
  }

  function handleTapForMana(color: ManaColor) {
    if (contextMenuCard) {
      gameStore.tapLandForMana(contextMenuCard.instanceId, color);
    }
    closeContextMenu();
  }

  function handleDrawCard() {
    gameStore.drawCard();
  }

  function handleShuffleLibrary() {
    gameStore.shuffleLibrary();
  }

  function handleMill(count: number) {
    gameStore.mill(count);
  }

  function handleCardDropOnBattlefield(card: GameCard) {
    if (card.zone === "battlefield") return;

    // Cards from hand need to pay mana costs (except lands)
    if (card.zone === "hand") {
      tryPlayCard(card);
      return;
    }

    // Cards from other zones can be moved directly (e.g., reanimation effects)
    gameStore.moveCard(card.instanceId, "battlefield");
  }

  function handleCardDropOnGraveyard(card: GameCard) {
    if (card.zone !== "graveyard") {
      gameStore.moveCard(card.instanceId, "graveyard");
    }
  }

  function handleCardDropOnExile(card: GameCard) {
    if (card.zone !== "exile") {
      gameStore.moveCard(card.instanceId, "exile");
    }
  }

  function handleCardDropOnLibrary(card: GameCard) {
    if (card.zone !== "library") {
      gameStore.moveCard(card.instanceId, "library");
      gameStore.shuffleLibrary();
    }
  }

  function handleLifeChange(amount: number) {
    gameStore.updateLife(amount);
  }

  function handleUntapAll() {
    gameStore.untapAll();
  }

  function handleNextTurn() {
    gameStore.untapAll();
    gameStore.clearManaPool();
    gameStore.nextTurn();
    gameStore.drawCard();
  }

  function handleSetPhase(phase: GamePhase) {
    gameStore.setPhase(phase);
  }

  function handleClearMana() {
    gameStore.clearManaPool();
  }

  function handleRemoveMana(color: ManaColor) {
    gameStore.removeMana(color);
  }

  // Get mana colors for context menu if card is a land
  function getLandManaColors(card: GameCard): ManaColor[] {
    if (!card.type_line.toLowerCase().includes("land")) return [];
    return detectLandMana(card);
  }

  // Close context menu when clicking outside
  function handleGlobalClick() {
    if (showContextMenu) {
      closeContextMenu();
    }
    if (showManaModal) {
      closeManaModal();
    }
  }
</script>

<svelte:window onclick={handleGlobalClick} />

{#if $currentGame && $currentPlayer}
  <div class="game-board">
    <!-- Top bar with game info and life tracker -->
    {#if showControls}
      <div class="game-header">
        <div class="game-info">
          <span class="deck-name">{$currentGame.deckName}</span>
          <span class="format-badge">{$currentGame.format}</span>
          <span class="turn-counter">Turn {$currentGame.turnNumber}</span>
        </div>

        <div class="life-tracker">
          <button class="life-btn minus" onclick={() => handleLifeChange(-1)}>−</button>
          <span class="life-total">{$currentPlayer.life}</span>
          <button class="life-btn plus" onclick={() => handleLifeChange(1)}>+</button>
        </div>

        <!-- Mana Pool Display -->
        <div class="mana-pool">
          <span class="mana-label">Mana:</span>
          <div class="mana-symbols">
            {#each (["W", "U", "B", "R", "G", "C"] as ManaColor[]) as color}
              {@const count = $currentPlayer.manaPool[color]}
              {#if count > 0}
                <button
                  class="mana-pip"
                  style="background: {manaColorInfo[color].bg}; color: {manaColorInfo[color].text};"
                  onclick={() => handleRemoveMana(color)}
                  title="Click to spend 1 {manaColorInfo[color].name} mana"
                >
                  {count}
                </button>
              {/if}
            {/each}
            {#if totalMana === 0}
              <span class="no-mana">Empty</span>
            {/if}
          </div>
          {#if totalMana > 0}
            <button class="clear-mana-btn" onclick={handleClearMana} title="Clear mana pool">
              Clear
            </button>
          {/if}
        </div>

        <div class="game-actions">
          <button class="action-btn" onclick={handleDrawCard}>Draw</button>
          <button class="action-btn" onclick={handleUntapAll}>Untap All</button>
          <button class="action-btn primary" onclick={handleNextTurn}>Next Turn</button>
        </div>
      </div>
    {/if}

    <!-- Phase tracker -->
    {#if showPhases && $currentGame.started}
      <div class="phase-tracker">
        {#each Object.entries(phaseLabels) as [phase, label] (phase)}
          <button
            class="phase-btn"
            class:active={$currentGame.phase === phase}
            onclick={() => handleSetPhase(phase as GamePhase)}
          >
            {label}
          </button>
        {/each}
      </div>
    {/if}

    <!-- Main game area -->
    <div class="game-area">
      <!-- Left sidebar with library and zones -->
      <div class="left-zones">
        <Library
          cards={$currentPlayer.library}
          onDraw={handleDrawCard}
          onShuffle={handleShuffleLibrary}
          onMill={handleMill}
          onCardDrop={handleCardDropOnLibrary}
        />

        <!-- Command zone for commanders -->
        {#if $currentPlayer.command.length > 0}
          <div class="command-zone">
            <div class="zone-label">Command</div>
            <div class="command-cards">
              {#each $currentPlayer.command as card (card.instanceId)}
                <GameCardComponent
                  {card}
                  size="small"
                  onclick={handleCardClick}
                  ondblclick={handleCardDoubleClick}
                  oncontextmenu={handleCardContextMenu}
                />
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <!-- Center with battlefield -->
      <div class="center-area">
        <Battlefield
          cards={$currentPlayer.battlefield}
          onCardClick={handleCardClick}
          onCardDoubleClick={handleCardDoubleClick}
          onCardContextMenu={handleCardContextMenu}
          onCardDrop={handleCardDropOnBattlefield}
        />
      </div>

      <!-- Right sidebar with graveyard and exile -->
      <div class="right-zones">
        <Graveyard
          cards={$currentPlayer.graveyard}
          onCardClick={handleCardClick}
          onCardContextMenu={handleCardContextMenu}
          onCardDrop={handleCardDropOnGraveyard}
        />

        <ExilePile
          cards={$currentPlayer.exile}
          onCardClick={handleCardClick}
          onCardContextMenu={handleCardContextMenu}
          onCardDrop={handleCardDropOnExile}
        />
      </div>
    </div>

    <!-- Bottom with hand -->
    <Hand
      cards={$currentPlayer.hand}
      onCardClick={handleCardClick}
      onCardDoubleClick={handleCardDoubleClick}
      onCardContextMenu={handleCardContextMenu}
    />

    <!-- Card preview panel -->
    {#if selectedCard}
      <div class="card-preview-panel">
        <button class="close-preview" onclick={() => (selectedCard = null)}>×</button>
        <div class="preview-image">
          <img src={selectedCard.image_uri} alt={selectedCard.name} />
        </div>
        <div class="preview-info">
          <h3>{selectedCard.name}</h3>
          <p class="type-line">{selectedCard.type_line}</p>
          {#if selectedCard.oracle_text}
            <p class="oracle-text">{selectedCard.oracle_text}</p>
          {/if}
          {#if selectedCard.power && selectedCard.toughness}
            <p class="pt">{selectedCard.power}/{selectedCard.toughness}</p>
          {/if}
        </div>
      </div>
    {/if}

    <!-- Context menu -->
    {#if showContextMenu && contextMenuCard}
      {@const landColors = getLandManaColors(contextMenuCard)}
      <div
        class="context-menu"
        style="left: {contextMenuPosition.x}px; top: {contextMenuPosition.y}px;"
        onclick={(e) => e.stopPropagation()}
      >
        <button class="menu-item" onclick={() => moveCardTo("hand")}>
          Return to Hand
        </button>
        <button class="menu-item" onclick={() => moveCardTo("battlefield")}>
          Put on Battlefield
        </button>
        <button class="menu-item" onclick={() => moveCardTo("graveyard")}>
          Send to Graveyard
        </button>
        <button class="menu-item" onclick={() => moveCardTo("exile")}>
          Exile
        </button>
        <button class="menu-item" onclick={() => moveCardTo("library")}>
          Put on Library (shuffle)
        </button>
        <div class="menu-divider"></div>
        {#if contextMenuCard.zone === "battlefield"}
          <button
            class="menu-item"
            onclick={() => {
              gameStore.toggleTap(contextMenuCard!.instanceId);
              closeContextMenu();
            }}
          >
            {contextMenuCard.isTapped ? "Untap" : "Tap"}
          </button>

          <!-- Land mana tapping options -->
          {#if landColors.length > 0 && !contextMenuCard.isTapped}
            <div class="menu-divider"></div>
            <div class="menu-label">Tap for Mana</div>
            <div class="mana-options">
              {#each landColors as color}
                <button
                  class="mana-option"
                  style="background: {manaColorInfo[color].bg}; color: {manaColorInfo[color].text};"
                  onclick={() => handleTapForMana(color)}
                >
                  {color}
                </button>
              {/each}
            </div>
          {/if}

          <div class="menu-divider"></div>
          <button
            class="menu-item"
            onclick={() => {
              gameStore.addCounter(contextMenuCard!.instanceId, "+1/+1");
              closeContextMenu();
            }}
          >
            Add +1/+1 Counter
          </button>
        {/if}
      </div>
    {/if}

    <!-- Mana Selection Modal -->
    {#if showManaModal && manaModalCard}
      <div class="modal-overlay" onclick={closeManaModal}>
        <div class="mana-modal" onclick={(e) => e.stopPropagation()}>
          <h3>Select Mana Color</h3>
          <p class="modal-subtitle">Tapping: {manaModalCard.name}</p>
          <div class="mana-choices">
            {#each manaModalColors as color}
              <button
                class="mana-choice"
                style="background: {manaColorInfo[color].bg}; color: {manaColorInfo[color].text};"
                onclick={() => selectManaColor(color)}
              >
                <span class="mana-letter">{color}</span>
                <span class="mana-name">{manaColorInfo[color].name}</span>
              </button>
            {/each}
          </div>
          <button class="modal-cancel" onclick={closeManaModal}>Cancel</button>
        </div>
      </div>
    {/if}

    <!-- Mana Payment Modal (for casting spells) -->
    {#if showPaymentModal && paymentModalCard && $currentPlayer}
      <ManaPaymentModal
        card={paymentModalCard}
        manaPool={$currentPlayer.manaPool}
        onConfirm={handlePaymentConfirm}
        onCancel={closePaymentModal}
      />
    {/if}

    <!-- Payment Error Toast -->
    {#if paymentError}
      <div class="payment-error-toast">
        {paymentError}
      </div>
    {/if}
  </div>
{:else}
  <div class="no-game">
    <p>No game in progress. Select a deck to start.</p>
  </div>
{/if}

<style>
  .game-board {
    display: flex;
    flex-direction: column;
    height: 100%;
    gap: 1rem;
    padding: 1rem;
    background: hsl(var(--background));
  }

  .game-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    flex-wrap: wrap;
    gap: 1rem;
  }

  .game-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .deck-name {
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .format-badge {
    padding: 0.25rem 0.5rem;
    background: hsl(var(--primary) / 0.1);
    color: hsl(var(--primary));
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
  }

  .turn-counter {
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
  }

  .life-tracker {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: hsl(var(--background));
    padding: 0.25rem;
    border-radius: var(--radius-md);
  }

  .life-btn {
    width: 36px;
    height: 36px;
    border: none;
    border-radius: var(--radius-sm);
    background: hsl(var(--secondary));
    color: hsl(var(--foreground));
    font-size: 1.25rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .life-btn:hover {
    background: hsl(var(--accent));
  }

  .life-btn.minus:hover {
    background: hsl(var(--destructive));
    color: white;
  }

  .life-btn.plus:hover {
    background: hsl(142 76% 36%);
    color: white;
  }

  .life-total {
    min-width: 50px;
    text-align: center;
    font-size: 1.5rem;
    font-weight: 700;
    color: hsl(var(--foreground));
  }

  /* Mana Pool Display */
  .mana-pool {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.75rem;
    background: hsl(var(--background));
    border-radius: var(--radius-md);
    border: 1px solid hsl(var(--border));
  }

  .mana-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
  }

  .mana-symbols {
    display: flex;
    gap: 0.25rem;
    align-items: center;
  }

  .mana-pip {
    min-width: 28px;
    height: 28px;
    border: none;
    border-radius: 50%;
    font-size: 0.875rem;
    font-weight: 700;
    cursor: pointer;
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .mana-pip:hover {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .no-mana {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    font-style: italic;
  }

  .clear-mana-btn {
    padding: 0.25rem 0.5rem;
    background: hsl(var(--secondary));
    border: none;
    border-radius: var(--radius-sm);
    font-size: 0.7rem;
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .clear-mana-btn:hover {
    background: hsl(var(--destructive));
    color: white;
  }

  .game-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-btn {
    padding: 0.5rem 1rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--foreground));
    font-size: 0.875rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .action-btn:hover {
    background: hsl(var(--accent));
  }

  .action-btn.primary {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border-color: hsl(var(--primary));
  }

  .action-btn.primary:hover {
    opacity: 0.9;
  }

  .phase-tracker {
    display: flex;
    gap: 0.25rem;
    padding: 0.5rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    overflow-x: auto;
  }

  .phase-btn {
    padding: 0.375rem 0.625rem;
    background: transparent;
    border: none;
    border-radius: var(--radius-sm);
    color: hsl(var(--muted-foreground));
    font-size: 0.75rem;
    cursor: pointer;
    white-space: nowrap;
    transition: all var(--transition-fast);
  }

  .phase-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .phase-btn.active {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
  }

  .game-area {
    display: flex;
    gap: 1rem;
    flex: 1;
    min-height: 0;
  }

  .left-zones,
  .right-zones {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    flex-shrink: 0;
  }

  .center-area {
    flex: 1;
    min-width: 0;
  }

  .command-zone {
    background: hsl(var(--card));
    border: 2px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    padding: 0.75rem;
  }

  .zone-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
  }

  .command-cards {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .card-preview-panel {
    position: fixed;
    top: 1rem;
    right: 1rem;
    width: 280px;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    z-index: 100;
    overflow: hidden;
  }

  .close-preview {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    width: 28px;
    height: 28px;
    border: none;
    border-radius: 50%;
    background: hsl(var(--background) / 0.8);
    color: hsl(var(--foreground));
    font-size: 1.25rem;
    cursor: pointer;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-preview:hover {
    background: hsl(var(--destructive));
    color: white;
  }

  .preview-image img {
    width: 100%;
    display: block;
  }

  .preview-info {
    padding: 1rem;
  }

  .preview-info h3 {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    color: hsl(var(--foreground));
  }

  .type-line {
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    margin: 0 0 0.5rem 0;
  }

  .oracle-text {
    font-size: 0.8rem;
    line-height: 1.5;
    color: hsl(var(--foreground));
    margin: 0 0 0.5rem 0;
    white-space: pre-wrap;
  }

  .pt {
    font-weight: 700;
    color: hsl(var(--primary));
    margin: 0;
  }

  .context-menu {
    position: fixed;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    z-index: 200;
    min-width: 180px;
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
    margin: 0.25rem 0;
  }

  .menu-label {
    padding: 0.375rem 1rem;
    font-size: 0.7rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
  }

  .mana-options {
    display: flex;
    gap: 0.375rem;
    padding: 0.375rem 1rem 0.625rem;
  }

  .mana-option {
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 50%;
    font-size: 0.875rem;
    font-weight: 700;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .mana-option:hover {
    transform: scale(1.15);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  /* Mana Selection Modal */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 300;
    animation: fadeIn 0.15s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .mana-modal {
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    min-width: 300px;
    text-align: center;
    animation: slideUp 0.2s ease-out;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .mana-modal h3 {
    margin: 0 0 0.25rem 0;
    font-size: 1.25rem;
    color: hsl(var(--foreground));
  }

  .modal-subtitle {
    margin: 0 0 1.5rem 0;
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
  }

  .mana-choices {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  .mana-choice {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.375rem;
    padding: 1rem 1.25rem;
    border: 2px solid transparent;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .mana-choice:hover {
    transform: scale(1.05);
    border-color: rgba(255, 255, 255, 0.3);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  }

  .mana-letter {
    font-size: 1.5rem;
    font-weight: 700;
  }

  .mana-name {
    font-size: 0.75rem;
    font-weight: 500;
    opacity: 0.9;
  }

  .modal-cancel {
    padding: 0.5rem 1.5rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .modal-cancel:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  /* Payment Error Toast */
  .payment-error-toast {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    padding: 0.75rem 1.5rem;
    background: hsl(var(--destructive));
    color: white;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    font-weight: 500;
    box-shadow: var(--shadow-lg);
    z-index: 400;
    animation: toastIn 0.2s ease-out;
  }

  @keyframes toastIn {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }

  .no-game {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: hsl(var(--muted-foreground));
    font-size: 1rem;
  }

  @media (max-width: 900px) {
    .game-area {
      flex-direction: column;
    }

    .left-zones,
    .right-zones {
      flex-direction: row;
      flex-wrap: wrap;
      justify-content: center;
    }

    .mana-pool {
      flex-wrap: wrap;
    }
  }
</style>
