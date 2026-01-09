<script>
  import { onMount } from 'svelte';
  import { deckStore } from './stores/deckStore.js';
  import Header from './lib/components/Header.svelte';
  import DeckList from './lib/components/DeckList.svelte';
  import DeckBuilder from './lib/components/DeckBuilder.svelte';
  import NewDeckModal from './lib/components/NewDeckModal.svelte';

  let currentView = 'home';
  let showNewDeckModal = false;

  onMount(() => {
    deckStore.loadDecks();
  });

  function handleNavigate(view) {
    if (view === 'new-deck') {
      showNewDeckModal = true;
    } else if (view === 'home') {
      deckStore.clearCurrentDeck();
      currentView = 'home';
    } else {
      currentView = view;
    }
  }

  function handleNewDeckComplete(deck) {
    showNewDeckModal = false;
    currentView = 'builder';
  }

  function handleEditDeck(deck) {
    currentView = 'builder';
  }

  function handleBackToDecks() {
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
