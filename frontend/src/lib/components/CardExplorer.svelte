<script lang="ts">
    import type { DbCard } from '$lib/types';
    import { isDFC, getFaceImage, getFaceData } from '$lib/cardUtils';

    interface Printing {
        id: string;
        name: string;
        set_name: string;
        set_code: string;
        collector_number: string;
        rarity: string;
        image_uris?: {
            small: string;
            normal: string;
            large: string;
        };
        card_faces?: Array<{
            image_uris?: {
                small: string;
                normal: string;
                large: string;
            };
        }>;
        released_at: string;
    }

    interface SearchFilters {
        name: string;
        text: string;
        colors: Set<string>;
        colorMatch: 'any' | 'all' | 'exact';
        types: Set<string>;
        rarity: Set<string>;
        cmcMin: string;
        cmcMax: string;
        keywords: string;
    }

    const COLORS = [
        { code: 'W', name: 'White', symbol: '○' },
        { code: 'U', name: 'Blue', symbol: '●' },
        { code: 'B', name: 'Black', symbol: '◆' },
        { code: 'R', name: 'Red', symbol: '▲' },
        { code: 'G', name: 'Green', symbol: '◼' },
        { code: 'C', name: 'Colorless', symbol: '◇' }
    ];

    const CARD_TYPES = [
        'Creature',
        'Instant',
        'Sorcery',
        'Enchantment',
        'Artifact',
        'Planeswalker',
        'Land',
        'Battle'
    ];

    const RARITIES = [
        { code: 'common', name: 'Common' },
        { code: 'uncommon', name: 'Uncommon' },
        { code: 'rare', name: 'Rare' },
        { code: 'mythic', name: 'Mythic' }
    ];

    let filters = $state<SearchFilters>({
        name: '',
        text: '',
        colors: new Set(),
        colorMatch: 'any',
        types: new Set(),
        rarity: new Set(),
        cmcMin: '',
        cmcMax: '',
        keywords: ''
    });

    interface Pagination {
        page: number;
        page_size: number;
        total_cards: number;
        total_pages: number;
        has_next: boolean;
        has_prev: boolean;
    }

    let cards = $state<DbCard[]>([]);
    let isLoading = $state(false);
    let hasSearched = $state(false);
    let showAdvanced = $state(false);
    let selectedCard = $state<DbCard | null>(null);
    let printings = $state<Printing[]>([]);
    let loadingPrintings = $state(false);
    let selectedPrintingIndex = $state(0);
    let currentPage = $state(1);
    let pagination = $state<Pagination | null>(null);
    let showingBackFace = $state(false);

    // Reset face when card changes
    $effect(() => {
        if (selectedCard) showingBackFace = false;
    });

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
            filters.name.length >= 2 ||
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
            name: '',
            text: '',
            colors: new Set(),
            colorMatch: 'any',
            types: new Set(),
            rarity: new Set(),
            cmcMin: '',
            cmcMax: '',
            keywords: ''
        };
    }

    async function searchCards(page: number = 1): Promise<void> {
        if (!hasAnyFilter()) return;

        isLoading = true;
        hasSearched = true;
        currentPage = page;

        try {
            const params = new URLSearchParams();

            if (filters.name.length >= 2) params.set('q', filters.name);
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
            params.set('page_size', '50');

            const response = await fetch(
                `http://localhost:8000/api/v1/search?${params.toString()}`
            );
            if (response.ok) {
                const data = await response.json();
                cards = data.data || [];
                pagination = data.pagination || null;
            } else {
                cards = [];
                pagination = null;
            }
        } catch {
            cards = [];
            pagination = null;
        } finally {
            isLoading = false;
        }
    }

    function goToPage(page: number): void {
        searchCards(page);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function handleKeydown(e: KeyboardEvent): void {
        if (e.key === 'Enter') {
            searchCards();
        }
    }

    async function selectCard(card: DbCard): Promise<void> {
        selectedCard = card;
        printings = [];
        selectedPrintingIndex = 0;
        loadingPrintings = true;

        try {
            const response = await fetch(
                `http://localhost:8000/api/v1/cards/${card.id}/printings`
            );
            if (response.ok) {
                const data = await response.json();
                printings = data.data || [];
            }
        } catch {
            printings = [];
        } finally {
            loadingPrintings = false;
        }
    }

    function closeModal(): void {
        selectedCard = null;
        printings = [];
        selectedPrintingIndex = 0;
    }

    function getCardImage(card: DbCard | Printing, size: 'small' | 'normal' | 'large' = 'normal'): string {
        if ('image_uris' in card && card.image_uris) {
            return card.image_uris[size] || card.image_uris.normal || card.image_uris.small || '';
        }
        if ('card_faces' in card && card.card_faces?.[0]?.image_uris) {
            const faceUris = card.card_faces[0].image_uris;
            return faceUris[size] || faceUris.normal || faceUris.small || '';
        }
        return '';
    }

    function selectPrinting(index: number): void {
        selectedPrintingIndex = index;
    }

    function formatManaCost(manaCost: string | undefined): string[] {
        if (!manaCost) return [];
        const matches = manaCost.match(/\{[^}]+\}/g);
        return matches || [];
    }

    function getManaSymbolClass(symbol: string): string {
        const inner = symbol.replace(/[{}]/g, '');
        if (inner === 'W') return 'mana-white';
        if (inner === 'U') return 'mana-blue';
        if (inner === 'B') return 'mana-black';
        if (inner === 'R') return 'mana-red';
        if (inner === 'G') return 'mana-green';
        if (inner === 'C') return 'mana-colorless';
        if (/^\d+$/.test(inner) || inner === 'X') return 'mana-generic';
        return 'mana-hybrid';
    }

    function getRarityClass(rarity: string): string {
        return `rarity-${rarity.toLowerCase()}`;
    }

    $effect(() => {
        if (printings.length > 0 && selectedPrintingIndex >= printings.length) {
            selectedPrintingIndex = 0;
        }
    });
