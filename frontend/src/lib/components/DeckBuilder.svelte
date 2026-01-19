<script lang="ts">
  import { deckStore } from '../../stores/deckStore';
  import type { ScryfallCard, CardInDeck, CardZone, DisplayMode, PileSortBy } from '$lib/types';
  import DeckStats from './DeckStats.svelte';
  import CardPreview from './CardPreview.svelte';
  import ResizeHandle from './ResizeHandle.svelte';

  interface Props {
    onBack: () => void;
  }

  let { onBack }: Props = $props();

  let currentDeck = $derived($deckStore.currentDeck);
  let displayMode = $derived($deckStore.displayMode);
  let pileSortBy = $derived($deckStore.pileSortBy);
  let selectedZone = $derived($deckStore.selectedZone);
  
  let searchQuery = $state('');
  let searchResults = $state<ScryfallCard[]>([]);
  let isSearching = $state(false);
  let searchTimeout: ReturnType<typeof setTimeout>;
  let selectedCard = $state<CardInDeck | null>(null);
  let showStats = $state(true);
  let draggedCard = $state<CardInDeck | null>(null);

  // Resizable panel widths
  let searchPanelWidth = $state(320);
  let rightPanelWidth = $state(280);

  const MIN_PANEL_WIDTH = 200;
  const MAX_PANEL_WIDTH = 500;

  function handleSearchPanelResize(delta: number): void {
    searchPanelWidth = Math.max(MIN_PANEL_WIDTH, Math.min(MAX_PANEL_WIDTH, searchPanelWidth + delta));
  }

  function handleRightPanelResize(delta: number): void {
    rightPanelWidth = Math.max(MIN_PANEL_WIDTH, Math.min(MAX_PANEL_WIDTH, rightPanelWidth - delta));
  }

  const zones: { id: CardZone; label: string; icon: string }[] = [
    { id: 'mainboard', label: 'Mainboard', icon: '▤' },
    { id: 'sideboard', label: 'Sideboard', icon: '▦' },
    { id: 'maybeboard', label: 'Maybeboard', icon: '▧' },
    { id: 'considering', label: 'Considering', icon: '▨' },
    { id: 'commander', label: 'Commander', icon: '★' },
  ];

  const displayModes: { id: DisplayMode; label: string; icon: string }[] = [
    { id: 'list', label: 'List', icon: '≡' },
    { id: 'grid', label: 'Grid', icon: '⊞' },
    { id: 'pile', label: 'Pile', icon: '▥' },
  ];

  const pileSortOptions: { id: PileSortBy; label: string }[] = [
    { id: 'cmc', label: 'CMC' },
    { id: 'type', label: 'Type' },
    { id: 'color', label: 'Color' },
    { id: 'rarity', label: 'Rarity' },
  ];

  async function searchCards(): Promise<void> {
    if (searchQuery.length < 2) {
      searchResults = [];
      return;
    }

    isSearching = true;
    try {
      const response = await fetch(
        `https://api.scryfall.com/cards/search?q=${encodeURIComponent(searchQuery)}`
      );
      if (response.ok) {
        const data = await response.json();
        searchResults = data.data || [];
      } else {
        searchResults = [];
      }
    } catch {
      searchResults = [];
    } finally {
      isSearching = false;
    }
  }

  function handleSearchInput(): void {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(searchCards, 300);
  }

  function addCardToDeck(card: ScryfallCard, zone: CardZone = selectedZone): void {
    const cardInDeck: Omit<CardInDeck, 'quantity' | 'zone' | 'tags'> = {
      id: card.id,
      name: card.name,
      mana_cost: card.mana_cost,
      cmc: card.cmc,
      type_line: card.type_line,
      colors: card.colors,
      rarity: card.rarity,
      image_uri: card.image_uris?.normal || card.card_faces?.[0]?.image_uris?.normal,
    };
    deckStore.addCard(cardInDeck, 1, zone, []);
  }

  function removeCard(cardId: string, zone: CardZone): void {
    deckStore.removeCard(cardId, zone);
    if (selectedCard?.id === cardId) {
      selectedCard = null;
    }
  }

  function updateQuantity(cardId: string, quantity: number, zone: CardZone): void {
    deckStore.updateCardQuantity(cardId, quantity, zone);
  }

  function selectCard(card: CardInDeck): void {
    selectedCard = card;
  }

  function getCardsInZone(zone: CardZone): CardInDeck[] {
    return currentDeck?.cards.filter(c => c.zone === zone) || [];
  }

  function getZoneCount(zone: CardZone): number {
    return getCardsInZone(zone).reduce((sum, c) => sum + c.quantity, 0);
  }

  function getTotalCards(): number {
    return currentDeck?.cards.reduce((sum, c) => sum + c.quantity, 0) || 0;
  }

  function setDisplayMode(mode: DisplayMode): void {
    deckStore.setDisplayMode(mode);
  }

  function setPileSortBy(sort: PileSortBy): void {
    deckStore.setPileSortBy(sort);
  }

  function setSelectedZone(zone: CardZone): void {
    deckStore.setSelectedZone(zone);
  }

  // Pile view grouping
  function getCardPiles(): Map<string, CardInDeck[]> {
    const cards = getCardsInZone(selectedZone);
    const piles = new Map<string, CardInDeck[]>();

    cards.forEach(card => {
      let key: string;
      switch (pileSortBy) {
        case 'cmc':
          key = card.cmc >= 7 ? '7+' : card.cmc.toString();
          break;
        case 'type':
          key = card.type_line.split('—')[0].trim().split(' ').pop() || 'Other';
          break;
        case 'color':
          if (!card.colors || card.colors.length === 0) {
            key = 'Colorless';
          } else if (card.colors.length > 1) {
            key = 'Multicolor';
          } else {
            const colorMap: Record<string, string> = { W: 'White', U: 'Blue', B: 'Black', R: 'Red', G: 'Green' };
            key = colorMap[card.colors[0]] || 'Other';
          }
          break;
        case 'rarity':
          key = card.rarity.charAt(0).toUpperCase() + card.rarity.slice(1);
          break;
        default:
          key = 'Other';
      }

      if (!piles.has(key)) {
        piles.set(key, []);
      }
      piles.get(key)!.push(card);
    });

    return piles;
  }

  // Drag and drop handlers
  function handleDragStart(e: DragEvent, card: CardInDeck): void {
    draggedCard = card;
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', card.id);
    }
  }

  function handleDragOver(e: DragEvent): void {
    e.preventDefault();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'move';
    }
  }

  function handleDrop(e: DragEvent, targetZone: CardZone): void {
    e.preventDefault();
    if (draggedCard && draggedCard.zone !== targetZone) {
      deckStore.moveCardToZone(draggedCard.id, draggedCard.zone, targetZone);
    }
    draggedCard = null;
  }

  function handleDragEnd(): void {
    draggedCard = null;
  }

  // Sort piles for display
  function getSortedPileKeys(piles: Map<string, CardInDeck[]>): string[] {
    const keys = Array.from(piles.keys());
    if (pileSortBy === 'cmc') {
      return keys.sort((a, b) => {
        const aNum = a === '7+' ? 7 : parseInt(a);
        const bNum = b === '7+' ? 7 : parseInt(b);
        return aNum - bNum;
      });
    }
    return keys.sort();
  }
