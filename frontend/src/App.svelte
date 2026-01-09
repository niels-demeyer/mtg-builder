<script lang="ts">
  import { onMount } from 'svelte';
  import { deckStore } from './stores/deckStore';
  import Sidebar from './lib/components/Sidebar.svelte';
  import Home from './lib/components/Home.svelte';
  import DeckList from './lib/components/DeckList.svelte';
  import DeckBuilder from './lib/components/DeckBuilder.svelte';
  import Explorer from './lib/components/Explorer.svelte';
  import Training from './lib/components/Training.svelte';
  import NewDeckModal from './lib/components/NewDeckModal.svelte';
  import type { Deck } from './lib/types';

  let currentView: 'home' | 'decks' | 'builder' | 'explorer' | 'training' = 'home';
  let showNewDeckModal = false;

  onMount(() => {
    deckStore.loadDecks();
  });

  function handleNavigate(view: string): void {
    if (view === 'new-deck') {
      showNewDeckModal = true;
    } else if (view === 'home') {
      deckStore.clearCurrentDeck();
      currentView = 'home';
    } else if (view === 'decks') {
      deckStore.clearCurrentDeck();
      currentView = 'decks';
    } else if (view === 'builder') {
      currentView = 'builder';
    } else if (view === 'explorer') {
      currentView = 'explorer';
    } else if (view === 'training') {
      currentView = 'training';
    }
  }

  function handleNewDeckComplete(_deck: Deck): void {
    showNewDeckModal = false;
    currentView = 'builder';
  }

  function handleEditDeck(_deck: Deck): void {
    currentView = 'builder';
  }

  function handleBackToDecks(): void {
    deckStore.clearCurrentDeck();
    currentView = 'decks';
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
