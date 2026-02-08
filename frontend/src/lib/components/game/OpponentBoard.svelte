<script lang="ts">
  import type { GameCard, PlayerState } from "$lib/types";
  import GameCardComponent from "./GameCard.svelte";

  interface Props {
    player: PlayerState;
    isActivePlayer?: boolean;
    onCardClick?: (card: GameCard) => void;
  }

  let { player, isActivePlayer = false, onCardClick }: Props = $props();

  // Group battlefield cards by type
  const battlefieldGroups = $derived.by(() => {
    const groups: Record<string, GameCard[]> = {
      Creatures: [],
      Lands: [],
      Other: [],
    };
    for (const card of player.battlefield) {
      const type = card.type_line.toLowerCase();
      if (type.includes("creature")) groups["Creatures"].push(card);
      else if (type.includes("land")) groups["Lands"].push(card);
      else groups["Other"].push(card);
    }
    return groups;
  });

  const handCount = $derived((player as any).hand_count ?? player.hand?.length ?? 0);
  const libraryCount = $derived((player as any).library_count ?? player.library?.length ?? 0);
</script>

<div class="opponent-board" class:active-turn={isActivePlayer}>
  <div class="opponent-header">
    <span class="opponent-name">{player.name}</span>
    {#if isActivePlayer}
      <span class="turn-indicator">Active</span>
    {/if}
    <div class="opponent-life">
      <span class="life-value">{player.life}</span>
      <span class="life-label">life</span>
    </div>
    <div class="opponent-counts">
      <span class="count-badge" title="Cards in hand">H: {handCount}</span>
      <span class="count-badge" title="Cards in library">L: {libraryCount}</span>
      {#if player.graveyard.length > 0}
        <span class="count-badge gy" title="Cards in graveyard">GY: {player.graveyard.length}</span>
      {/if}
      {#if player.exile.length > 0}
        <span class="count-badge ex" title="Cards in exile">EX: {player.exile.length}</span>
      {/if}
    </div>
    {#if player.poison > 0}
      <span class="poison-badge">{player.poison} poison</span>
    {/if}
  </div>

  <!-- Commander zone -->
  {#if player.command.length > 0}
    <div class="opponent-command">
      {#each player.command as card (card.instanceId)}
        <GameCardComponent
          {card}
          size="small"
          onclick={onCardClick}
        />
      {/each}
    </div>
  {/if}

  <!-- Battlefield -->
  <div class="opponent-battlefield">
    {#each Object.entries(battlefieldGroups) as [groupName, cards] (groupName)}
      {#if cards.length > 0}
        <div class="card-group">
          <span class="group-label">{groupName} ({cards.length})</span>
          <div class="group-cards">
            {#each cards as card (card.instanceId)}
              <GameCardComponent
                {card}
                size="small"
                onclick={onCardClick}
              />
            {/each}
          </div>
        </div>
      {/if}
    {/each}
    {#if player.battlefield.length === 0}
      <span class="empty-battlefield">No permanents</span>
    {/if}
  </div>
</div>

<style>
  .opponent-board {
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    padding: 0.75rem;
    min-width: 300px;
    flex: 1;
    overflow-y: auto;
  }

  .opponent-board.active-turn {
    border-color: hsl(var(--primary));
    box-shadow: 0 0 0 1px hsl(var(--primary) / 0.3);
  }

  .opponent-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
  }

  .opponent-name {
    font-weight: 600;
    font-size: 0.875rem;
    color: hsl(var(--foreground));
  }

  .turn-indicator {
    padding: 0.125rem 0.375rem;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border-radius: var(--radius-sm);
    font-size: 0.625rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .opponent-life {
    display: flex;
    align-items: baseline;
    gap: 0.25rem;
    margin-left: auto;
  }

  .life-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: hsl(var(--foreground));
  }

  .life-label {
    font-size: 0.625rem;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
  }

  .opponent-counts {
    display: flex;
    gap: 0.375rem;
  }

  .count-badge {
    padding: 0.125rem 0.375rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-sm);
    font-size: 0.6875rem;
    font-weight: 500;
    color: hsl(var(--muted-foreground));
  }

  .count-badge.gy {
    color: hsl(var(--destructive));
  }

  .count-badge.ex {
    color: hsl(210 40% 60%);
  }

  .poison-badge {
    padding: 0.125rem 0.375rem;
    background: hsl(120 50% 20%);
    color: hsl(120 80% 70%);
    border-radius: var(--radius-sm);
    font-size: 0.6875rem;
    font-weight: 600;
  }

  .opponent-command {
    display: flex;
    gap: 0.25rem;
    margin-bottom: 0.5rem;
  }

  .opponent-battlefield {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    min-height: 60px;
  }

  .card-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .group-label {
    font-size: 0.5625rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .group-cards {
    display: flex;
    gap: 0.125rem;
    flex-wrap: wrap;
  }

  .empty-battlefield {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    font-style: italic;
    padding: 0.5rem;
  }
</style>
