<script>
  let toasts = [];
  let idCounter = 0;

  export function show(message, type = 'info') {
    const id = ++idCounter;
    toasts = [...toasts, { id, message, type }];
    setTimeout(() => dismiss(id), 4000);
  }

  function dismiss(id) {
    toasts = toasts.filter((t) => t.id !== id);
  }

  import { setContext } from 'svelte';
  setContext('toast', { show });
</script>

{#if toasts.length}
  <div class="toast-container">
    {#each toasts as toast (toast.id)}
      <div class="toast toast-{toast.type}" role="alert" tabindex="0" onclick={() => dismiss(toast.id)} onkeydown={(e) => { if (e.key === 'Enter') dismiss(toast.id); }}>
        <div class="toast-icon">
          {#if toast.type === 'success'}
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          {:else if toast.type === 'error'}
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
          {:else}
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          {/if}
        </div>
        <span class="toast-message">{toast.message}</span>
        <button class="toast-close" onclick={(e) => { e.stopPropagation(); dismiss(toast.id); }} aria-label="Dismiss">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    {/each}
  </div>
{/if}

<style>
  .toast-container {
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: 380px;
  }
  .toast {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.75rem 1rem;
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow-lg);
    font-size: 0.85rem;
    line-height: 1.4;
    cursor: pointer;
    animation: slideUp 0.25s ease;
    backdrop-filter: blur(12px);
  }
  .toast-info { background: var(--bg-card); border: 1px solid var(--border); color: var(--text); }
  .toast-success { background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); color: var(--success); }
  .toast-error { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: var(--danger); }
  .toast-icon { flex-shrink: 0; display: flex; }
  .toast-message { flex: 1; }
  .toast-close {
    display: flex;
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    opacity: 0.5;
    padding: 0;
    transition: opacity var(--transition);
    flex-shrink: 0;
  }
  .toast-close:hover { opacity: 1; }

  @media (max-width: 480px) {
    .toast-container { left: 1rem; right: 1rem; bottom: 1rem; max-width: none; }
  }
</style>
