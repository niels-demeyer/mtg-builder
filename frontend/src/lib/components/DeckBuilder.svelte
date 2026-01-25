<script lang="ts">
  import { onDestroy } from 'svelte';
  import { deckStore, flushPendingSave } from '../../stores/deckStore';
  import type { ScryfallCard, CardInDeck, CardZone, DisplayMode, PileSortBy } from '$lib/types';
  import { downloadDeckAsTxt, parseDeckTxt, type ParsedDeck } from '$lib/deckTxt';

  // Flush any pending saves when leaving the deck builder
  onDestroy(() => {
    flushPendingSave();
  });
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

  // Advanced search state
  let showAdvanced = $state(false);
  let currentPage = $state(1);
  let hasMore = $state(false);
  let totalResults = $state(0);

  interface SearchFilters {
    text: string;
    colors: Set<string>;
    colorMatch: 'any' | 'all' | 'exact';
    types: Set<string>;
    rarity: Set<string>;
    cmcMin: string;
    cmcMax: string;
    keywords: string;
  }

  let filters = $state<SearchFilters>({
    text: '',
    colors: new Set(),
    colorMatch: 'any',
    types: new Set(),
    rarity: new Set(),
    cmcMin: '',
    cmcMax: '',
    keywords: ''
  });

  const COLORS = [
    { code: 'W', name: 'White', symbol: '○' },
    { code: 'U', name: 'Blue', symbol: '●' },
    { code: 'B', name: 'Black', symbol: '◆' },
    { code: 'R', name: 'Red', symbol: '▲' },
    { code: 'G', name: 'Green', symbol: '◼' },
    { code: 'C', name: 'Colorless', symbol: '◇' }
  ];

  const CARD_TYPES = [
    'Creature', 'Instant', 'Sorcery', 'Enchantment',
    'Artifact', 'Planeswalker', 'Land', 'Battle'
  ];

  const RARITIES = [
    { code: 'common', name: 'C' },
    { code: 'uncommon', name: 'U' },
    { code: 'rare', name: 'R' },
    { code: 'mythic', name: 'M' }
  ];

  // Hover preview state
  let hoveredCard = $state<ScryfallCard | null>(null);
  let hoverPosition = $state({ x: 0, y: 0 });

  // Import/Export state
  let fileInput: HTMLInputElement | undefined = $state();
  let isImporting = $state(false);
  let importError = $state<string | null>(null);

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

  function toggleColor(code: string): void {
    const newColors = new Set(filters.colors);
    if (newColors.has(code)) {
      newColors.delete(code);
    } else {
      newColors.add(code);
    }
    filters.colors = newColors;
  }

  function toggleType(type: string): void {
    const newTypes = new Set(filters.types);
    if (newTypes.has(type)) {
      newTypes.delete(type);
    } else {
      newTypes.add(type);
    }
    filters.types = newTypes;
  }

  function toggleRarity(code: string): void {
    const newRarity = new Set(filters.rarity);
    if (newRarity.has(code)) {
      newRarity.delete(code);
    } else {
      newRarity.add(code);
    }
    filters.rarity = newRarity;
  }

  function hasAnyFilter(): boolean {
    return (
      searchQuery.length >= 2 ||
      filters.text.length >= 2 ||
      filters.colors.size > 0 ||
      filters.types.size > 0 ||
      filters.rarity.size > 0 ||
      filters.cmcMin !== '' ||
      filters.cmcMax !== '' ||
      filters.keywords.length >= 2
    );
  }

  function clearFilters(): void {
    filters = {
      text: '',
      colors: new Set(),
      colorMatch: 'any',
      types: new Set(),
      rarity: new Set(),
      cmcMin: '',
      cmcMax: '',
      keywords: ''
    };
    searchQuery = '';
    searchResults = [];
    currentPage = 1;
    hasMore = false;
    totalResults = 0;
  }

  async function searchCards(page: number = 1, append: boolean = false): Promise<void> {
    if (!hasAnyFilter()) {
      searchResults = [];
      return;
    }

    isSearching = true;
    currentPage = page;

    try {
      const params = new URLSearchParams();

      if (searchQuery.length >= 2) params.set('q', searchQuery);
      if (filters.text.length >= 2) params.set('text', filters.text);
      if (filters.colors.size > 0) {
        params.set('colors', Array.from(filters.colors).join(','));
        params.set('color_match', filters.colorMatch);
      }
      if (filters.types.size > 0) params.set('types', Array.from(filters.types).join(','));
      if (filters.rarity.size > 0) params.set('rarity', Array.from(filters.rarity).join(','));
      if (filters.cmcMin !== '') params.set('cmc_min', filters.cmcMin);
      if (filters.cmcMax !== '') params.set('cmc_max', filters.cmcMax);
      if (filters.keywords.length >= 2) params.set('keywords', filters.keywords);
      params.set('page', String(page));
      params.set('page_size', '30');

      const response = await fetch(
        `http://localhost:8000/api/v1/search?${params.toString()}`
      );
      if (response.ok) {
        const data = await response.json();
        const results = (data.data || []).map((card: ScryfallCard) => ({
          ...card,
          image_uris: card.image_uris || { small: '', normal: '', large: '' }
        }));

        if (append) {
          searchResults = [...searchResults, ...results];
        } else {
          searchResults = results;
        }

        if (data.pagination) {
          hasMore = data.pagination.has_next;
          totalResults = data.pagination.total_cards;
        } else {
          hasMore = false;
          totalResults = results.length;
        }
      } else {
        if (!append) searchResults = [];
        hasMore = false;
      }
    } catch {
      if (!append) searchResults = [];
      hasMore = false;
    } finally {
      isSearching = false;
    }
  }

  function loadMore(): void {
    if (!isSearching && hasMore) {
      searchCards(currentPage + 1, true);
    }
  }

  function handleSearchInput(): void {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => searchCards(1, false), 300);
  }

  function handleSearchKeydown(e: KeyboardEvent): void {
    if (e.key === 'Enter') {
      clearTimeout(searchTimeout);
      searchCards(1, false);
    }
  }

  function handleCardHover(card: ScryfallCard, event: MouseEvent): void {
    hoveredCard = card;
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    hoverPosition = {
      x: rect.right + 10,
      y: rect.top
    };
  }

  function handleCardHoverEnd(): void {
    hoveredCard = null;
  }

  function addCardToDeck(card: ScryfallCard, zone: CardZone = selectedZone): void {
    // Ensure colors is always an array (API may return string)
    const rawColors = card.colors as unknown;
    let colors: string[];
    if (typeof rawColors === 'string') {
      colors = rawColors ? rawColors.split('') : [];
    } else if (Array.isArray(rawColors)) {
      colors = rawColors;
    } else {
      colors = [];
    }

    const cardInDeck: Omit<CardInDeck, 'quantity' | 'zone' | 'tags'> = {
      id: card.id,
      name: card.name,
      mana_cost: card.mana_cost,
      cmc: card.cmc,
      type_line: card.type_line,
      colors,
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

  // Export deck to txt file
  function handleExport(): void {
    if (currentDeck) {
      downloadDeckAsTxt(currentDeck);
    }
  }

  // Import deck from txt file
  function handleImportClick(): void {
    fileInput?.click();
  }

  async function handleFileSelect(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    isImporting = true;
    importError = null;

    try {
      const content = await file.text();
      const parsed = parseDeckTxt(content);
      await importParsedDeck(parsed);
    } catch (e) {
      importError = e instanceof Error ? e.message : 'Failed to import deck';
      console.error('Import error:', e);
    } finally {
      isImporting = false;
      input.value = ''; // Reset file input
    }
  }

  async function importParsedDeck(parsed: ParsedDeck): Promise<void> {
    if (!currentDeck) {
      importError = 'No deck selected';
      return;
    }

    const notFound: string[] = [];
    const skipped: string[] = [];
    let importedCount = 0;

    // Look up each card by name and add to deck
    for (const card of parsed.cards) {
      try {
        // Check if card already exists in the deck (same zone)
        const existingCard = currentDeck.cards.find(
          (c) => c.name.toLowerCase() === card.name.toLowerCase() && c.zone === card.zone
        );

        if (existingCard) {
          skipped.push(card.name);
          continue;
        }

        // Search for the card by exact name (use larger page size to find exact matches)
        const response = await fetch(
          `http://localhost:8000/api/v1/search?q=${encodeURIComponent(card.name)}&page_size=10`
        );

        if (response.ok) {
          const data = await response.json();
          const results = data.data || [];

          // Find exact name match
          const match = results.find(
            (c: ScryfallCard) => c.name.toLowerCase() === card.name.toLowerCase()
          );

          if (match) {
            // Ensure colors is always an array (API may return string)
            const rawColors = match.colors as unknown;
            let colors: string[];
            if (typeof rawColors === 'string') {
              colors = rawColors ? rawColors.split('') : [];
            } else if (Array.isArray(rawColors)) {
              colors = rawColors;
            } else {
              colors = [];
            }

            const cardInDeck: Omit<CardInDeck, 'quantity' | 'zone' | 'tags'> = {
              id: match.id,
              name: match.name,
              mana_cost: match.mana_cost,
              cmc: match.cmc,
              type_line: match.type_line,
              colors,
              rarity: match.rarity,
              image_uri: match.image_uris?.normal || match.card_faces?.[0]?.image_uris?.normal,
            };
            deckStore.addCard(cardInDeck, card.quantity, card.zone, []);
            importedCount++;
          } else {
            notFound.push(card.name);
          }
        } else {
          notFound.push(card.name);
        }
      } catch {
        notFound.push(card.name);
      }
    }

    // Build result message
    const messages: string[] = [];
    if (importedCount > 0) {
      messages.push(`Imported ${importedCount} cards`);
    }
    if (skipped.length > 0) {
      messages.push(`${skipped.length} already in deck`);
    }
    if (notFound.length > 0) {
      const notFoundPreview = notFound.slice(0, 3).join(', ');
      const more = notFound.length > 3 ? ` +${notFound.length - 3} more` : '';
      messages.push(`Not found: ${notFoundPreview}${more}`);
    }

    if (messages.length > 0) {
      importError = messages.join('. ');
    }
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
        class="header-btn"
        onclick={handleImportClick}
        disabled={isImporting}
        title="Import deck from .txt file"
      >
        {isImporting ? '...' : 'Import'}
      </button>
      <button
        class="header-btn"
        onclick={handleExport}
        disabled={!currentDeck || currentDeck.cards.length === 0}
        title="Export deck to .txt file"
      >
        Export
      </button>
      <button
        class="stats-toggle"
        class:active={showStats}
        onclick={() => showStats = !showStats}
      >
        Stats
      </button>
      <input
        type="file"
        accept=".txt"
        bind:this={fileInput}
        onchange={handleFileSelect}
        style="display: none;"
      />
    </div>
  </header>

  {#if importError}
    <div class="import-notification" class:warning={importError.includes('Not found')} class:success={!importError.includes('Not found') && importError.includes('Imported')}>
      <span>{importError}</span>
      <button onclick={() => importError = null}>×</button>
    </div>
  {/if}

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
          onkeydown={handleSearchKeydown}
        />
        <button
          class="toggle-advanced-btn"
          class:active={showAdvanced}
          onclick={() => showAdvanced = !showAdvanced}
          title="Advanced Search"
        >
          ⚙
        </button>
        {#if isSearching}
          <span class="search-spinner">⟳</span>
        {/if}
      </div>

      {#if showAdvanced}
        <div class="advanced-filters">
          <div class="filter-group">
            <label for="filter-text">Oracle Text</label>
            <input
              id="filter-text"
              type="text"
              placeholder="Card text..."
              bind:value={filters.text}
              onkeydown={handleSearchKeydown}
            />
          </div>

          <div class="filter-group">
            <label for="filter-keywords">Keywords</label>
            <input
              id="filter-keywords"
              type="text"
              placeholder="Flying, Trample..."
              bind:value={filters.keywords}
              onkeydown={handleSearchKeydown}
            />
          </div>

          <div class="filter-group">
            <span class="filter-label">Colors</span>
            <div class="color-buttons">
              {#each COLORS as color}
                <button
                  class="color-btn color-{color.code.toLowerCase()}"
                  class:selected={filters.colors.has(color.code)}
                  onclick={() => toggleColor(color.code)}
                  title={color.name}
                >
                  {color.symbol}
                </button>
              {/each}
            </div>
            <select class="color-match-select" bind:value={filters.colorMatch}>
              <option value="any">Any</option>
              <option value="all">All</option>
              <option value="exact">Exact</option>
            </select>
          </div>

          <div class="filter-group">
            <span class="filter-label">Types</span>
            <div class="type-buttons">
              {#each CARD_TYPES as type}
                <button
                  class="type-btn"
                  class:selected={filters.types.has(type)}
                  onclick={() => toggleType(type)}
                >
                  {type.slice(0, 4)}
                </button>
              {/each}
            </div>
          </div>

          <div class="filter-group">
            <span class="filter-label">Rarity</span>
            <div class="rarity-buttons">
              {#each RARITIES as rarity}
                <button
                  class="rarity-btn rarity-{rarity.code}"
                  class:selected={filters.rarity.has(rarity.code)}
                  onclick={() => toggleRarity(rarity.code)}
                  title={rarity.code}
                >
                  {rarity.name}
                </button>
              {/each}
            </div>
          </div>

          <div class="filter-group">
            <span class="filter-label">CMC</span>
            <div class="cmc-inputs">
              <input
                type="number"
                placeholder="Min"
                min="0"
                bind:value={filters.cmcMin}
                onkeydown={handleSearchKeydown}
              />
              <span>-</span>
              <input
                type="number"
                placeholder="Max"
                min="0"
                bind:value={filters.cmcMax}
                onkeydown={handleSearchKeydown}
              />
            </div>
          </div>

          <button class="clear-filters-btn" onclick={clearFilters}>Clear All</button>
        </div>
      {/if}

      <div class="add-to-zone">
        <span class="label">Add to:</span>
        <select bind:value={selectedZone} onchange={(e) => setSelectedZone(e.currentTarget.value as CardZone)}>
          {#each zones.filter(z => z.id !== 'commander') as zone}
            <option value={zone.id}>{zone.label}</option>
          {/each}
        </select>
      </div>

      <div class="search-results">
        {#if totalResults > 0}
          <div class="results-header">
            <span class="results-count">{totalResults} cards found</span>
          </div>
        {/if}
        {#if searchResults.length > 0}
          {#each searchResults as card}
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
              class="search-card"
              draggable="true"
              role="listitem"
              ondragstart={(e) => handleDragStart(e, { ...card, quantity: 1, zone: 'mainboard', tags: [] } as CardInDeck)}
              onmouseenter={(e) => handleCardHover(card, e)}
              onmouseleave={handleCardHoverEnd}
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
          {#if hasMore}
            <button class="load-more-btn" onclick={loadMore} disabled={isSearching}>
              {isSearching ? 'Loading...' : 'Load More'}
            </button>
          {/if}
        {:else if hasAnyFilter() && !isSearching}
          <p class="no-results">No cards found</p>
        {:else if !hasAnyFilter()}
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

  <!-- Hover Preview -->
  {#if hoveredCard}
    <div
      class="hover-preview"
      style="left: {hoverPosition.x}px; top: {hoverPosition.y}px;"
    >
      <div class="hover-preview-image">
        <img
          src={hoveredCard.image_uris?.normal || hoveredCard.card_faces?.[0]?.image_uris?.normal || ''}
          alt={hoveredCard.name}
        />
      </div>
      <div class="hover-preview-details">
        <h4>{hoveredCard.name}</h4>
        <p class="hover-type">{hoveredCard.type_line}</p>
        {#if hoveredCard.oracle_text}
          <p class="hover-oracle">{hoveredCard.oracle_text}</p>
        {/if}
        <div class="hover-stats">
          <span class="hover-mana">{hoveredCard.mana_cost || 'No cost'}</span>
          <span class="hover-rarity rarity-{hoveredCard.rarity}">{hoveredCard.rarity}</span>
        </div>
      </div>
    </div>
  {/if}
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

  .stats-toggle,
  .header-btn {
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .stats-toggle:hover,
  .header-btn:hover:not(:disabled) {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .header-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .stats-toggle.active {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .import-notification {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.625rem 1rem;
    background: hsl(var(--primary) / 0.1);
    border-bottom: 1px solid hsl(var(--primary) / 0.2);
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
  }

  .import-notification.warning {
    background: hsl(40 80% 50% / 0.1);
    border-color: hsl(40 80% 50% / 0.3);
  }

  .import-notification.success {
    background: hsl(142 70% 45% / 0.1);
    border-color: hsl(142 70% 45% / 0.3);
  }

  .import-notification button {
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    font-size: 1.25rem;
    cursor: pointer;
    padding: 0 0.25rem;
    line-height: 1;
  }

  .import-notification button:hover {
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

  .toggle-advanced-btn {
    position: absolute;
    right: 2.5rem;
    top: 50%;
    transform: translateY(-50%);
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    font-size: 1rem;
    padding: 0.25rem;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
  }

  .toggle-advanced-btn:hover,
  .toggle-advanced-btn.active {
    color: hsl(var(--primary));
    background: hsl(var(--accent));
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

  /* Advanced Filters */
  .advanced-filters {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid hsl(var(--border));
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .filter-group label,
  .filter-label {
    font-size: 0.6875rem;
    font-weight: 500;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .filter-group input[type="text"],
  .filter-group input[type="number"] {
    padding: 0.5rem 0.625rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
  }

  .filter-group input:focus {
    outline: none;
    border-color: hsl(var(--ring));
  }

  /* Color Buttons */
  .color-buttons {
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
  }

  .color-btn {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    border: 2px solid hsl(var(--border));
    cursor: pointer;
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    padding: 0;
  }

  .color-btn.color-w { background: linear-gradient(135deg, #fffbd5, #f8f6e1); color: #9b8e4e; }
  .color-btn.color-u { background: linear-gradient(135deg, #0e68ab, #1a88c9); color: #fff; }
  .color-btn.color-b { background: linear-gradient(135deg, #150b00, #3d3d3d); color: #a08c7e; }
  .color-btn.color-r { background: linear-gradient(135deg, #d32029, #f34336); color: #fff; }
  .color-btn.color-g { background: linear-gradient(135deg, #00733e, #19a654); color: #fff; }
  .color-btn.color-c { background: linear-gradient(135deg, #a8a8a8, #d4d4d4); color: #4a4a4a; }

  .color-btn:hover {
    transform: scale(1.1);
  }

  .color-btn.selected {
    border-color: hsl(var(--primary));
    box-shadow: 0 0 0 2px hsl(var(--primary) / 0.3);
  }

  .color-match-select {
    margin-top: 0.25rem;
    padding: 0.375rem 0.5rem;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    background: hsl(var(--secondary));
    color: hsl(var(--foreground));
  }

  /* Type Buttons */
  .type-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .type-btn {
    padding: 0.25rem 0.5rem;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    background: hsl(var(--secondary));
    color: hsl(var(--muted-foreground));
    font-size: 0.6875rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .type-btn:hover {
    border-color: hsl(var(--muted-foreground));
  }

  .type-btn.selected {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border-color: hsl(var(--primary));
  }

  /* Rarity Buttons */
  .rarity-buttons {
    display: flex;
    gap: 0.25rem;
  }

  .rarity-btn {
    padding: 0.25rem 0.5rem;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    background: hsl(var(--secondary));
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .rarity-btn.rarity-common { color: #666; }
  .rarity-btn.rarity-uncommon { color: #607d8b; }
  .rarity-btn.rarity-rare { color: #b8860b; }
  .rarity-btn.rarity-mythic { color: #d84315; }

  .rarity-btn:hover {
    border-color: hsl(var(--muted-foreground));
  }

  .rarity-btn.selected {
    border-width: 2px;
  }

  .rarity-btn.selected.rarity-common { background: #e0e0e0; border-color: #666; }
  .rarity-btn.selected.rarity-uncommon { background: #cfd8dc; border-color: #607d8b; }
  .rarity-btn.selected.rarity-rare { background: #fff8e1; border-color: #b8860b; }
  .rarity-btn.selected.rarity-mythic { background: #ffebee; border-color: #d84315; }

  /* CMC Inputs */
  .cmc-inputs {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .cmc-inputs input {
    width: 50px;
    padding: 0.375rem;
    text-align: center;
  }

  .cmc-inputs span {
    color: hsl(var(--muted-foreground));
    font-size: 0.75rem;
  }

  /* Clear Filters Button */
  .clear-filters-btn {
    margin-top: 0.25rem;
    padding: 0.5rem;
    background: transparent;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--muted-foreground));
    font-size: 0.75rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .clear-filters-btn:hover {
    background: hsl(var(--destructive) / 0.1);
    border-color: hsl(var(--destructive));
    color: hsl(var(--destructive));
  }

  /* Results Header */
  .results-header {
    padding: 0.5rem;
    border-bottom: 1px solid hsl(var(--border));
  }

  .results-count {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  /* Load More Button */
  .load-more-btn {
    width: 100%;
    padding: 0.75rem;
    margin-top: 0.5rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .load-more-btn:hover:not(:disabled) {
    background: hsl(var(--accent));
    border-color: hsl(var(--ring));
  }

  .load-more-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
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

  /* Hover Preview */
  .hover-preview {
    position: fixed;
    z-index: 1000;
    display: flex;
    gap: 0.75rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-lg);
    padding: 0.75rem;
    box-shadow: var(--shadow-lg);
    max-width: 420px;
    pointer-events: none;
    animation: fadeIn 0.15s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateX(-8px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .hover-preview-image {
    flex-shrink: 0;
  }

  .hover-preview-image img {
    width: 180px;
    height: auto;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-md);
  }

  .hover-preview-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 0;
    max-width: 200px;
  }

  .hover-preview-details h4 {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    line-height: 1.2;
  }

  .hover-type {
    margin: 0;
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .hover-oracle {
    margin: 0;
    font-size: 0.75rem;
    color: hsl(var(--foreground));
    line-height: 1.4;
    max-height: 120px;
    overflow-y: auto;
    white-space: pre-wrap;
  }

  .hover-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: auto;
    padding-top: 0.5rem;
    border-top: 1px solid hsl(var(--border));
  }

  .hover-mana {
    font-family: monospace;
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .hover-rarity {
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: capitalize;
    padding: 0.125rem 0.375rem;
    border-radius: var(--radius-sm);
  }

  .hover-rarity.rarity-common { background: #e0e0e0; color: #1a1a1a; }
  .hover-rarity.rarity-uncommon { background: #607d8b; color: #fff; }
  .hover-rarity.rarity-rare { background: #b8860b; color: #fff; }
  .hover-rarity.rarity-mythic { background: #d84315; color: #fff; }
</style>