</script>

<div class="deck-builder">
  <header class="builder-header">
    <div class="header-left">
      <button class="back-btn" onclick={onBack}>← Back</button>
      <div class="deck-info">
        <h1>{currentDeck?.name || 'Deck Builder'}</h1>
        <span class="deck-format">{currentDeck?.format}</span>
      </div>
    </div>
    <div class="header-right">
      <span class="card-count">{getTotalCards()} cards</span>
      <button 
        class="stats-toggle"
        class:active={showStats}
        onclick={() => showStats = !showStats}
      >
        📊 Stats
      </button>
    </div>
  </header>

  <div class="builder-content">
    <!-- Card Search Panel -->
    <aside class="search-panel" style="width: {searchPanelWidth}px">
      <div class="panel-header">
        <h2>Add Cards</h2>
      </div>
      
      <div class="search-input-wrapper">
        <input
          type="text"
          placeholder="Search for cards..."
          bind:value={searchQuery}
          oninput={handleSearchInput}
        />
        {#if isSearching}
          <span class="search-spinner">⟳</span>
        {/if}
      </div>

      <div class="add-to-zone">
        <span class="label">Add to:</span>
        <select bind:value={selectedZone} onchange={(e) => setSelectedZone(e.currentTarget.value as CardZone)}>
          {#each zones.filter(z => z.id !== 'commander') as zone}
            <option value={zone.id}>{zone.label}</option>
          {/each}
        </select>
      </div>

      <div class="search-results">
        {#if searchResults.length > 0}
          {#each searchResults as card}
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div 
              class="search-card"
              draggable="true"
              role="listitem"
              ondragstart={(e) => handleDragStart(e, { ...card, quantity: 1, zone: 'mainboard', tags: [] } as CardInDeck)}
            >
              <img
                src={card.image_uris?.small || card.card_faces?.[0]?.image_uris?.small || ''}
                alt={card.name}
                loading="lazy"
              />
              <div class="card-info">
                <span class="card-name">{card.name}</span>
                <span class="card-type">{card.type_line}</span>
                <span class="card-mana">{card.mana_cost || ''}</span>
              </div>
              <button class="add-btn" onclick={() => addCardToDeck(card)}>+</button>
            </div>
          {/each}
        {:else if searchQuery.length >= 2 && !isSearching}
          <p class="no-results">No cards found</p>
        {:else if searchQuery.length < 2}
          <p class="search-hint">Type at least 2 characters to search</p>
        {/if}
      </div>
    </aside>

    <ResizeHandle direction="horizontal" onResize={handleSearchPanelResize} />

    <!-- Main Deck View -->
    <main class="deck-main">
      <!-- Zone Tabs -->
      <div class="zone-tabs">
        {#each zones as zone}
          <button
            class="zone-tab"
            class:active={selectedZone === zone.id}
            class:has-cards={getZoneCount(zone.id) > 0}
            onclick={() => setSelectedZone(zone.id)}
            ondragover={handleDragOver}
            ondrop={(e) => handleDrop(e, zone.id)}
          >
            <span class="zone-icon">{zone.icon}</span>
            <span class="zone-label">{zone.label}</span>
            <span class="zone-count">{getZoneCount(zone.id)}</span>
          </button>
        {/each}
      </div>

      <!-- Display Mode Controls -->
      <div class="view-controls">
        <div class="display-modes">
          {#each displayModes as mode}
            <button
              class="mode-btn"
              class:active={displayMode === mode.id}
              onclick={() => setDisplayMode(mode.id)}
              title={mode.label}
            >
              {mode.icon}
            </button>
          {/each}
        </div>
        
        {#if displayMode === 'pile'}
          <div class="pile-sort">
            <span class="label">Sort by:</span>
            {#each pileSortOptions as option}
              <button
                class="sort-btn"
                class:active={pileSortBy === option.id}
                onclick={() => setPileSortBy(option.id)}
              >
                {option.label}
              </button>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Card List View -->
      {#if displayMode === 'list'}
        <div class="card-list">
          {#each getCardsInZone(selectedZone) as card}
            <!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events a11y_no_noninteractive_element_interactions -->
            <div 
              class="list-card"
              class:selected={selectedCard?.id === card.id}
              draggable="true"
              role="listitem"
              ondragstart={(e) => handleDragStart(e, card)}
              ondragend={handleDragEnd}
              onclick={() => selectCard(card)}
            >
              <div class="card-main">
                <span class="quantity">{card.quantity}x</span>
                <span class="name">{card.name}</span>
                {#if card.tags.length > 0}
                  <div class="card-tags">
                    {#each card.tags.slice(0, 2) as tag}
                      <span class="mini-tag">{tag}</span>
                    {/each}
                    {#if card.tags.length > 2}
                      <span class="mini-tag more">+{card.tags.length - 2}</span>
                    {/if}
                  </div>
                {/if}
              </div>
              <div class="card-meta">
                <span class="mana">{card.mana_cost || ''}</span>
                <span class="type">{card.type_line.split('—')[0].trim()}</span>
              </div>
              <div class="card-controls">
                <button onclick={(e) => { e.stopPropagation(); updateQuantity(card.id, card.quantity - 1, card.zone); }}>−</button>
                <button onclick={(e) => { e.stopPropagation(); updateQuantity(card.id, card.quantity + 1, card.zone); }}>+</button>
                <button class="remove" onclick={(e) => { e.stopPropagation(); removeCard(card.id, card.zone); }}>✕</button>
              </div>
            </div>
          {/each}
          {#if getCardsInZone(selectedZone).length === 0}
            <div class="empty-zone">
              <p>No cards in {zones.find(z => z.id === selectedZone)?.label}</p>
              <p class="hint">Search and add cards, or drag cards here</p>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Grid View -->
      {#if displayMode === 'grid'}
        <div class="card-grid">
          {#each getCardsInZone(selectedZone) as card}
            <!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events a11y_no_noninteractive_element_interactions -->
            <div 
              class="grid-card"
              class:selected={selectedCard?.id === card.id}
              draggable="true"
              role="listitem"
              ondragstart={(e) => handleDragStart(e, card)}
              ondragend={handleDragEnd}
              onclick={() => selectCard(card)}
            >
              {#if card.image_uri}
                <img src={card.image_uri} alt={card.name} loading="lazy" />
              {:else}
                <div class="no-image">
                  <span>{card.name}</span>
                </div>
              {/if}
              <div class="grid-card-overlay">
                <span class="quantity-badge">{card.quantity}x</span>
                <div class="grid-controls">
                  <button onclick={(e) => { e.stopPropagation(); updateQuantity(card.id, card.quantity - 1, card.zone); }}>−</button>
                  <button onclick={(e) => { e.stopPropagation(); updateQuantity(card.id, card.quantity + 1, card.zone); }}>+</button>
                </div>
              </div>
            </div>
          {/each}
          {#if getCardsInZone(selectedZone).length === 0}
            <div class="empty-zone grid-empty">
              <p>No cards in {zones.find(z => z.id === selectedZone)?.label}</p>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Pile View -->
      {#if displayMode === 'pile'}
        <div class="card-piles">
          {#each getSortedPileKeys(getCardPiles()) as pileKey}
            <div class="pile-column">
              <div class="pile-header">
                <span class="pile-title">{pileKey}</span>
                <span class="pile-count">{getCardPiles().get(pileKey)?.reduce((s, c) => s + c.quantity, 0)}</span>
              </div>
              <div class="pile-stack">
                {#each getCardPiles().get(pileKey) || [] as card, i}
                  <!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events a11y_no_noninteractive_element_interactions -->
                  <div 
                    class="pile-card"
                    class:selected={selectedCard?.id === card.id}
                    style="--stack-offset: {i * 28}px"
                    draggable="true"
                    role="listitem"
                    ondragstart={(e) => handleDragStart(e, card)}
                    ondragend={handleDragEnd}
                    onclick={() => selectCard(card)}
                  >
                    {#if card.image_uri}
                      <img src={card.image_uri} alt={card.name} loading="lazy" />
                    {:else}
                      <div class="pile-card-text">
                        <span class="name">{card.name}</span>
                      </div>
                    {/if}
                    <span class="pile-quantity">{card.quantity}x</span>
                  </div>
                {/each}
              </div>
            </div>
          {/each}
          {#if getCardsInZone(selectedZone).length === 0}
            <div class="empty-zone pile-empty">
              <p>No cards in {zones.find(z => z.id === selectedZone)?.label}</p>
            </div>
          {/if}
        </div>
      {/if}
    </main>

    <!-- Right Panel - Preview & Stats -->
    {#if showStats || selectedCard}
      <ResizeHandle direction="horizontal" onResize={handleRightPanelResize} />
      <aside class="right-panel" style="width: {rightPanelWidth}px">
        {#if selectedCard}
          <CardPreview card={selectedCard} onClose={() => selectedCard = null} />
        {/if}
        {#if showStats}
          <DeckStats />
        {/if}
      </aside>
    {/if}
  </div>
</div>

<style>
  .deck-builder {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: hsl(var(--background));
  }

  .builder-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.5rem;
    background: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
    flex-shrink: 0;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .back-btn {
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .back-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .deck-info {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
  }

  .deck-info h1 {
    font-size: 1.125rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    margin: 0;
  }

  .deck-format {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    padding: 0.25rem 0.5rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-full);
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .card-count {
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
  }

  .stats-toggle {
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .stats-toggle:hover {
    background: hsl(var(--accent));
  }

  .stats-toggle.active {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .builder-content {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  /* Search Panel */
  .search-panel {
    min-width: 200px;
    max-width: 500px;
    background: hsl(var(--card));
    border-right: 1px solid hsl(var(--border));
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }

  .panel-header {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid hsl(var(--border));
  }

  .panel-header h2 {
    font-size: 0.875rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    margin: 0;
  }

  .search-input-wrapper {
    padding: 0.75rem 1rem;
    position: relative;
  }

  .search-input-wrapper input {
    width: 100%;
    padding: 0.625rem 0.875rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    color: hsl(var(--foreground));
    font-size: 0.875rem;
  }

  .search-input-wrapper input:focus {
    outline: none;
    border-color: hsl(var(--ring));
  }

  .search-input-wrapper input::placeholder {
    color: hsl(var(--muted-foreground));
  }

  .search-spinner {
    position: absolute;
    right: 1.5rem;
    top: 50%;
    transform: translateY(-50%);
    animation: spin 1s linear infinite;
    color: hsl(var(--muted-foreground));
  }

  @keyframes spin {
    from { transform: translateY(-50%) rotate(0deg); }
    to { transform: translateY(-50%) rotate(360deg); }
  }

  .add-to-zone {
    padding: 0 1rem 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .add-to-zone .label {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .add-to-zone select {
    flex: 1;
    padding: 0.375rem 0.5rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
  }

  .search-results {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
  }

  .search-card {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0.5rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-md);
    margin-bottom: 0.375rem;
    cursor: grab;
    transition: all var(--transition-fast);
  }

  .search-card:hover {
    background: hsl(var(--accent));
  }

  .search-card:active {
    cursor: grabbing;
  }

  .search-card img {
    width: 40px;
    height: 56px;
    object-fit: cover;
    border-radius: var(--radius-sm);
  }

  .search-card .card-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .search-card .card-name {
    font-size: 0.8125rem;
    font-weight: 500;
    color: hsl(var(--foreground));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .search-card .card-type {
    font-size: 0.6875rem;
    color: hsl(var(--muted-foreground));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .search-card .card-mana {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    font-family: monospace;
  }

  .add-btn {
    width: 28px;
    height: 28px;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border: none;
    border-radius: 50%;
    font-size: 1.125rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    flex-shrink: 0;
  }

  .add-btn:hover {
    transform: scale(1.1);
  }

  .no-results, .search-hint {
    text-align: center;
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    padding: 2rem 1rem;
  }

  /* Main Deck Area */
  .deck-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .zone-tabs {
    display: flex;
    padding: 0.5rem 1rem;
    gap: 0.375rem;
    background: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
    flex-shrink: 0;
    overflow-x: auto;
  }

  .zone-tab {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: 1px solid transparent;
    border-radius: var(--radius-md);
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
  }

  .zone-tab:hover {
    background: hsl(var(--accent));
  }

  .zone-tab.active {
    background: hsl(var(--secondary));
    color: hsl(var(--foreground));
    border-color: hsl(var(--border));
  }

  .zone-tab.has-cards .zone-count {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
  }

  .zone-icon {
    font-size: 0.875rem;
  }

  .zone-count {
    font-size: 0.6875rem;
    padding: 0.125rem 0.375rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-full);
  }

  .view-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 1rem;
    background: hsl(var(--card));
    border-bottom: 1px solid hsl(var(--border));
    flex-shrink: 0;
  }

  .display-modes {
    display: flex;
    gap: 0.25rem;
  }

  .mode-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--muted-foreground));
    font-size: 1rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .mode-btn:hover {
    background: hsl(var(--accent));
  }

  .mode-btn.active {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border-color: hsl(var(--primary));
  }

  .pile-sort {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .pile-sort .label {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .sort-btn {
    padding: 0.375rem 0.625rem;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--muted-foreground));
    font-size: 0.75rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .sort-btn:hover {
    background: hsl(var(--accent));
  }

  .sort-btn.active {
    background: hsl(var(--secondary));
    color: hsl(var(--foreground));
  }

  /* List View */
  .card-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.75rem 1rem;
  }

  .list-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.625rem 0.75rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    margin-bottom: 0.375rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .list-card:hover {
    border-color: hsl(var(--ring));
  }

  .list-card.selected {
    border-color: hsl(var(--primary));
    background: hsl(var(--accent));
  }

  .list-card .card-main {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 0;
  }

  .list-card .quantity {
    font-weight: 700;
    color: hsl(var(--primary));
    min-width: 24px;
    font-size: 0.875rem;
  }

  .list-card .name {
    color: hsl(var(--foreground));
    font-size: 0.875rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .card-tags {
    display: flex;
    gap: 0.25rem;
    margin-left: auto;
  }

  .mini-tag {
    font-size: 0.625rem;
    padding: 0.125rem 0.375rem;
    background: hsl(var(--secondary));
    border-radius: var(--radius-full);
    color: hsl(var(--muted-foreground));
  }

  .mini-tag.more {
    background: hsl(var(--accent));
  }

  .list-card .card-meta {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
  }

  .list-card .mana {
    font-family: monospace;
    font-size: 0.8125rem;
    color: hsl(var(--muted-foreground));
  }

  .list-card .type {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    min-width: 80px;
  }

  .card-controls {
    display: flex;
    gap: 0.25rem;
  }

  .card-controls button {
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .card-controls button:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .card-controls .remove:hover {
    background: hsl(var(--destructive));
    color: hsl(var(--destructive-foreground));
    border-color: hsl(var(--destructive));
  }

  .empty-zone {
    text-align: center;
    padding: 3rem 1rem;
    color: hsl(var(--muted-foreground));
  }

  .empty-zone p {
    margin: 0.25rem 0;
  }

  .empty-zone .hint {
    font-size: 0.8125rem;
    opacity: 0.7;
  }

  /* Grid View */
  .card-grid {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.75rem;
    align-content: start;
  }

  .grid-card {
    position: relative;
    aspect-ratio: 63/88;
    border-radius: var(--radius-md);
    overflow: hidden;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .grid-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
  }

  .grid-card.selected {
    outline: 2px solid hsl(var(--primary));
    outline-offset: 2px;
  }

  .grid-card img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .grid-card .no-image {
    width: 100%;
    height: 100%;
    background: hsl(var(--secondary));
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
    text-align: center;
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .grid-card-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 50%);
    opacity: 0;
    transition: opacity var(--transition-fast);
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 0.5rem;
  }

  .grid-card:hover .grid-card-overlay {
    opacity: 1;
  }

  .quantity-badge {
    position: absolute;
    top: 0.375rem;
    right: 0.375rem;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.125rem 0.375rem;
    border-radius: var(--radius-sm);
  }

  .grid-controls {
    display: flex;
    justify-content: center;
    gap: 0.25rem;
  }

  .grid-controls button {
    width: 28px;
    height: 28px;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border: none;
    border-radius: var(--radius-sm);
    font-size: 1rem;
    cursor: pointer;
  }

  .grid-empty {
    grid-column: 1 / -1;
  }

  /* Pile View */
  .card-piles {
    flex: 1;
    overflow-x: auto;
    padding: 1rem;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
  }

  .pile-column {
    flex-shrink: 0;
    width: 140px;
  }

  .pile-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    margin-bottom: 0.5rem;
  }

  .pile-title {
    font-size: 0.8125rem;
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .pile-count {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .pile-stack {
    position: relative;
    min-height: 200px;
  }

  .pile-card {
    position: absolute;
    top: var(--stack-offset, 0);
    left: 0;
    width: 100%;
    aspect-ratio: 63/88;
    border-radius: var(--radius-md);
    overflow: hidden;
    cursor: pointer;
    transition: all var(--transition-fast);
    box-shadow: var(--shadow-sm);
  }

  .pile-card:hover {
    transform: translateY(-8px) scale(1.02);
    z-index: 10;
    box-shadow: var(--shadow-lg);
  }

  .pile-card.selected {
    outline: 2px solid hsl(var(--primary));
  }

  .pile-card img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .pile-card-text {
    width: 100%;
    height: 100%;
    background: hsl(var(--secondary));
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
    text-align: center;
  }

  .pile-card-text .name {
    font-size: 0.75rem;
    color: hsl(var(--foreground));
  }

  .pile-quantity {
    position: absolute;
    bottom: 0.25rem;
    right: 0.25rem;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    font-size: 0.6875rem;
    font-weight: 700;
    padding: 0.125rem 0.25rem;
    border-radius: var(--radius-sm);
  }

  .pile-empty {
    width: 100%;
  }

  /* Right Panel */
  .right-panel {
    min-width: 200px;
    max-width: 500px;
    background: hsl(var(--card));
    border-left: 1px solid hsl(var(--border));
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    flex-shrink: 0;
  }
</style>
