<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { deckStore } from './stores/deckStore';
  import Sidebar from './lib/components/Sidebar.svelte';
  import Home from './lib/components/Home.svelte';
  import DeckList from './lib/components/DeckList.svelte';
  import DeckBuilder from './lib/components/DeckBuilder.svelte';
  import Explorer from './lib/components/Explorer.svelte';
  import Training from './lib/components/Training.svelte';
  import NewDeckModal from './lib/components/NewDeckModal.svelte';
  import type { Deck } from './lib/types';

  type ViewType = 'home' | 'decks' | 'builder' | 'explorer' | 'training';
  
  const routes: Record<string, ViewType> = {
    '/': 'home',
    '/home': 'home',
    '/decks': 'decks',
    '/decks/builder': 'builder',
    '/explorer': 'explorer',
    '/training': 'training'
  };

  let currentView: ViewType = 'home';
  let showNewDeckModal = false;

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

  onMount(() => {
    deckStore.loadDecks();
    currentView = getViewFromPath();
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
    }
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
</script>

<div class="app-layout">
  <Sidebar onNavigate={handleNavigate} />

  <main class="main-content">
    {#if currentView === 'home'}
      <Home onNavigate={handleNavigate} />
    {:else if currentView === 'decks'}
      <DeckList onNavigate={handleNavigate} onEdit={handleEditDeck} />
    {:else if currentView === 'builder'}
      <DeckBuilder onBack={handleBackToDecks} />
    {:else if currentView === 'explorer'}
      <Explorer />
    {:else if currentView === 'training'}
      <Training />
    {/if}
  </main>
</div>

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
  }

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-x: hidden;
  }
</style>
