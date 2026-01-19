<script lang="ts">
    import type { DbCard } from '$lib/types';

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
        released_at: string;
    }

    let searchQuery = $state('');
    let cards = $state<DbCard[]>([]);
    let isLoading = $state(false);
    let hasSearched = $state(false);
    let selectedCard = $state<DbCard | null>(null);
    let printings = $state<Printing[]>([]);
    let loadingPrintings = $state(false);
    let selectedPrintingIndex = $state(0);

    async function searchCards(): Promise<void> {
        if (searchQuery.length < 2) return;

        isLoading = true;
        hasSearched = true;
        try {
            const response = await fetch(
                `http://localhost:8000/api/v1/search?q=${encodeURIComponent(searchQuery)}`
            );
            if (response.ok) {
                const data = await response.json();
                cards = data.data || [];
            } else {
                cards = [];
            }
        } catch {
            cards = [];
        } finally {
            isLoading = false;
        }
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

    function getCardImage(card: DbCard | Printing): string {
        if ('image_uri' in card) {
            return card.image_uri || card.image_uris?.normal || card.image_uris?.small || '';
        }
        return card.image_uris?.normal || card.image_uris?.small || '';
    }

    function selectPrinting(index: number): void {
        selectedPrintingIndex = index;
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
        <p>Search your card database</p>
    </header>

    <div class="search-bar">
        <input
            type="text"
            placeholder="Search for cards..."
            bind:value={searchQuery}
            onkeydown={handleKeydown}
        />
        <button onclick={searchCards} disabled={isLoading || searchQuery.length < 2}>
            {isLoading ? 'Searching...' : 'Search'}
        </button>
    </div>

    <div class="results-area">
        {#if isLoading}
            <div class="loading-state">Searching...</div>
        {:else if hasSearched && cards.length === 0}
            <div class="empty-state">No cards found. Try a different search term.</div>
        {:else if !hasSearched}
            <div class="empty-state">Enter a card name to search your database.</div>
        {:else}
            <div class="card-grid">
                {#each cards as card}
                    <button class="card-item" onclick={() => selectCard(card)}>
                        {#if getCardImage(card)}
                            <img src={getCardImage(card)} alt={card.name} />
                        {:else}
                            <div class="card-placeholder">{card.name}</div>
                        {/if}
                    </button>
                {/each}
            </div>
        {/if}
    </div>
</div>

{#if selectedCard}
    <div class="card-modal" onclick={closeModal} role="dialog" aria-modal="true">
        <div class="modal-content" onclick={(e) => e.stopPropagation()}>
            <button class="close-btn" onclick={closeModal}>✕</button>

            {#if printings.length > 0}
                <img src={getCardImage(printings[selectedPrintingIndex])} alt={printings[selectedPrintingIndex].name} />
            {:else if getCardImage(selectedCard)}
                <img src={getCardImage(selectedCard)} alt={selectedCard.name} />
            {/if}

            <div class="card-details">
                <h2>{selectedCard.name}</h2>
                {#if selectedCard.type_line}
                    <p class="type">{selectedCard.type_line}</p>
                {/if}
                {#if selectedCard.oracle_text}
                    <p class="oracle">{selectedCard.oracle_text}</p>
                {/if}

                {#if loadingPrintings}
                    <p class="set">Loading printings...</p>
                {:else if printings.length > 0}
                    <p class="set">{printings[selectedPrintingIndex].set_name} ({printings[selectedPrintingIndex].released_at})</p>
                    <div class="printings-section">
                        <p class="printings-label">{printings.length} printings available</p>
                        <div class="printings-grid">
                            {#each printings as printing, index}
                                <button
                                    class="printing-thumb"
                                    class:selected={index === selectedPrintingIndex}
                                    onclick={() => selectPrinting(index)}
                                    title="{printing.set_name} ({printing.released_at})"
                                >
                                    <img src={printing.image_uris?.small || ''} alt={printing.set_name} />
                                </button>
                            {/each}
                        </div>
                    </div>
                {:else if selectedCard.set_name}
                    <p class="set">{selectedCard.set_name}</p>
                {/if}
            </div>
        </div>
    </div>
{/if}

<style>
    .explorer {
        padding: 3rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    .explorer-header {
        text-align: center;
        margin-bottom: 2.5rem;
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

    .search-bar {
        display: flex;
        gap: 0.75rem;
        max-width: 640px;
        margin: 0 auto 2.5rem;
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

    .search-bar button {
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

    .search-bar button:hover:not(:disabled) {
        opacity: 0.9;
    }

    .search-bar button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .results-area {
        min-height: 400px;
    }

    .loading-state,
    .empty-state {
        text-align: center;
        padding: 4rem;
        color: hsl(var(--muted-foreground));
        font-size: 0.95rem;
    }

    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 1.25rem;
    }

    .card-item {
        background: none;
        border: none;
        padding: 0;
        cursor: pointer;
        transition: transform var(--transition-fast);
    }

    .card-item:hover {
        transform: scale(1.04);
    }

    .card-item img {
        width: 100%;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-md);
    }

    .card-placeholder {
        aspect-ratio: 488 / 680;
        background: hsl(var(--secondary));
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        text-align: center;
        color: hsl(var(--muted-foreground));
        font-size: 0.875rem;
    }

    .card-modal {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .modal-content {
        position: relative;
        background: hsl(var(--card));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius-xl);
        padding: 2rem;
        max-width: 520px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1.25rem;
        box-shadow: var(--shadow-lg);
    }

    .close-btn {
        position: absolute;
        top: 1rem;
        right: 1rem;
        width: 32px;
        height: 32px;
        background: hsl(var(--secondary));
        border: none;
        border-radius: 50%;
        cursor: pointer;
        font-size: 1rem;
        color: hsl(var(--muted-foreground));
        transition: all var(--transition-fast);
    }

    .close-btn:hover {
        background: hsl(var(--accent));
        color: hsl(var(--foreground));
    }

    .modal-content img {
        max-width: 280px;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-md);
    }

    .card-details {
        text-align: center;
        width: 100%;
    }

    .card-details h2 {
        margin: 0;
        color: hsl(var(--foreground));
        font-size: 1.25rem;
        font-weight: 600;
    }

    .type {
        color: hsl(var(--muted-foreground));
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }

    .oracle {
        background: hsl(var(--secondary));
        padding: 1rem;
        border-radius: var(--radius-md);
        font-style: italic;
        color: hsl(var(--muted-foreground));
        font-size: 0.9rem;
        line-height: 1.6;
        margin: 0.5rem 0;
    }

    .set {
        color: hsl(var(--muted-foreground));
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }

    .price {
        color: hsl(var(--success));
        font-weight: 700;
        font-size: 1.25rem;
        margin: 0.5rem 0;
    }

    .printings-section {
        margin-top: 1rem;
        width: 100%;
    }

    .printings-label {
        color: hsl(var(--muted-foreground));
        font-size: 0.85rem;
        margin-bottom: 0.75rem;
    }

    .printings-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
        gap: 0.5rem;
        max-height: 200px;
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

    .modal-content {
        max-height: 90vh;
        overflow-y: auto;
    }
</style>
