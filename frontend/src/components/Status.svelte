<script>
  import { _ } from '../lib/i18n.js';
  import { onDestroy } from 'svelte';
  import { view, currentTaskId, status, progress, logs, startTime, updateHistoryItem } from '../lib/stores.js';
  import { getDownloadUrl, getLogs, createLogStream } from '../lib/api.js';
  import { copyToClipboard } from '../lib/utils.js';
  import Console from './Console.svelte';

  let copied = false;
  let esCleanup = null;
  let pollTimer = null;
  let taskId;
  let elapsedDisplay = '';
  let elapsedTimer = null;

  $: {
    $startTime;
    $status;
    if ($startTime && ($status === 'PENDING' || $status === 'PROCESSING')) {
      clearInterval(elapsedTimer);
      const tick = () => {
        const s = Math.floor((Date.now() - $startTime) / 1000);
        const m = Math.floor(s / 60);
        elapsedDisplay = `${m}m ${s % 60}s`;
      };
      tick();
      elapsedTimer = setInterval(tick, 500);
    } else {
      clearInterval(elapsedTimer);
      elapsedTimer = null;
      elapsedDisplay = '';
    }
  }

  onDestroy(() => clearInterval(elapsedTimer));

  $: {
    $currentTaskId;
    if ($currentTaskId && $view === 'status') {
      taskId = $currentTaskId;
      setupStreaming(taskId);
      setupPolling(taskId);
    }
  }

  function setupStreaming(tid) {
    if (esCleanup) esCleanup();
    esCleanup = createLogStream(tid, (sev, msg) => {
      logs.update((l) => [...l, { severity: sev, message: msg }]);
    });
  }

  function setupPolling(tid) {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      try {
        const s = await (await fetch(`/jobs/${tid}/status`)).json();
        status.set(s.status);
        if (s.progress_percent !== undefined) progress.set(s.progress_percent);
        if (s.status === 'SUCCESS' || s.status === 'FAILURE') {
          clearInterval(pollTimer);
          pollTimer = null;
          updateHistoryItem(tid, s.status);
          if (esCleanup) { esCleanup(); esCleanup = null; }
        }
      } catch {}
    }, 2000);
  }

  function goBack() {
    if (esCleanup) { esCleanup(); esCleanup = null; }
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    logs.set([]);
    view.set('upload');
  }

  function copyId() {
    if (taskId) {
      copyToClipboard(taskId);
      copied = true;
      setTimeout(() => copied = false, 2000);
    }
  }

  function retry() {
    logs.set([]);
    progress.set(0);
    status.set('PENDING');
    startTime.set(Date.now());
    setupStreaming(taskId);
    setupPolling(taskId);
  }

  $: pct = $progress;
  $: circumference = 2 * Math.PI * 36;
  $: offset = circumference - (pct / 100) * circumference;
  $: isSuccess = $status === 'SUCCESS';
  $: isFailure = $status === 'FAILURE';
  $: isProcessing = $status === 'PROCESSING';
</script>