</script>

<div class="explorer">
    <header class="explorer-header">
        <h1>Card Explorer</h1>
        <p>Search your card database with advanced filters</p>
    </header>

    <div class="search-section">
        <div class="search-bar">
            <input
                type="text"
                placeholder="Search by card name..."
                bind:value={filters.name}
                onkeydown={handleKeydown}
            />
            <button
                class="toggle-advanced"
                class:active={showAdvanced}
                onclick={() => (showAdvanced = !showAdvanced)}
                title="Advanced Search"
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="4" y1="6" x2="20" y2="6"></line>
                    <line x1="4" y1="12" x2="20" y2="12"></line>
                    <line x1="4" y1="18" x2="20" y2="18"></line>
                    <circle cx="8" cy="6" r="2" fill="currentColor"></circle>
                    <circle cx="16" cy="12" r="2" fill="currentColor"></circle>
                    <circle cx="10" cy="18" r="2" fill="currentColor"></circle>
                </svg>
            </button>
            <button
                class="search-btn"
                onclick={() => searchCards()}
                disabled={isLoading || !hasAnyFilter()}
            >
                {isLoading ? 'Searching...' : 'Search'}
            </button>
        </div>

        {#if showAdvanced}
            <div class="advanced-filters">
                <div class="filter-row">
                    <div class="filter-group">
                        <label for="filter-text">Oracle Text</label>
                        <input
                            id="filter-text"
                            type="text"
                            placeholder="Search card text..."
                            bind:value={filters.text}
                            onkeydown={handleKeydown}
                        />
                    </div>
                    <div class="filter-group">
                        <label for="filter-keywords">Keywords</label>
                        <input
                            id="filter-keywords"
                            type="text"
                            placeholder="Flying, Trample..."
                            bind:value={filters.keywords}
                            onkeydown={handleKeydown}
                        />
                    </div>
                </div>

                <div class="filter-row">
                    <div class="filter-group colors-group">
                        <span class="filter-label">Colors</span>
                        <div class="color-buttons">
                            {#each COLORS as color}
                                <button
                                    class="color-btn color-{color.code.toLowerCase()}"
                                    class:selected={filters.colors.has(color.code)}
                                    onclick={() => toggleColor(color.code)}
                                    title={color.name}
                                >
                                    <span class="color-symbol">{color.symbol}</span>
                                </button>
                            {/each}
                        </div>
                        <div class="color-match">
                            <select bind:value={filters.colorMatch}>
                                <option value="any">Any of these</option>
                                <option value="all">All of these</option>
                                <option value="exact">Exactly these</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="filter-row">
                    <div class="filter-group types-group">
                        <span class="filter-label">Card Types</span>
                        <div class="type-buttons">
                            {#each CARD_TYPES as type}
                                <button
                                    class="type-btn"
                                    class:selected={filters.types.has(type)}
                                    onclick={() => toggleType(type)}
                                >
                                    {type}
                                </button>
                            {/each}
                        </div>
                    </div>
                </div>

                <div class="filter-row">
                    <div class="filter-group rarity-group">
                        <span class="filter-label">Rarity</span>
                        <div class="rarity-buttons">
                            {#each RARITIES as rarity}
                                <button
                                    class="rarity-btn rarity-{rarity.code}"
                                    class:selected={filters.rarity.has(rarity.code)}
                                    onclick={() => toggleRarity(rarity.code)}
                                >
                                    {rarity.name}
                                </button>
                            {/each}
                        </div>
                    </div>
                    <div class="filter-group cmc-group">
                        <span class="filter-label">Mana Value (CMC)</span>
                        <div class="cmc-inputs">
                            <label class="sr-only" for="cmc-min">Minimum CMC</label>
                            <input
                                id="cmc-min"
                                type="number"
                                placeholder="Min"
                                min="0"
                                bind:value={filters.cmcMin}
                                onkeydown={handleKeydown}
                            />
                            <span>to</span>
                            <label class="sr-only" for="cmc-max">Maximum CMC</label>
                            <input
                                id="cmc-max"
                                type="number"
                                placeholder="Max"
                                min="0"
                                bind:value={filters.cmcMax}
                                onkeydown={handleKeydown}
                            />
                        </div>
                    </div>
                </div>

                <div class="filter-actions">
                    <button class="clear-btn" onclick={clearFilters}>Clear Filters</button>
                </div>
            </div>
        {/if}
    </div>

    <div class="results-area">
        {#if isLoading}
            <div class="loading-state">
                <div class="spinner"></div>
                <span>Searching cards...</span>
            </div>
        {:else if hasSearched && cards.length === 0}
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <p>No cards found matching your criteria.</p>
                <span>Try adjusting your filters or search terms.</span>
            </div>
        {:else if !hasSearched}
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="3" width="18" height="18" rx="2"></rect>
                    <line x1="9" y1="9" x2="15" y2="15"></line>
                    <line x1="15" y1="9" x2="9" y2="15"></line>
                </svg>
                <p>Enter search criteria to find cards.</p>
                <span>Use the advanced filters for more specific searches.</span>
            </div>
        {:else}
            <div class="results-header">
                <span class="results-count">
                    {#if pagination}
                        {pagination.total_cards} card{pagination.total_cards !== 1 ? 's' : ''} found
                        {#if pagination.total_pages > 1}
                            <span class="page-info">(page {pagination.page} of {pagination.total_pages})</span>
                        {/if}
                    {:else}
                        {cards.length} card{cards.length !== 1 ? 's' : ''} found
                    {/if}
                </span>
            </div>
            <div class="card-grid">
                {#each cards as card}
                    <button class="card-item" onclick={() => selectCard(card)}>
                        <div class="card-image-container">
                            {#if getCardImage(card)}
                                <img src={getCardImage(card)} alt={card.name} loading="lazy" />
                            {:else}
                                <div class="card-placeholder">
                                    <span class="placeholder-name">{card.name}</span>
                                </div>
                            {/if}
                            <div class="card-overlay">
                                <div class="overlay-header">
                                    <span class="card-name">{card.name}</span>
                                    <div class="mana-cost">
                                        {#each formatManaCost(card.mana_cost) as symbol}
                                            <span class="mana-symbol {getManaSymbolClass(symbol)}">{symbol.replace(/[{}]/g, '')}</span>
                                        {/each}
                                    </div>
                                </div>
                                <div class="overlay-footer">
                                    <span class="card-type">{card.type_line}</span>
                                    <span class="card-rarity {getRarityClass(card.rarity)}">{card.rarity}</span>
                                </div>
                            </div>
                        </div>
                    </button>
                {/each}
            </div>

            {#if pagination && pagination.total_pages > 1}
                {@const totalPages = pagination.total_pages}
                {@const hasPrev = pagination.has_prev}
                {@const hasNext = pagination.has_next}
                <div class="pagination">
                    <button
                        class="page-btn"
                        onclick={() => goToPage(1)}
                        disabled={!hasPrev}
                        title="First page"
                    >
                        ««
                    </button>
                    <button
                        class="page-btn"
                        onclick={() => goToPage(currentPage - 1)}
                        disabled={!hasPrev}
                        title="Previous page"
                    >
                        «
                    </button>

                    <div class="page-numbers">
                        {#each Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                            const start = Math.max(1, Math.min(currentPage - 2, totalPages - 4));
                            return start + i;
                        }).filter(p => p <= totalPages) as pageNum}
                            <button
                                class="page-num"
                                class:active={pageNum === currentPage}
                                onclick={() => goToPage(pageNum)}
                            >
                                {pageNum}
                            </button>
                        {/each}
                    </div>

                    <button
                        class="page-btn"
                        onclick={() => goToPage(currentPage + 1)}
                        disabled={!hasNext}
                        title="Next page"
                    >
                        »
                    </button>
                    <button
                        class="page-btn"
                        onclick={() => goToPage(totalPages)}
                        disabled={!hasNext}
                        title="Last page"
                    >
                        »»
                    </button>
                </div>
            {/if}
        {/if}
    </div>
</div>

{#if selectedCard}
    <div class="card-modal" onclick={closeModal} role="dialog" aria-modal="true">
        <div class="modal-content" onclick={(e) => e.stopPropagation()}>
            <button class="close-btn" onclick={closeModal}>×</button>

            {#if selectedCard}
            {@const faceSource = printings.length > 0 ? printings[selectedPrintingIndex] : selectedCard}
            {@const faceIdx = showingBackFace ? 1 : 0}
            {@const face = getFaceData(selectedCard, faceIdx)}
            <div class="modal-layout">
                <div class="modal-image">
                    {#if isDFC(faceSource)}
                        <img src={getFaceImage(faceSource, faceIdx, 'large')} alt={face.name} />
                        <button class="flip-btn" onclick={() => showingBackFace = !showingBackFace} title="Flip card">
                            &#x21BB;
                        </button>
                    {:else if printings.length > 0}
                        <img src={getCardImage(printings[selectedPrintingIndex], 'large')} alt={printings[selectedPrintingIndex].name} />
                    {:else if getCardImage(selectedCard, 'large')}
                        <img src={getCardImage(selectedCard, 'large')} alt={selectedCard.name} />
                    {:else}
                        <div class="card-placeholder large">
                            <span>{selectedCard.name}</span>
                        </div>
                    {/if}
                </div>

                <div class="modal-details">
                    <div class="detail-header">
                        <h2>{face.name}</h2>
                        <div class="mana-cost large">
                            {#each formatManaCost(face.mana_cost) as symbol}
                                <span class="mana-symbol {getManaSymbolClass(symbol)}">{symbol.replace(/[{}]/g, '')}</span>
                            {/each}
                        </div>
                    </div>

                    <div class="detail-type">
                        <span class="type-line">{face.type_line}</span>
                        <span class="rarity-badge {getRarityClass(selectedCard.rarity)}">{selectedCard.rarity}</span>
                    </div>

                    {#if face.oracle_text}
                        <div class="oracle-text">
                            {#each face.oracle_text.split('\n') as paragraph}
                                <p>{paragraph}</p>
                            {/each}
                        </div>
                    {/if}

                    {#if face.power && face.toughness}
                        <div class="power-toughness">
                            {face.power} / {face.toughness}
                        </div>
                    {/if}

                    {#if selectedCard.keywords && selectedCard.keywords.length > 0}
                        <div class="keywords">
                            {#each selectedCard.keywords as keyword}
                                <span class="keyword-tag">{keyword}</span>
                            {/each}
                        </div>
                    {/if}

                    <div class="card-stats">
                        <div class="stat">
                            <span class="stat-label">Mana Value</span>
                            <span class="stat-value">{selectedCard.cmc}</span>
                        </div>
                        {#if selectedCard.colors && selectedCard.colors.length > 0}
                            <div class="stat">
                                <span class="stat-label">Colors</span>
                                <span class="stat-value color-icons">
                                    {#each selectedCard.colors as color}
                                        <span class="color-dot color-{color.toLowerCase()}"></span>
                                    {/each}
                                </span>
                            </div>
                        {/if}
                    </div>

                    {#if loadingPrintings}
                        <div class="printings-loading">Loading printings...</div>
                    {:else if printings.length > 0}
                        <div class="printings-section">
                            <div class="printings-header">
                                <span class="printings-label">{printings.length} printings</span>
                                <span class="current-set">{printings[selectedPrintingIndex].set_name}</span>
                            </div>
                            <div class="printings-grid">
                                {#each printings as printing, index}
                                    <button
                                        class="printing-thumb"
                                        class:selected={index === selectedPrintingIndex}
                                        onclick={() => selectPrinting(index)}
                                        title="{printing.set_name} ({printing.released_at})"
                                    >
                                        <img src={printing.image_uris?.small || printing.card_faces?.[0]?.image_uris?.small || ''} alt={printing.set_name} />
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {:else if selectedCard.set_name}
                        <div class="set-info">
                            <span class="set-label">Set:</span>
                            <span class="set-name">{selectedCard.set_name}</span>
                        </div>
                    {/if}
                </div>
            </div>
            {/if}
        </div>
    </div>
{/if}

<style>
    .explorer {
        padding: 2rem 3rem;
        max-width: 1600px;
        margin: 0 auto;
    }

    .explorer-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .explorer-header h1 {
        margin: 0;
        color: hsl(var(--foreground));
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.025em;
    }

    .explorer-header p {
        color: hsl(var(--muted-foreground));
        margin-top: 0.5rem;
        font-size: 1rem;
    }

    /* Search Section */
    .search-section {
        max-width: 900px;
        margin: 0 auto 2rem;
    }

    .search-bar {
        display: flex;
        gap: 0.5rem;
    }

    .search-bar input {
        flex: 1;
        padding: 0.875rem 1.25rem;
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-md);
        font-size: 0.95rem;
        background: hsl(var(--secondary));
        color: hsl(var(--foreground));
    }

    .search-bar input::placeholder {
        color: hsl(var(--muted-foreground));
    }

    .search-bar input:focus {
        outline: none;
        border-color: hsl(var(--ring));
        box-shadow: 0 0 0 3px hsl(var(--ring) / 0.2);
    }

    .toggle-advanced {
        padding: 0.875rem;
        background: hsl(var(--secondary));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-md);
        cursor: pointer;
        color: hsl(var(--muted-foreground));
        transition: all var(--transition-fast);
    }

    .toggle-advanced:hover,
    .toggle-advanced.active {
        background: hsl(var(--accent));
        color: hsl(var(--foreground));
        border-color: hsl(var(--ring));
    }

    .search-btn {
        padding: 0.875rem 1.75rem;
        background: hsl(var(--primary));
        color: hsl(var(--primary-foreground));
        border: none;
        border-radius: var(--radius-md);
        font-size: 0.95rem;
        font-weight: 600;
        cursor: pointer;
        transition: all var(--transition-fast);
    }

    .search-btn:hover:not(:disabled) {
        opacity: 0.9;
    }

    .search-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    /* Advanced Filters */
    .advanced-filters {
        margin-top: 1rem;
        padding: 1.5rem;
        background: hsl(var(--card));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-lg);
    }

    .filter-row {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1.25rem;
    }

    .filter-row:last-of-type {
        margin-bottom: 0;
    }

    .filter-group {
        flex: 1;
    }

    .filter-group label,
    .filter-label {
        display: block;
        font-size: 0.85rem;
        font-weight: 500;
        color: hsl(var(--muted-foreground));
        margin-bottom: 0.5rem;
    }

    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }

    .filter-group input {
        width: 100%;
        padding: 0.625rem 0.875rem;
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-md);
        font-size: 0.9rem;
        background: hsl(var(--secondary));
        color: hsl(var(--foreground));
    }

    .filter-group input:focus {
        outline: none;
        border-color: hsl(var(--ring));
    }

    /* Color Buttons */
    .colors-group {
        flex: 2;
    }

    .color-buttons {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .color-btn {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 2px solid hsl(var(--border));
        cursor: pointer;
        transition: all var(--transition-fast);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
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
        box-shadow: 0 0 0 3px hsl(var(--primary) / 0.3);
    }

    .color-match select {
        padding: 0.5rem 0.75rem;
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-md);
        font-size: 0.85rem;
        background: hsl(var(--secondary));
        color: hsl(var(--foreground));
    }

    /* Type Buttons */
    .type-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .type-btn {
        padding: 0.5rem 1rem;
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-md);
        background: hsl(var(--secondary));
        color: hsl(var(--muted-foreground));
        font-size: 0.85rem;
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
        gap: 0.5rem;
    }

    .rarity-btn {
        padding: 0.5rem 1rem;
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-md);
        background: hsl(var(--secondary));
        font-size: 0.85rem;
        cursor: pointer;
        transition: all var(--transition-fast);
    }

    .rarity-btn.rarity-common { color: #1a1a1a; }
    .rarity-btn.rarity-uncommon { color: #607d8b; }
    .rarity-btn.rarity-rare { color: #b8860b; }
    .rarity-btn.rarity-mythic { color: #d84315; }

    .rarity-btn:hover {
        border-color: hsl(var(--muted-foreground));
    }

    .rarity-btn.selected {
        border-width: 2px;
    }

    .rarity-btn.selected.rarity-common { background: #e0e0e0; border-color: #1a1a1a; }
    .rarity-btn.selected.rarity-uncommon { background: #cfd8dc; border-color: #607d8b; }
    .rarity-btn.selected.rarity-rare { background: #fff8e1; border-color: #b8860b; }
    .rarity-btn.selected.rarity-mythic { background: #ffebee; border-color: #d84315; }

    /* CMC Group */
    .cmc-group {
        max-width: 200px;
    }

    .cmc-inputs {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .cmc-inputs input {
        width: 70px;
        padding: 0.5rem;
        text-align: center;
    }

    .cmc-inputs span {
        color: hsl(var(--muted-foreground));
        font-size: 0.85rem;
    }

    /* Filter Actions */
    .filter-actions {
        margin-top: 1.25rem;
        padding-top: 1rem;
        border-top: 1px solid hsl(var(--border));
        display: flex;
        justify-content: flex-end;
    }

    .clear-btn {
        padding: 0.5rem 1rem;
        background: transparent;
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-md);
        color: hsl(var(--muted-foreground));
        font-size: 0.85rem;
        cursor: pointer;
        transition: all var(--transition-fast);
    }

    .clear-btn:hover {
        background: hsl(var(--destructive) / 0.1);
        border-color: hsl(var(--destructive));
        color: hsl(var(--destructive));
    }

    /* Results Area */
    .results-area {
        min-height: 400px;
    }

    .results-header {
        margin-bottom: 1rem;
    }

    .results-count {
        font-size: 0.9rem;
        color: hsl(var(--muted-foreground));
    }

    .page-info {
        color: hsl(var(--muted-foreground) / 0.7);
        font-size: 0.85rem;
    }

    .pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.5rem;
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid hsl(var(--border));
    }

    .page-btn {
        padding: 0.5rem 0.75rem;
        background: hsl(var(--secondary));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-md);
        color: hsl(var(--foreground));
        font-size: 0.9rem;
        cursor: pointer;
        transition: all var(--transition-fast);
    }

    .page-btn:hover:not(:disabled) {
        background: hsl(var(--accent));
        border-color: hsl(var(--ring));
    }

    .page-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .page-numbers {
        display: flex;
        gap: 0.25rem;
    }

    .page-num {
        min-width: 36px;
        height: 36px;
        padding: 0;
        background: hsl(var(--secondary));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-md);
        color: hsl(var(--foreground));
        font-size: 0.9rem;
        cursor: pointer;
        transition: all var(--transition-fast);
    }

    .page-num:hover:not(.active) {
        background: hsl(var(--accent));
        border-color: hsl(var(--ring));
    }

    .page-num.active {
        background: hsl(var(--primary));
        color: hsl(var(--primary-foreground));
        border-color: hsl(var(--primary));
    }

    .loading-state,
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: hsl(var(--muted-foreground));
    }

    .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid hsl(var(--border));
        border-top-color: hsl(var(--primary));
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .empty-state svg {
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    .empty-state p {
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        color: hsl(var(--foreground));
    }

    .empty-state span {
        font-size: 0.9rem;
    }

    /* Card Grid */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 1.5rem;
    }

    .card-item {
        background: none;
        border: none;
        padding: 0;
        cursor: pointer;
        transition: transform var(--transition-fast);
    }

    .card-item:hover {
        transform: translateY(-4px);
    }

    .card-image-container {
        position: relative;
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-md);
    }

    .card-image-container img {
        width: 100%;
        display: block;
    }

    .card-overlay {
        position: absolute;
        inset: 0;
        background: linear-gradient(
            to top,
            rgba(0, 0, 0, 0.9) 0%,
            rgba(0, 0, 0, 0.4) 30%,
            rgba(0, 0, 0, 0) 50%,
            rgba(0, 0, 0, 0.4) 80%,
            rgba(0, 0, 0, 0.7) 100%
        );
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 0.75rem;
        opacity: 0;
        transition: opacity var(--transition-fast);
    }

    .card-item:hover .card-overlay {
        opacity: 1;
    }

    .overlay-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.5rem;
    }

    .card-name {
        font-weight: 600;
        font-size: 0.85rem;
        color: #fff;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
    }

    .mana-cost {
        display: flex;
        gap: 2px;
        flex-shrink: 0;
    }

    .mana-symbol {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }

    .mana-white { background: #fffbd5; color: #9b8e4e; }
    .mana-blue { background: #0e68ab; color: #fff; }
    .mana-black { background: #150b00; color: #a08c7e; }
    .mana-red { background: #d32029; color: #fff; }
    .mana-green { background: #00733e; color: #fff; }
    .mana-colorless { background: #a8a8a8; color: #4a4a4a; }
    .mana-generic { background: #ccc; color: #333; }
    .mana-hybrid { background: linear-gradient(135deg, #ffd700, #c0c0c0); color: #333; }

    .overlay-footer {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }

    .card-type {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.9);
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
    }

    .card-rarity {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        padding: 0.2rem 0.5rem;
        border-radius: var(--radius-sm);
    }

    .rarity-common { background: #e0e0e0; color: #1a1a1a; }
    .rarity-uncommon { background: #607d8b; color: #fff; }
    .rarity-rare { background: #b8860b; color: #fff; }
    .rarity-mythic { background: #d84315; color: #fff; }

    .card-placeholder {
        aspect-ratio: 488 / 680;
        background: hsl(var(--secondary));
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
    }

    .placeholder-name {
        text-align: center;
        color: hsl(var(--muted-foreground));
        font-size: 0.9rem;
        font-weight: 500;
    }

    /* Modal */
    .card-modal {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        padding: 2rem;
    }

    .modal-content {
        position: relative;
        background: hsl(var(--card));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-xl);
        max-width: 900px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: var(--shadow-lg);
    }

    .close-btn {
        position: absolute;
        top: 1rem;
        right: 1rem;
        width: 36px;
        height: 36px;
        background: hsl(var(--secondary));
        border: none;
        border-radius: 50%;
        cursor: pointer;
        font-size: 1.5rem;
        color: hsl(var(--muted-foreground));
        transition: all var(--transition-fast);
        z-index: 10;
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1;
    }

    .close-btn:hover {
        background: hsl(var(--accent));
        color: hsl(var(--foreground));
    }

    .modal-layout {
        display: grid;
        grid-template-columns: 320px 1fr;
        gap: 2rem;
        padding: 2rem;
    }

    .modal-image {
        position: relative;
    }

    .modal-image img {
        width: 100%;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
    }

    .flip-btn {
        position: absolute;
        bottom: 0.5rem;
        right: 0.5rem;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: hsl(0 0% 0% / 0.7);
        color: white;
        border: 2px solid hsl(0 0% 100% / 0.3);
        font-size: 1.25rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.15s ease;
        backdrop-filter: blur(4px);
    }

    .flip-btn:hover {
        background: hsl(var(--primary));
        border-color: hsl(var(--primary));
        transform: rotate(180deg);
    }

    .modal-image .card-placeholder.large {
        height: 446px;
        border-radius: var(--radius-lg);
    }

    .modal-details {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .detail-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
    }

    .detail-header h2 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: hsl(var(--foreground));
    }

    .mana-cost.large .mana-symbol {
        width: 24px;
        height: 24px;
        font-size: 0.85rem;
    }

    .detail-type {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .type-line {
        font-size: 1rem;
        color: hsl(var(--muted-foreground));
    }

    .rarity-badge {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        padding: 0.25rem 0.75rem;
        border-radius: var(--radius-md);
    }

    .oracle-text {
        background: hsl(var(--secondary));
        padding: 1.25rem;
        border-radius: var(--radius-md);
        border-left: 3px solid hsl(var(--primary));
    }

    .oracle-text p {
        margin: 0 0 0.75rem 0;
        font-size: 0.95rem;
        line-height: 1.6;
        color: hsl(var(--foreground));
    }

    .oracle-text p:last-child {
        margin-bottom: 0;
    }

    .power-toughness {
        display: inline-flex;
        align-self: flex-start;
        padding: 0.5rem 1rem;
        background: hsl(var(--secondary));
        border: 2px solid hsl(var(--border));
        border-radius: var(--radius-md);
        font-size: 1.25rem;
        font-weight: 700;
        color: hsl(var(--foreground));
    }

    .keywords {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .keyword-tag {
        padding: 0.35rem 0.75rem;
        background: hsl(var(--accent));
        border-radius: var(--radius-md);
        font-size: 0.8rem;
        color: hsl(var(--accent-foreground));
    }

    .card-stats {
        display: flex;
        gap: 2rem;
        padding: 1rem;
        background: hsl(var(--secondary));
        border-radius: var(--radius-md);
    }

    .stat {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .stat-label {
        font-size: 0.75rem;
        color: hsl(var(--muted-foreground));
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stat-value {
        font-size: 1rem;
        font-weight: 600;
        color: hsl(var(--foreground));
    }

    .color-icons {
        display: flex;
        gap: 0.25rem;
    }

    .color-dot {
        width: 16px;
        height: 16px;
        border-radius: 50%;
    }

    .color-dot.color-w { background: #fffbd5; border: 1px solid #9b8e4e; }
    .color-dot.color-u { background: #0e68ab; }
    .color-dot.color-b { background: #150b00; }
    .color-dot.color-r { background: #d32029; }
    .color-dot.color-g { background: #00733e; }

    .printings-loading {
        font-size: 0.9rem;
        color: hsl(var(--muted-foreground));
        padding: 1rem;
        text-align: center;
    }

    .printings-section {
        border-top: 1px solid hsl(var(--border));
        padding-top: 1rem;
    }

    .printings-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }

    .printings-label {
        font-size: 0.85rem;
        color: hsl(var(--muted-foreground));
    }

    .current-set {
        font-size: 0.85rem;
        font-weight: 500;
        color: hsl(var(--foreground));
    }

    .printings-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
        gap: 0.5rem;
        max-height: 180px;
        overflow-y: auto;
        padding: 0.5rem;
        background: hsl(var(--secondary));
        border-radius: var(--radius-md);
    }

    .printing-thumb {
        background: none;
        border: 2px solid transparent;
        border-radius: var(--radius-sm);
        padding: 0;
        cursor: pointer;
        transition: all var(--transition-fast);
    }

    .printing-thumb:hover {
        border-color: hsl(var(--muted-foreground));
    }

    .printing-thumb.selected {
        border-color: hsl(var(--primary));
    }

    .printing-thumb img {
        width: 100%;
        border-radius: var(--radius-sm);
        display: block;
    }

    .set-info {
        display: flex;
        gap: 0.5rem;
        font-size: 0.9rem;
    }

    .set-label {
        color: hsl(var(--muted-foreground));
    }

    .set-name {
        color: hsl(var(--foreground));
        font-weight: 500;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .explorer {
            padding: 1.5rem;
        }

        .modal-layout {
            grid-template-columns: 1fr;
            padding: 1.5rem;
        }

        .modal-image {
            max-width: 280px;
            margin: 0 auto;
        }

        .card-grid {
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 1rem;
        }

        .filter-row {
            flex-direction: column;
            gap: 1rem;
        }

        .colors-group {
            flex: 1;
        }

        .cmc-group {
            max-width: none;
        }
    }
</style>
