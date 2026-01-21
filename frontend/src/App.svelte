<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { deckStore } from './stores/deckStore';
  import { authStore, isAuthenticated } from './stores/authStore';
  import Sidebar from './lib/components/Sidebar.svelte';
  import Home from './lib/components/Home.svelte';
  import DeckList from './lib/components/DeckList.svelte';
  import DeckBuilder from './lib/components/DeckBuilder.svelte';
  import CardExplorer from './lib/components/CardExplorer.svelte';
  import Training from './lib/components/Training.svelte';
  import NewDeckModal from './lib/components/NewDeckModal.svelte';
  import Login from './lib/components/Login.svelte';
  import Register from './lib/components/Register.svelte';
  import type { Deck } from './lib/types';

  type ViewType = 'home' | 'decks' | 'builder' | 'explorer' | 'training' | 'settings' | 'collection' | 'import-export' | 'login' | 'register';

  const routes: Record<string, ViewType> = {
    '/': 'home',
    '/home': 'home',
    '/decks': 'decks',
    '/decks/builder': 'builder',
    '/explorer': 'explorer',
    '/training': 'training',
    '/settings': 'settings',
    '/collection': 'collection',
    '/import-export': 'import-export',
    '/login': 'login',
    '/register': 'register'
  };

  // Views that don't require authentication
  const publicViews: ViewType[] = ['login', 'register'];

  // Views that show without sidebar (auth pages)
  const noSidebarViews: ViewType[] = ['login', 'register'];

  let authInitialized = $state(false);

  let currentView = $state<ViewType>('home');
  let showNewDeckModal = $state(false);

  function getViewFromPath(): ViewType {
    const path = window.location.pathname;
    return routes[path] || 'home';
  }

  function navigateTo(path: string): void {
    window.history.pushState({}, '', path);
    currentView = getViewFromPath();
  }

  function handlePopState(): void {
    currentView = getViewFromPath();
  }

  onMount(async () => {
    await authStore.init();
    authInitialized = true;
    await deckStore.loadDecks();
    currentView = getViewFromPath();

    // Redirect to login if accessing protected route without auth
    if (!$isAuthenticated && !publicViews.includes(currentView)) {
      navigateTo('/login');
    }

    window.addEventListener('popstate', handlePopState);
  });

  onDestroy(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('popstate', handlePopState);
    }
  });

  function handleNavigate(view: string): void {
    if (view === 'new-deck') {
      showNewDeckModal = true;
    } else if (view === 'home') {
      deckStore.clearCurrentDeck();
      navigateTo('/');
    } else if (view === 'decks') {
      deckStore.clearCurrentDeck();
      navigateTo('/decks');
    } else if (view === 'builder') {
      navigateTo('/decks/builder');
    } else if (view === 'explorer') {
      navigateTo('/explorer');
    } else if (view === 'training') {
      navigateTo('/training');
    } else if (view === 'settings') {
      navigateTo('/settings');
    } else if (view === 'collection') {
      navigateTo('/collection');
    } else if (view === 'import-export') {
      navigateTo('/import-export');
    } else if (view === 'login') {
      navigateTo('/login');
    } else if (view === 'register') {
      navigateTo('/register');
    } else if (view === 'logout') {
      authStore.logout();
      navigateTo('/login');
    }
  }

  function handleSelectDeck(deckId: string): void {
    deckStore.selectDeck(deckId);
    navigateTo('/decks/builder');
  }

  function handleNewDeckComplete(_deck: Deck): void {
    showNewDeckModal = false;
    navigateTo('/decks/builder');
  }

  function handleEditDeck(_deck: Deck): void {
    navigateTo('/decks/builder');
  }

  function handleBackToDecks(): void {
    deckStore.clearCurrentDeck();
    navigateTo('/decks');
  }

  // Resizable sidebar
  let sidebarWidth = $state(260);
  const MIN_SIDEBAR_WIDTH = 200;
  const MAX_SIDEBAR_WIDTH = 400;

  function handleSidebarResize(delta: number): void {
    sidebarWidth = Math.max(MIN_SIDEBAR_WIDTH, Math.min(MAX_SIDEBAR_WIDTH, sidebarWidth + delta));
  }
</script>

{#if !authInitialized}
  <div class="loading-screen">
    <div class="loading-spinner"></div>
  </div>
{:else if noSidebarViews.includes(currentView)}
  {#if currentView === 'login'}
    <Login onNavigate={handleNavigate} />
  {:else if currentView === 'register'}
    <Register onNavigate={handleNavigate} />
  {/if}
{:else}
  <div class="app-layout">
    <Sidebar
      onNavigate={handleNavigate}
      onSelectDeck={handleSelectDeck}
      currentView={currentView}
      width={sidebarWidth}
      onResize={handleSidebarResize}
    />

    <main class="main-content">
      {#if currentView === 'home'}
        <Home onNavigate={handleNavigate} />
      {:else if currentView === 'decks'}
        <DeckList onNavigate={handleNavigate} onEdit={handleEditDeck} />
      {:else if currentView === 'builder'}
        <DeckBuilder onBack={handleBackToDecks} />
      {:else if currentView === 'explorer'}
        <CardExplorer />
      {:else if currentView === 'training'}
        <Training />
      {:else if currentView === 'settings'}
        <div class="placeholder-view">
          <h2>Settings</h2>
          <p>Settings view coming soon...</p>
        </div>
      {:else if currentView === 'collection'}
        <div class="placeholder-view">
          <h2>My Collection</h2>
          <p>Collection management coming soon...</p>
        </div>
      {:else if currentView === 'import-export'}
        <div class="placeholder-view">
          <h2>Import / Export</h2>
          <p>Import and export functionality coming soon...</p>
        </div>
      {/if}
    </main>
  </div>
{/if}

{#if showNewDeckModal}
  <NewDeckModal
    onComplete={handleNewDeckComplete}
    onCancel={() => showNewDeckModal = false}
  />
{/if}

<style>
  .app-layout {
    display: flex;
    min-height: 100vh;
    background: var(--color-bg);
  }

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-x: hidden;
    background: var(--color-bg);
  }

  .placeholder-view {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
  }

  .placeholder-view h2 {
    font-size: 1.5rem;
    color: hsl(var(--foreground));
    margin-bottom: 0.5rem;
  }

  .placeholder-view p {
    color: hsl(var(--muted-foreground));
    font-size: 0.9375rem;
  }

  .loading-screen {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-bg);
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid hsl(var(--border));
    border-top-color: hsl(var(--foreground));
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
