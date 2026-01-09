<script lang="ts">
  import { onMount } from 'svelte';
  import { deckStore } from './stores/deckStore';
  import Header from './lib/components/Header.svelte';
  import DeckList from './lib/components/DeckList.svelte';
  import DeckBuilder from './lib/components/DeckBuilder.svelte';
  import NewDeckModal from './lib/components/NewDeckModal.svelte';
  import type { Deck } from './lib/types';

  let currentView: 'home' | 'builder' = 'home';
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
    } else if (view === 'builder') {
      currentView = 'builder';
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
    currentView = 'home';
  }
</script>

<Header onNavigate={handleNavigate} />

<main class="main-content">
  {#if currentView === 'home'}
    <DeckList onNavigate={handleNavigate} onEdit={handleEditDeck} />
  {:else if currentView === 'builder'}
    <DeckBuilder onBack={handleBackToDecks} />
  {/if}
</main>

{#if showNewDeckModal}
  <NewDeckModal
    onComplete={handleNewDeckComplete}
    onCancel={() => showNewDeckModal = false}
  />
{/if}

<style>
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
</style>
