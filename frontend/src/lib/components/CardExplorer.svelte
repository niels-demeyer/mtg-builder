<script lang="ts">
    import type { DbCard } from '$lib/types';

    let searchQuery = $state('');
    let cards = $state<DbCard[]>([]);
    let isLoading = $state(false);
    let hasSearched = $state(false);
    let selectedCard = $state<DbCard | null>(null);


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
</script> <style> .explorer { padding: 3rem; max-width: 1400px; margin: 0 auto; } .explorer-header { text-align: center; margin-bottom: 2.5rem;
  }

  .explorer-header h1 {
    margin: 0;
    color: var(--color-text);
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.025em;
  }

  .explorer-header p {
    color: var(--color-text-secondary);
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
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    background: var(--color-bg-tertiary);
    color: var(--color-text);
  }

  .search-bar input::placeholder {
    color: var(--color-text-muted);
  }

  .search-bar input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px var(--color-primary-muted);
  }

  .search-bar button {
    padding: 0.875rem 1.75rem;
    background: var(--color-primary);
    color: var(--color-bg);
    border: none;
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .search-bar button:hover:not(:disabled) {
    background: var(--color-primary-hover);
    box-shadow: var(--shadow-glow);
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
    color: var(--color-text-muted);
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
    background: var(--color-bg-tertiary);
    border: 1px solid var(--color-border);
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
    background: var(--color-bg-hover);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1rem;
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);
  }

  .close-btn:hover {
    background: var(--color-border);
    color: var(--color-text);
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
    color: var(--color-text);
    font-size: 1.25rem;
    font-weight: 600;
  }

  .type {
    color: var(--color-text-secondary);
    margin: 0.5rem 0;
    font-size: 0.9rem;
  }

  .oracle {
    background: var(--color-bg-secondary);
    padding: 1rem;
    border-radius: var(--radius-md);
    font-style: italic;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
    line-height: 1.6;
    margin: 0.5rem 0;
  }

  .set {
    color: var(--color-text-muted);
    font-size: 0.85rem;
    margin: 0.5rem 0;
  }

  .price {
    color: var(--color-success);
    font-weight: 700;
    font-size: 1.25rem;
    margin: 0.5rem 0;
  }
</style>
