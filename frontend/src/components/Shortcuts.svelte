<script>
  import { _ } from '../lib/i18n.js';

  let visible = false;

  function toggle() { visible = !visible; }
  function close() { visible = false; }

  function handleKey(e) {
    if (e.key === 'Escape' && visible) { close(); return; }
    if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      const tag = e.target.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      e.preventDefault();
      toggle();
    }
  }

  import { onMount } from 'svelte';
  onMount(() => {
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  });
</script>

{#if visible}
  <div class="overlay" role="dialog" aria-modal="true" tabindex="-1" onclick={(e) => { if (e.target === e.currentTarget) close(); }} onkeydown={(e) => { if (e.key === 'Escape') close(); }}>
    <div class="modal">
      <div class="modal-header">
        <h2>Keyboard Shortcuts</h2>
        <button class="modal-close" onclick={close} aria-label="Close">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="modal-body">
        <div class="shortcut-row">
          <span class="shortcut-desc">Submit conversion</span>
          <kbd>Ctrl</kbd>+<kbd>Enter</kbd>
        </div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Go back / Close</span>
          <kbd>Esc</kbd>
        </div>
        <div class="shortcut-row">
          <span class="shortcut-desc">Show shortcuts</span>
          <kbd>?</kbd>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    z-index: 9998;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(4px);
  }
  .modal {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0;
    max-width: 420px;
    width: 90%;
    box-shadow: var(--shadow-lg);
    animation: fadeIn 0.2s ease;
    overflow: hidden;
  }
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border);
  }
  .modal-header h2 { font-size: 1rem; font-weight: 600; }
  .modal-close {
    display: flex;
    background: none;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    padding: 0.2rem;
    border-radius: 4px;
    transition: all var(--transition);
  }
  .modal-close:hover { color: var(--text); background: var(--bg-hover); }
  .modal-body { padding: 0.75rem 1.25rem 1.25rem; }
  .shortcut-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0;
  }
  .shortcut-row + .shortcut-row { border-top: 1px solid var(--border); }
  .shortcut-desc { font-size: 0.85rem; color: var(--text-secondary); }
  .shortcut-row :global(kbd) {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.15rem 0.4rem;
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--text);
  }
</style>
