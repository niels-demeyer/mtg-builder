<script lang="ts">
  import { deckStore } from '../../stores/deckStore';
  import { currentUser } from '../../stores/authStore';
  import type { Deck } from '$lib/types';
  import ResizeHandle from './ResizeHandle.svelte';

  interface Props {
    onNavigate: (view: string) => void;
    onSelectDeck?: (deckId: string) => void;
    currentView?: string;
    width?: number;
    onResize?: (delta: number) => void;
  }

  let { onNavigate, onSelectDeck, currentView = 'home', width = 260, onResize }: Props = $props();

  let user = $derived($currentUser);

  let folders = $derived($deckStore.folders);
  let decks = $derived($deckStore.decks);
  let currentDeck = $derived($deckStore.currentDeck);
  
  let expandedFolders = $state<Set<string>>(new Set());
  let showNewFolderInput = $state(false);
  let newFolderName = $state('');
  let showAccountMenu = $state(false);
  let deckSearchQuery = $state('');

  const mainMenuItems = [
    { id: 'home', label: 'Home', icon: '⌂' },
    { id: 'explorer', label: 'Card Explorer', icon: '◎' },
    { id: 'training', label: 'Training', icon: '◈' },
  ];

  function toggleFolder(folderId: string): void {
    const newSet = new Set(expandedFolders);
    if (newSet.has(folderId)) {
      newSet.delete(folderId);
    } else {
      newSet.add(folderId);
    }
    expandedFolders = newSet;
  }

  function createFolder(): void {
    if (newFolderName.trim()) {
      deckStore.createFolder(newFolderName.trim());
      newFolderName = '';
      showNewFolderInput = false;
    }
  }

  function handleFolderKeydown(e: KeyboardEvent): void {
    if (e.key === 'Enter') {
      createFolder();
    } else if (e.key === 'Escape') {
      showNewFolderInput = false;
      newFolderName = '';
    }
  }

  function getDecksInFolder(folderId?: string): Deck[] {
    return decks.filter(d => d.folderId === folderId);
  }

  function getUnfiledDecks(): Deck[] {
    return decks.filter(d => !d.folderId);
  }

  function selectDeck(deck: Deck): void {
    deckStore.selectDeck(deck.id);
    if (onSelectDeck) {
      onSelectDeck(deck.id);
    }
    onNavigate('builder');
  }

  function deleteFolder(folderId: string, e: MouseEvent): void {
    e.stopPropagation();
    if (confirm('Delete this folder? Decks will be moved to unfiled.')) {
      deckStore.deleteFolder(folderId);
    }
  }

  let filteredDecks = $derived(
    deckSearchQuery.trim() 
      ? decks.filter(d => d.name.toLowerCase().includes(deckSearchQuery.toLowerCase()))
      : null
  );

  function getDeckCardCount(deck: Deck): number {
    return deck.cards.reduce((sum, c) => sum + c.quantity, 0);
  }

  function handleResize(delta: number): void {
    if (onResize) {
      onResize(delta);
    }
  }
</script>

