<script>
  import { _ } from '../lib/i18n.js';
  import { logs } from '../lib/stores.js';
  import { copyToClipboard } from '../lib/utils.js';

  let consoleEl;
  let autoScroll = true;

  $: {
    $logs;
    if (autoScroll && consoleEl) {
      requestAnimationFrame(() => { consoleEl.scrollTop = consoleEl.scrollHeight; });
    }
  }

  function clear() { logs.set([]); }
  function copy() { copyToClipboard($logs.map(l => l.message).join('\n')); }
</script>

<div class="terminal">
  <div class="terminal-bar">
    <div class="terminal-dots">
      <span class="dot red"></span>
      <span class="dot yellow"></span>
      <span class="dot green"></span>
    </div>
    <span class="terminal-title">console.log</span>
    <div class="terminal-actions">
      <button class="term-btn" onclick={copy} title="Copy">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      </button>
      <button class="term-btn" onclick={clear} title="Clear">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
      </button>
    </div>
  </div>
  <div class="terminal-body" bind:this={consoleEl} role="log" aria-live="polite">
    {#if $logs.length === 0}
      <div class="terminal-empty">
        <span class="prompt">$</span> Waiting for output…
      </div>
    {:else}
      {#each $logs as entry}
        <div class="line" class:info={!entry.severity || entry.severity === 'Info'}
             class:warning={entry.severity === 'Warning'}
             class:error={entry.severity === 'Error' || entry.severity === 'Fatal'}
             class:complete={entry.severity === 'Complete'}>
          <span class="line-prefix">{entry.severity === 'Info' ? '▸' : entry.severity === 'Warning' ? '⚠' : entry.severity === 'Error' ? '✖' : entry.severity === 'Fatal' ? '!!' : entry.severity === 'Complete' ? '✓' : '▸'}</span>
          {#if entry.line_number}
            <span class="line-num">[{entry.line_number}]</span>
          {/if}
          {entry.message}
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .terminal {
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    overflow: hidden;
    background: #0a0a0f;
    margin-top: 0.5rem;
  }
  :global([data-theme="light"]) .terminal { background: #f4f4f6; }

  .terminal-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0.85rem;
    background: var(--bg-elevated);
    border-bottom: 1px solid var(--border);
  }
  .terminal-dots { display: flex; gap: 5px; }
  .dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot.red { background: #ff5f57; }
  .dot.yellow { background: #ffbd2e; }
  .dot.green { background: #28c840; }
  .terminal-title { font-size: 0.72rem; color: var(--text-tertiary); flex: 1; }
  .terminal-actions { display: flex; gap: 0.15rem; }
  .term-btn {
    display: flex;
    background: none;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    padding: 0.15rem;
    border-radius: 4px;
    transition: color var(--transition);
  }
  .term-btn:hover { color: var(--text-secondary); }

  .terminal-body {
    height: 260px;
    overflow-y: auto;
    padding: 0.75rem;
    font-family: var(--mono);
    font-size: 0.76rem;
    line-height: 1.6;
  }
  .terminal-empty { color: var(--text-dim); }
  .prompt { color: var(--accent); margin-right: 0.5rem; }

  .line {
    padding: 0.08rem 0;
    display: flex;
    align-items: flex-start;
    gap: 0.4rem;
    word-break: break-word;
  }
  .line-prefix { flex-shrink: 0; width: 1.2rem; text-align: center; }
  .line-num { color: var(--text-dim); }
  .line.info .line-prefix { color: var(--text-tertiary); }
  .line.info { color: var(--text-secondary); }
  .line.warning .line-prefix { color: var(--warning); }
  .line.warning { color: var(--warning); }
  .line.error .line-prefix { color: var(--danger); }
  .line.error { color: var(--danger); }
  .line.complete .line-prefix { color: var(--success); }
  .line.complete { color: var(--success); }
</style>
