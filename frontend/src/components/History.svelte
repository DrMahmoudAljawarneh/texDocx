<script>
  import { _ } from '../lib/i18n.js';
  import { view, currentTaskId, status, progress, logs, startTime, history, clearHistory } from '../lib/stores.js';
  import { getLogs } from '../lib/api.js';

  $: items = $history;

  function loadJob(item) {
    if ($currentTaskId === item.taskId && $view === 'status') return;
    currentTaskId.set(item.taskId);
    status.set(item.status);
    progress.set(item.status === 'SUCCESS' ? 100 : 0);
    startTime.set(item.date);
    view.set('status');

    getLogs(item.taskId).then((text) => {
      logs.set([]);
      text.split('\n').filter(Boolean).forEach((line) => {
        try {
          const d = JSON.parse(line);
          logs.update((l) => [...l, { severity: d.severity || 'Info', message: d.message, line_number: d.line_number }]);
        } catch {
          logs.update((l) => [...l, { severity: 'Info', message: line }]);
        }
      });
    }).catch(() => {
      logs.set([{ severity: 'Info', message: 'Could not load logs for this job' }]);
    });
  }

  function formatDate(ts) {
    return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
</script>

<div class="sidebar-header">
  <div class="sidebar-title">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
    <h2>{$_('hist_title')}</h2>
  </div>
  {#if items.length}
    <button class="clear-btn" onclick={clearHistory} title="Clear history">
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
    </button>
  {/if}
</div>
<div class="history-list">
  {#if items.length === 0}
    <div class="empty-state">
      <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
      <span>{$_('hist_empty')}</span>
    </div>
  {:else}
    {#each items as item}
      <button class="hist-item"
        class:active={$view === 'status' && $currentTaskId === item.taskId}
        onclick={() => loadJob(item)}>
        <span class="hist-indicator" class:done={item.status === 'SUCCESS'} class:fail={item.status === 'FAILURE'} class:pending={item.status !== 'SUCCESS' && item.status !== 'FAILURE'}></span>
        <span class="hist-body">
          <span class="hist-name">{item.filename || 'pasted code'}</span>
          <span class="hist-meta">
            <span class="hist-status" class:success={item.status === 'SUCCESS'} class:fail={item.status === 'FAILURE'}>{item.status}</span>
            <span class="hist-date">{formatDate(item.date)}</span>
          </span>
        </span>
      </button>
    {/each}
  {/if}
</div>

<style>
  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .sidebar-title {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--text-tertiary);
  }
  .sidebar-title svg { flex-shrink: 0; }
  .sidebar-title h2 {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .clear-btn {
    display: flex;
    background: none;
    border: none;
    color: var(--text-dim);
    cursor: pointer;
    padding: 0.2rem;
    border-radius: 4px;
    transition: all var(--transition);
  }
  .clear-btn:hover { color: var(--danger); background: var(--danger-bg); }

  .history-list {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    max-height: calc(100vh - 200px);
    overflow-y: auto;
    flex: 1;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 2rem 0.5rem;
    color: var(--text-dim);
    font-size: 0.8rem;
  }
  .empty-state svg { opacity: 0.4; }

  .hist-item {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.55rem 0.65rem;
    background: var(--bg-card);
    border: 1px solid transparent;
    border-radius: var(--radius-xs);
    cursor: pointer;
    transition: all var(--transition);
    font: inherit;
    text-align: inherit;
    width: 100%;
    color: inherit;
    font-size: inherit;
  }
  .hist-item:hover { background: var(--bg-hover); }
  .hist-item.active { border-color: var(--accent); background: var(--accent-bg); }

  .hist-indicator {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
    background: var(--text-dim);
  }
  .hist-indicator.done { background: var(--success); box-shadow: 0 0 6px var(--success-glow); }
  .hist-indicator.fail { background: var(--danger); }
  .hist-indicator.pending { background: var(--accent); animation: pulse 1.5s ease infinite; }

  .hist-body { flex: 1; min-width: 0; }
  .hist-name {
    display: block;
    font-size: 0.78rem;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .hist-meta {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.68rem;
    color: var(--text-tertiary);
    margin-top: 0.1rem;
  }
  .hist-status { font-weight: 600; }
  .hist-status.success { color: var(--success); }
  .hist-status.fail { color: var(--danger); }
  .hist-date { color: var(--text-dim); }

  @media (max-width: 820px) {
    .history-list { max-height: 200px; }
  }
</style>