<div class="sidebar-container">
  <aside class="sidebar" style="width: {width}px">
  <div class="logo">
    <div class="logo-icon">✦</div>
    <span class="logo-text">MTG Builder</span>
  </div>

  <nav class="nav-menu">
    {#each mainMenuItems as item}
      <button
        class="nav-item"
        class:active={currentView === item.id}
        onclick={() => onNavigate(item.id)}
      >
        <span class="icon">{item.icon}</span>
        <span class="label">{item.label}</span>
      </button>
    {/each}
  </nav>

  <div class="decks-section">
    <div class="section-header">
      <span class="section-title">My Decks</span>
      <div class="section-actions">
        <button 
          class="icon-btn" 
          title="New Folder"
          onclick={() => showNewFolderInput = !showNewFolderInput}
        >
          📁
        </button>
        <button 
          class="icon-btn" 
          title="New Deck"
          onclick={() => onNavigate('new-deck')}
        >
          +
        </button>
      </div>
    </div>

    <div class="deck-search">
      <input 
        type="text" 
        placeholder="Search decks..." 
        bind:value={deckSearchQuery}
      />
    </div>

    {#if showNewFolderInput}
      <div class="new-folder-input">
        <input
          type="text"
          placeholder="Folder name..."
          bind:value={newFolderName}
          onkeydown={handleFolderKeydown}
        />
        <button class="create-btn" onclick={createFolder}>✓</button>
        <button class="cancel-btn" onclick={() => { showNewFolderInput = false; newFolderName = ''; }}>✕</button>
      </div>
    {/if}

    <div class="deck-tree">
      {#if filteredDecks}
        <!-- Search results -->
        <div class="search-results">
          {#each filteredDecks as deck}
            <button 
              class="deck-item"
              class:active={currentDeck?.id === deck.id}
              onclick={() => selectDeck(deck)}
            >
              <span class="deck-icon">▤</span>
              <span class="deck-name">{deck.name}</span>
              <span class="deck-count">{getDeckCardCount(deck)}</span>
            </button>
          {/each}
          {#if filteredDecks.length === 0}
            <p class="no-results">No decks found</p>
          {/if}
        </div>
      {:else}
        <!-- Folders -->
        {#each folders as folder}
          <div class="folder-group">
            <div class="folder-header-wrapper">
              <button 
                class="folder-header"
                onclick={() => toggleFolder(folder.id)}
              >
                <span class="folder-icon">{expandedFolders.has(folder.id) ? '📂' : '📁'}</span>
                <span class="folder-name">{folder.name}</span>
                <span class="folder-count">{getDecksInFolder(folder.id).length}</span>
              </button>
              <button 
                class="delete-folder-btn"
                onclick={(e) => deleteFolder(folder.id, e)}
                title="Delete folder"
              >✕</button>
            </div>
            {#if expandedFolders.has(folder.id)}
              <div class="folder-contents">
                {#each getDecksInFolder(folder.id) as deck}
                  <button 
                    class="deck-item"
                    class:active={currentDeck?.id === deck.id}
                    onclick={() => selectDeck(deck)}
                  >
                    <span class="deck-icon">▤</span>
                    <span class="deck-name">{deck.name}</span>
                    <span class="deck-count">{getDeckCardCount(deck)}</span>
                  </button>
                {/each}
              </div>
            {/if}
          </div>
        {/each}

        <!-- Unfiled decks -->
        {#if getUnfiledDecks().length > 0}
          <div class="unfiled-decks">
            {#if folders.length > 0}
              <div class="unfiled-label">Unfiled</div>
            {/if}
            {#each getUnfiledDecks() as deck}
              <button 
                class="deck-item"
                class:active={currentDeck?.id === deck.id}
                onclick={() => selectDeck(deck)}
              >
                <span class="deck-icon">▤</span>
                <span class="deck-name">{deck.name}</span>
                <span class="deck-count">{getDeckCardCount(deck)}</span>
              </button>
            {/each}
          </div>
        {/if}

        {#if decks.length === 0}
          <p class="no-decks">No decks yet. Create one!</p>
        {/if}
      {/if}
    </div>
  </div>

  <div class="sidebar-footer">
    <div class="separator"></div>
    
    <button
      class="account-btn"
      onclick={() => showAccountMenu = !showAccountMenu}
    >
      <span class="account-avatar">👤</span>
      <span class="account-label">{user?.username || 'Account'}</span>
      <span class="chevron">{showAccountMenu ? '▲' : '▼'}</span>
    </button>

    {#if showAccountMenu}
      <div class="account-menu">
        <button class="account-menu-item" onclick={() => onNavigate('settings')}>
          <span>⚙</span> Settings
        </button>
        <button class="account-menu-item" onclick={() => onNavigate('collection')}>
          <span>📚</span> My Collection
        </button>
        <button class="account-menu-item" onclick={() => onNavigate('import-export')}>
          <span>↕</span> Import/Export
        </button>
        <div class="menu-separator"></div>
        <button class="account-menu-item logout" onclick={() => onNavigate('logout')}>
          <span>↪</span> Sign Out
        </button>
      </div>
    {/if}
  </div>
</aside>
  {#if onResize}
    <ResizeHandle direction="horizontal" onResize={handleResize} />
  {/if}
</div>

<style>
  .sidebar-container {
    display: flex;
    flex-shrink: 0;
  }

  .sidebar {
    min-width: 200px;
    max-width: 400px;
    background: hsl(var(--card));
    display: flex;
    flex-direction: column;
    border-right: 1px solid hsl(var(--border));
    height: 100vh;
    overflow: hidden;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1rem 0.75rem;
    flex-shrink: 0;
  }

  .logo-icon {
    width: 32px;
    height: 32px;
    background: hsl(var(--foreground));
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    color: hsl(var(--background));
  }

  .logo-text {
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: -0.025em;
    color: hsl(var(--foreground));
  }

  .nav-menu {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    padding: 0.5rem 0.75rem;
    flex-shrink: 0;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
    text-align: left;
  }

  .nav-item:hover {
    background: hsl(var(--accent));
    color: hsl(var(--accent-foreground));
  }

  .nav-item.active {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .icon {
    font-size: 1rem;
    width: 1.25rem;
    text-align: center;
    opacity: 0.8;
  }

  .decks-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: 0.5rem 0.75rem;
    border-top: 1px solid hsl(var(--border));
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0.25rem;
    flex-shrink: 0;
  }

  .section-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: hsl(var(--muted-foreground));
  }

  .section-actions {
    display: flex;
    gap: 0.25rem;
  }

  .icon-btn {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.875rem;
    transition: all var(--transition-fast);
  }

  .icon-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .deck-search {
    padding: 0.25rem 0;
    flex-shrink: 0;
  }

  .deck-search input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-md);
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
  }

  .deck-search input::placeholder {
    color: hsl(var(--muted-foreground));
  }

  .deck-search input:focus {
    outline: none;
    border-color: hsl(var(--ring));
  }

  .new-folder-input {
    display: flex;
    gap: 0.25rem;
    padding: 0.25rem 0;
    flex-shrink: 0;
  }

  .new-folder-input input {
    flex: 1;
    padding: 0.375rem 0.5rem;
    background: hsl(var(--secondary));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius-sm);
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
  }

  .new-folder-input input:focus {
    outline: none;
    border-color: hsl(var(--ring));
  }

  .create-btn, .cancel-btn {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.875rem;
    transition: all var(--transition-fast);
  }

  .create-btn {
    background: hsl(var(--success));
    color: hsl(var(--success-foreground));
  }

  .cancel-btn {
    background: hsl(var(--secondary));
    color: hsl(var(--muted-foreground));
  }

  .deck-tree {
    flex: 1;
    overflow-y: auto;
    padding: 0.25rem 0;
  }

  .folder-group {
    margin-bottom: 0.25rem;
  }

  .folder-header-wrapper {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .folder-header-wrapper:hover .delete-folder-btn {
    opacity: 1;
  }

  .folder-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
    padding: 0.5rem 0.5rem;
    background: transparent;
    border: none;
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
    text-align: left;
  }

  .folder-header:hover {
    background: hsl(var(--accent));
  }

  .folder-icon {
    font-size: 0.875rem;
  }

  .folder-name {
    flex: 1;
  }

  .folder-count {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    background: hsl(var(--secondary));
    padding: 0.125rem 0.375rem;
    border-radius: var(--radius-full);
  }

  .delete-folder-btn {
    opacity: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    color: hsl(var(--destructive));
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.75rem;
    transition: all var(--transition-fast);
  }

  .delete-folder-btn:hover {
    background: hsl(var(--destructive) / 0.1);
  }

  .folder-contents {
    padding-left: 1.25rem;
  }

  .deck-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.375rem 0.5rem;
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    cursor: pointer;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
    text-align: left;
  }

  .deck-item:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .deck-item.active {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .deck-icon {
    font-size: 0.875rem;
    opacity: 0.7;
  }

  .deck-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .deck-count {
    font-size: 0.6875rem;
    color: hsl(var(--muted-foreground));
  }

  .unfiled-label {
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: hsl(var(--muted-foreground));
    padding: 0.5rem 0.5rem 0.25rem;
    margin-top: 0.5rem;
  }

  .no-decks, .no-results {
    text-align: center;
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    padding: 1.5rem 0.5rem;
  }

  .sidebar-footer {
    padding: 0.5rem 0.75rem 0.75rem;
    flex-shrink: 0;
  }

  .separator {
    height: 1px;
    background: hsl(var(--border));
    margin-bottom: 0.5rem;
  }

  .account-btn {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.5rem;
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    cursor: pointer;
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
    text-align: left;
  }

  .account-btn:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .account-avatar {
    font-size: 1rem;
  }

  .account-label {
    flex: 1;
  }

  .chevron {
    font-size: 0.625rem;
    opacity: 0.6;
  }

  .account-menu {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    padding: 0.25rem 0;
  }

  .account-menu-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.75rem;
    background: transparent;
    border: none;
    color: hsl(var(--muted-foreground));
    font-size: 0.8125rem;
    cursor: pointer;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
    text-align: left;
  }

  .account-menu-item:hover {
    background: hsl(var(--accent));
    color: hsl(var(--foreground));
  }

  .menu-separator {
    height: 1px;
    background: hsl(var(--border));
    margin: 0.25rem 0.5rem;
  }

  .account-menu-item.logout {
    color: hsl(var(--destructive));
  }

  .account-menu-item.logout:hover {
    background: hsl(var(--destructive) / 0.1);
    color: hsl(var(--destructive));
  }
</style>