<div class="card">
  <div class="card-header">
    <button class="back-btn" onclick={goBack}>
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
      {$_('back')}
    </button>
    <div class="task-info">
      <span class="task-label">Job</span>
      <code class="task-id">{taskId?.slice(0, 12)}…</code>
      <button class="copy-btn" onclick={copyId}>
        {#if copied}
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        {:else}
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        {/if}
      </button>
    </div>
    <span class="badge" class:processing={isProcessing} class:success={isSuccess} class:failure={isFailure} class:pending={!isProcessing && !isSuccess && !isFailure}>
      <span class="badge-dot"></span>
      {$status}
    </span>
  </div>

  <div class="progress-section">
    <div class="ring-wrap">
      <svg class="ring" viewBox="0 0 80 80" width="80" height="80">
        <circle class="ring-bg" cx="40" cy="40" r="36" fill="none" stroke-width="6"/>
        <circle class="ring-fg" class:success={isSuccess} class:failure={isFailure} cx="40" cy="40" r="36" fill="none" stroke-width="6"
          stroke-dasharray={circumference}
          stroke-dashoffset={offset}
          stroke-linecap="round"
          transform="rotate(-90 40 40)"
        />
      </svg>
      <div class="ring-label">
        {#if isSuccess}
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="var(--success)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        {:else if isFailure}
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="var(--danger)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        {:else}
          <span class="ring-pct">{pct}%</span>
        {/if}
      </div>
    </div>
    <div class="progress-details">
      <div class="progress-bar-lg">
        <div class="progress-bar-fill" class:success={isSuccess} class:failure={isFailure} style="width: {pct}%"></div>
      </div>
      {#if elapsedDisplay && isProcessing}
        <span class="elapsed">Elapsed: {elapsedDisplay}</span>
      {/if}
      {#if $startTime}
        <span class="started">Started at {new Date($startTime).toLocaleTimeString()}</span>
      {/if}
    </div>
  </div>

  <Console />

  {#if isSuccess}
    <div class="downloads">
      <a href={getDownloadUrl(taskId, 'xml')} class="dl-btn" download>
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        {$_('download_xml')}
      </a>
      <a href={getDownloadUrl(taskId, 'docx')} class="dl-btn" download>
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        {$_('download_docx')}
      </a>
    </div>
  {:else if isFailure}
    <div class="retry-section">
      <button class="btn-outline" onclick={retry}>
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        {$_('retry')}
      </button>
    </div>
  {/if}
</div>

<style>
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    box-shadow: var(--shadow-md);
    animation: fadeIn 0.3s ease;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }
  .back-btn {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 0.35rem 0.65rem;
    border-radius: var(--radius-xs);
    font-size: 0.8rem;
    cursor: pointer;
    transition: all var(--transition);
  }
  .back-btn:hover { border-color: var(--border-hover); color: var(--text); }
  .task-info {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    flex: 1;
  }
  .task-label { font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }
  .task-id { font-family: var(--mono); font-size: 0.78rem; color: var(--accent-light); }
  .copy-btn {
    display: flex;
    background: none;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    padding: 0.2rem;
    border-radius: 4px;
    transition: all var(--transition);
  }
  .copy-btn:hover { color: var(--text); background: var(--bg-hover); }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.25rem 0.65rem;
    border-radius: 20px;
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }
  .badge-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }
  .badge.pending { background: var(--bg-elevated); color: var(--text-tertiary); }
  .badge.pending .badge-dot { background: var(--text-tertiary); }
  .badge.processing { background: var(--accent-bg); color: var(--accent-light); }
  .badge.processing .badge-dot { background: var(--accent-light); animation: pulse 1.5s ease infinite; }
  .badge.success { background: var(--success-bg); color: var(--success); }
  .badge.success .badge-dot { background: var(--success); }
  .badge.failure { background: var(--danger-bg); color: var(--danger); }
  .badge.failure .badge-dot { background: var(--danger); }

  .progress-section {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.25rem 0;
  }
  .ring-wrap { flex-shrink: 0; position: relative; }
  .ring { display: block; }
  .ring .ring-bg { stroke: var(--bg-elevated); }
  .ring .ring-fg { stroke: var(--accent); transition: stroke-dashoffset 0.5s ease; }
  .ring .ring-fg.success { stroke: var(--success); }
  .ring .ring-fg.failure { stroke: var(--danger); }
  .ring-label {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ring-pct { font-size: 1rem; font-weight: 700; color: var(--text); }
  .progress-details { flex: 1; min-width: 0; }
  .progress-bar-lg {
    height: 8px;
    background: var(--bg-elevated);
    border-radius: 4px;
    overflow: hidden;
  }
  .progress-bar-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 4px;
    transition: width 0.4s ease;
    box-shadow: 0 0 8px var(--accent-glow);
  }
  .progress-bar-fill.success { background: var(--success); box-shadow: 0 0 8px var(--success-glow); }
  .progress-bar-fill.failure { background: var(--danger); box-shadow: 0 0 8px var(--danger-glow); }
  .elapsed { display: block; margin-top: 0.5rem; font-size: 0.8rem; color: var(--text-tertiary); }
  .started { display: block; margin-top: 0.15rem; font-size: 0.75rem; color: var(--text-dim); }

  .downloads {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }
  .dl-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.55rem 1rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 500;
    text-decoration: none;
    transition: all var(--transition);
  }
  .dl-btn:hover { border-color: var(--accent); color: var(--accent-light); background: var(--accent-bg); }

  .retry-section { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border); }
  .btn-outline {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.55rem 1.25rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition);
  }
  .btn-outline:hover { border-color: var(--border-hover); color: var(--text); }
</style>
