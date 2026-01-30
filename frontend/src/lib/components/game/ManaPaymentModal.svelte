<script lang="ts">
  import type { GameCard, ManaPool } from "$lib/types";
  import {
    parseManaCost,
    canPayManaCost,
    type ManaColor,
    type ParsedManaCost,
  } from "../../../stores/gameStore";

  interface Props {
    card: GameCard;
    manaPool: ManaPool;
    onConfirm: (genericAllocation: Partial<ManaPool>) => void;
    onCancel: () => void;
  }

  let { card, manaPool, onConfirm, onCancel }: Props = $props();

  // Mana color display info
  const manaColorInfo: Record<ManaColor, { name: string; bg: string; text: string }> = {
    W: { name: "White", bg: "#f9faf4", text: "#1a1a1a" },
    U: { name: "Blue", bg: "#0e68ab", text: "#ffffff" },
    B: { name: "Black", bg: "#150b00", text: "#ffffff" },
    R: { name: "Red", bg: "#d3202a", text: "#ffffff" },
    G: { name: "Green", bg: "#00733e", text: "#ffffff" },
    C: { name: "Colorless", bg: "#888888", text: "#ffffff" },
  };

  // Parse cost
  const cost = $derived(parseManaCost(card.mana_cost));

  // Track generic mana allocation
  let genericPaymentAllocation = $state<ManaPool>({ W: 0, U: 0, B: 0, R: 0, G: 0, C: 0 });

  // Calculate remaining generic mana to allocate
  const genericRemaining = $derived.by(() => {
    const allocated = genericPaymentAllocation.W + genericPaymentAllocation.U +
                      genericPaymentAllocation.B + genericPaymentAllocation.R +
                      genericPaymentAllocation.G + genericPaymentAllocation.C;
    return cost.generic - allocated;
  });

  // Get available mana for generic payment (after colored costs)
  const availableForGeneric = $derived.by(() => {
    return {
      W: manaPool.W - cost.W,
      U: manaPool.U - cost.U,
      B: manaPool.B - cost.B,
      R: manaPool.R - cost.R,
      G: manaPool.G - cost.G,
      C: manaPool.C - cost.C,
    };
  });

  // Check if we can afford this card
  const canAfford = $derived(canPayManaCost(manaPool, cost));

  function adjustGenericPayment(color: ManaColor, delta: number) {
    const available = availableForGeneric[color];
    const current = genericPaymentAllocation[color];
    const newValue = Math.max(0, Math.min(available, current + delta));

    // Don't allow over-allocation
    if (delta > 0 && genericRemaining <= 0) return;

    genericPaymentAllocation = { ...genericPaymentAllocation, [color]: newValue };
  }

  function handleConfirm() {
    if (genericRemaining !== 0) return;
    onConfirm(genericPaymentAllocation);
  }

  function handleOverlayClick() {
    onCancel();
  }

  function handleModalClick(e: MouseEvent) {
    e.stopPropagation();
  }
</script>

<div class="modal-overlay" onclick={handleOverlayClick}>
  <div class="payment-modal" onclick={handleModalClick}>
    <h3>Pay Mana Cost</h3>
    <p class="modal-subtitle">Casting: {card.name}</p>
    <p class="mana-cost-display">{card.mana_cost || "Free"}</p>

    {#if !canAfford}
      <div class="cannot-afford">
        <p>Not enough mana to cast this spell</p>
        <button class="modal-cancel" onclick={onCancel}>Cancel</button>
      </div>
    {:else if cost.generic > 0}
      <div class="generic-payment-section">
        <p class="section-label">
          Pay {cost.generic} generic mana
          {#if genericRemaining > 0}
            <span class="remaining">({genericRemaining} remaining)</span>
          {/if}
        </p>
        <div class="generic-allocators">
          {#each (["W", "U", "B", "R", "G", "C"] as ManaColor[]) as color}
            {@const available = availableForGeneric[color]}
            {@const allocated = genericPaymentAllocation[color]}
            {#if available > 0}
              <div class="allocator">
                <button
                  class="alloc-btn minus"
                  onclick={() => adjustGenericPayment(color, -1)}
                  disabled={allocated === 0}
                >-</button>
                <div
                  class="alloc-pip"
                  style="background: {manaColorInfo[color].bg}; color: {manaColorInfo[color].text};"
                >
                  {allocated}/{available}
                </div>
                <button
                  class="alloc-btn plus"
                  onclick={() => adjustGenericPayment(color, 1)}
                  disabled={allocated >= available || genericRemaining === 0}
                >+</button>
              </div>
            {/if}
          {/each}
        </div>
      </div>

      <div class="payment-actions">
        <button
          class="confirm-payment"
          onclick={handleConfirm}
          disabled={genericRemaining !== 0}
        >
          Cast Spell
        </button>
        <button class="modal-cancel" onclick={onCancel}>Cancel</button>
      </div>
    {:else}
      <!-- Only colored mana required, auto-confirm -->
      <div class="payment-actions">
        <button class="confirm-payment" onclick={() => onConfirm({})}>
          Cast Spell
        </button>
        <button class="modal-cancel" onclick={onCancel}>Cancel</button>
      </div>
    {/if}
  </div>
</div>

<style>
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

  .payment-modal {
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    min-width: 340px;
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

  .payment-modal h3 {
    margin: 0 0 0.25rem 0;
    font-size: 1.25rem;
    color: hsl(var(--foreground));
  }

  .modal-subtitle {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
  }

  .mana-cost-display {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0.5rem 0 1.5rem;
    color: hsl(var(--foreground));
  }

  .cannot-afford {
    padding: 1rem;
  }

  .cannot-afford p {
    color: hsl(var(--destructive));
    font-weight: 500;
    margin-bottom: 1rem;
  }

  .generic-payment-section {
    margin-bottom: 1.5rem;
  }

  .section-label {
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
    margin-bottom: 0.75rem;
  }

  .section-label .remaining {
    color: hsl(var(--primary));
    font-weight: 600;
  }

  .generic-allocators {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.75rem;
  }

  .allocator {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .alloc-btn {
    width: 28px;
    height: 28px;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    background: hsl(var(--secondary));
    color: hsl(var(--foreground));
    font-size: 1rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .alloc-btn:hover:not(:disabled) {
    background: hsl(var(--accent));
  }

  .alloc-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .alloc-btn.minus:hover:not(:disabled) {
    background: hsl(var(--destructive));
    color: white;
  }

  .alloc-btn.plus:hover:not(:disabled) {
    background: hsl(142 76% 36%);
    color: white;
  }

  .alloc-pip {
    min-width: 50px;
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
    font-weight: 600;
    text-align: center;
  }

  .payment-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: center;
  }

  .confirm-payment {
    padding: 0.625rem 1.5rem;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border: none;
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .confirm-payment:hover:not(:disabled) {
    opacity: 0.9;
  }

  .confirm-payment:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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
</style>
