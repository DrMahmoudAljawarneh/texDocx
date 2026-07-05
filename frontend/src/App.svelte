<script>
  import { view } from './lib/stores.js';
  import Header from './components/Header.svelte';
  import History from './components/History.svelte';
  import Upload from './components/Upload.svelte';
  import Status from './components/Status.svelte';
  import Shortcuts from './components/Shortcuts.svelte';
  import Toast from './components/Toast.svelte';
</script>

<div class="layout">
  <aside class="sidebar">
    <History />
  </aside>

  <main class="main-content">
    <Header />
    <div class="content-area">
      {#if $view === 'upload'}
        <Upload />
      {:else}
        <Status />
      {/if}
    </div>
  </main>
</div>

<Shortcuts />
<Toast />

<style>
  .layout {
    display: flex;
    flex: 1;
    gap: 1.5rem;
    animation: fadeIn 0.4s ease;
  }
  .sidebar {
    width: 260px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    position: sticky;
    top: 2rem;
    align-self: flex-start;
    max-height: calc(100vh - 4rem);
  }
  .main-content {
    flex: 1;
    min-width: 0;
  }
  .content-area {
    animation: fadeIn 0.3s ease;
  }

  @media (max-width: 820px) {
    .layout { flex-direction: column; padding: 1rem; gap: 1rem; }
    .sidebar { width: 100%; position: static; max-height: none; }
  }
</style>
