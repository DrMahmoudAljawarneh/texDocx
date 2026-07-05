<script>
  import { _ } from '../lib/i18n.js';
  import { view, currentTaskId, logs, progress, status, startTime, addHistoryItem } from '../lib/stores.js';
  import { submitJob } from '../lib/api.js';
  import { formatSize, highlightLatex, copyToClipboard } from '../lib/utils.js';

  let activeTab = 'file';
  let selectedFile = null;
  let dragOver = false;
  let codeArea = '';
  let format = 'all';
  let citationStyle = 'ieee';
  let algorithmRender = 'text';
  let macros = '';
  let showAdvanced = false;
  let submitting = false;
  let previewContent = '';
  let templateFile = null;

  function handleTemplateFile(file) {
    if (file && file.name.toLowerCase().endsWith('.docx')) {
      templateFile = { file, name: file.name };
    } else {
      templateFile = null;
    }
  }

  function handleFile(file) {
    const valid = /\.(tex|zip)$/i.test(file.name) && file.size <= 50 * 1048576;
    selectedFile = { file, valid, name: file.name, size: file.size };
    if (valid && /\.tex$/i.test(file.name)) {
      const reader = new FileReader();
      reader.onload = (e) => { previewContent = e.target.result; };
      reader.readAsText(file);
    } else {
      previewContent = '';
    }
  }

  function clearFile() {
    selectedFile = null;
    previewContent = '';
  }

  function getSubmitData() {
    if (activeTab === 'file') {
      if (!selectedFile || !selectedFile.valid) return null;
      return selectedFile.file;
    }
    if (!codeArea.trim()) return null;
    return new File([codeArea], 'document.tex', { type: 'text/plain' });
  }

  async function doSubmit() {
    const file = getSubmitData();
    if (!file) return;

    submitting = true;
    logs.set([]);
    progress.set(0);
    status.set('PENDING');
    startTime.set(Date.now());

    try {
      const data = await submitJob(file, format, macros, citationStyle, algorithmRender, templateFile?.file);
      const taskId = data.task_id;
      addHistoryItem(taskId, 'PENDING', format, file.name);
      currentTaskId.set(taskId);
      view.set('status');
    } catch (err) {
      logs.update((l) => [...l, { severity: 'Error', message: `Submission failed: ${err.message}` }]);
      submitting = false;
    }
  }
</script>

<div class="card">
  <div class="tabs">
    <button class="tab" class:active={activeTab === 'file'} onclick={() => { activeTab = 'file'; clearFile(); }}>
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      {$_('tab_file')}
    </button>
    <button class="tab" class:active={activeTab === 'code'} onclick={() => activeTab = 'code'}>
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
      {$_('tab_code')}
    </button>
  </div>

  {#if activeTab === 'file'}
    <div
      class="drop-zone"
      class:dragover={dragOver}
      role="button"
      tabindex="0"
      ondragover={(e) => { e.preventDefault(); dragOver = true; }}
      ondragleave={() => dragOver = false}
      ondrop={(e) => { e.preventDefault(); dragOver = false; if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); }}
      onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); document.getElementById('file-input').click(); } }}
    >
      <div class="drop-icon">
        <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>
      <div class="drop-text">{$_('drop_text')}</div>
      <div class="drop-hint">{$_('drop_hint')}</div>
      <input id="file-input" type="file" accept=".tex,.zip" onchange={(e) => { if (e.target.files.length) handleFile(e.target.files[0]); }}>
    </div>

    {#if selectedFile}
      <div class="file-card" class:invalid={!selectedFile.valid}>
        <div class="file-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
        </div>
        <div class="file-details">
          <span class="file-name">{selectedFile.name}</span>
          <span class="file-meta">
            {formatSize(selectedFile.size)}
            {#if !selectedFile.valid}
              <span class="file-error">— Invalid file</span>
            {/if}
          </span>
        </div>
        {#if selectedFile.valid}
          <span class="file-badge success">Ready</span>
        {:else}
          <span class="file-badge error">Error</span>
        {/if}
        <button class="file-remove" onclick={clearFile} aria-label="Remove file">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    {/if}

    {#if previewContent}
      <details class="preview-block">
        <summary class="preview-toggle">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
          {$_('preview')}
        </summary>
        <div class="preview-code">{@html highlightLatex(previewContent)}</div>
      </details>
    {/if}
  {:else}
    <div class="code-section">
      <textarea class="code-area" bind:value={codeArea} placeholder={$_('paste_placeholder')} spellcheck="false"></textarea>
    </div>
  {/if}

  <div class="options-row">
    <div class="option-group">
      <span class="option-label">{$_('lbl_format')}</span>
      <div class="format-toggles">
        <button class="format-btn" class:active={format === 'all'} onclick={() => format = 'all'}>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          {$_('fmt_all')}
        </button>
        <button class="format-btn" class:active={format === 'xml'} onclick={() => format = 'xml'}>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
          {$_('fmt_xml')}
        </button>
        <button class="format-btn" class:active={format === 'docx'} onclick={() => format = 'docx'}>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          {$_('fmt_docx')}
        </button>
      </div>
    </div>
    <div class="option-group">
      <span class="option-label">Citation style</span>
      <select class="style-select" bind:value={citationStyle}>
        <option value="ieee">IEEE (numeric)</option>
        <option value="apa">APA (author-year)</option>
        <option value="mla">MLA</option>
        <option value="chicago">Chicago (author-date)</option>
        <option value="harvard">Harvard (author-year)</option>
      </select>
    </div>
    <div class="option-group">
      <span class="option-label">Algorithm render</span>
      <select class="style-select" bind:value={algorithmRender}>
        <option value="text">Text (LaTeX source)</option>
        <option value="image">Image (rendered)</option>
      </select>
    </div>
  </div>

  <div class="advanced-section">
    <button class="advanced-toggle" onclick={() => showAdvanced = !showAdvanced}>
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class:rotated={showAdvanced}><polyline points="9 18 15 12 9 6"/></svg>
      {$_('advanced')}
    </button>
    {#if showAdvanced}
      <div class="advanced-panel">
        <div style="margin-bottom: 1rem;">
          <span class="option-label">Journal DOCX Template</span>
          <div style="display: flex; gap: 0.5rem; align-items: center; margin-top: 0.25rem;">
            <input type="file" id="template-input" accept=".docx" style="display: none;" onchange={(e) => { if (e.target.files.length) handleTemplateFile(e.target.files[0]); }} />
            <button class="format-btn" onclick={() => document.getElementById('template-input').click()}>
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              Upload Template
            </button>
            {#if templateFile}
              <span class="file-name" style="max-width: 200px;">{templateFile.name}</span>
              <button class="file-remove" onclick={() => { templateFile = null; document.getElementById('template-input').value = ''; }} aria-label="Remove template">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            {/if}
          </div>
          <span class="drop-hint" style="display: block; margin-top: 0.25rem;">Optional: Inherit styles & margins from a .docx file</span>
        </div>
        <span class="option-label">Custom macros (JSON)</span>
        <textarea class="macros-area" bind:value={macros} placeholder={$_('macros_placeholder')}></textarea>
      </div>
    {/if}
  </div>

  <div class="action-row">
    <button class="btn-primary" disabled={submitting} onclick={doSubmit}>
      {#if submitting}
        <span class="btn-spinner"></span>
        Submitting…
      {:else}
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 10 4 15 9 20"/><path d="M20 4v7a4 4 0 0 1-4 4H4"/></svg>
        {$_('submit')}
      {/if}
    </button>
    <span class="shortcut-hint">
      <kbd>Ctrl</kbd>+<kbd>Enter</kbd>
    </span>
  </div>
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

  .tabs {
    display: flex;
    gap: 0.25rem;
    margin-bottom: 1.25rem;
    background: var(--bg-elevated);
    border-radius: var(--radius-sm);
    padding: 0.2rem;
  }
  .tab {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 0.55rem 0.75rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-secondary);
    background: transparent;
    border: none;
    border-radius: var(--radius-xs);
    cursor: pointer;
    transition: all var(--transition);
  }
  .tab:hover { color: var(--text); }
  .tab.active {
    background: var(--bg-card);
    color: var(--text);
    box-shadow: var(--shadow-sm);
  }

  .drop-zone {
    position: relative;
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 2.5rem 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: all var(--transition-slow);
    background: var(--bg);
    overflow: hidden;
  }
  .drop-zone::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at center, var(--accent-glow), transparent 70%);
    opacity: 0;
    transition: opacity var(--transition-slow);
  }
  .drop-zone:hover { border-color: var(--accent); background: var(--bg-elevated); }
  .drop-zone:hover::before { opacity: 1; }
  .drop-zone.dragover { border-color: var(--accent); border-style: solid; background: var(--accent-bg); }
  .drop-zone.dragover::before { opacity: 1; }
  .drop-zone .drop-icon { color: var(--text-tertiary); margin-bottom: 0.5rem; transition: transform var(--transition), color var(--transition); }
  .drop-zone:hover .drop-icon { color: var(--accent-light); transform: translateY(-2px); }
  .drop-zone .drop-text { color: var(--text-secondary); font-size: 0.9rem; font-weight: 500; }
  .drop-zone .drop-hint { color: var(--text-tertiary); font-size: 0.75rem; margin-top: 0.25rem; }
  .drop-zone input[type="file"] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }

  .file-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    animation: slideUp 0.2s ease;
  }
  .file-card.invalid { border-color: var(--danger); }
  .file-icon { color: var(--accent-light); display: flex; }
  .file-details { flex: 1; min-width: 0; }
  .file-name { display: block; font-size: 0.85rem; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .file-meta { display: block; font-size: 0.75rem; color: var(--text-tertiary); }
  .file-error { color: var(--danger); }
  .file-badge {
    font-size: 0.68rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .file-badge.success { background: var(--success-bg); color: var(--success); }
  .file-badge.error { background: var(--danger-bg); color: var(--danger); }
  .file-remove {
    display: flex;
    background: none;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 4px;
    transition: all var(--transition);
  }
  .file-remove:hover { color: var(--danger); background: var(--danger-bg); }

  .preview-block {
    margin-top: 0.75rem;
  }
  .preview-toggle {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.8rem;
    color: var(--text-tertiary);
    cursor: pointer;
    padding: 0.35rem 0;
    user-select: none;
  }
  .preview-toggle:hover { color: var(--text-secondary); }
  .preview-code {
    margin-top: 0.5rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.75rem;
    max-height: 280px;
    overflow-y: auto;
    font-family: var(--mono);
    font-size: 0.78rem;
    line-height: 1.6;
    white-space: pre-wrap;
  }

  .code-section { margin-bottom: 1rem; }
  .code-area {
    width: 100%;
    min-height: 200px;
    padding: 0.85rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text);
    font-family: var(--mono);
    font-size: 0.82rem;
    line-height: 1.6;
    resize: vertical;
    transition: border-color var(--transition);
  }
  .code-area:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }

  .options-row {
    display: flex;
    gap: 1.5rem;
    margin-top: 1rem;
    flex-wrap: wrap;
  }
  .option-group { flex: 1; min-width: 180px; }
  .option-label {
    display: block;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 0.4rem;
  }
  .format-toggles {
    display: flex;
    gap: 0.35rem;
  }
  .format-btn {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.45rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-secondary);
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-xs);
    cursor: pointer;
    transition: all var(--transition);
  }
  .format-btn:hover { border-color: var(--border-hover); color: var(--text); }
  .format-btn.active { background: var(--accent-bg); border-color: var(--accent); color: var(--accent-light); }

  .style-select {
    width: 100%;
    padding: 0.45rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-secondary);
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-xs);
    cursor: pointer;
    transition: all var(--transition);
    appearance: auto;
    font-family: inherit;
  }
  .style-select:hover { border-color: var(--border-hover); color: var(--text); }
  .style-select:focus { outline: none; border-color: var(--accent); }

  .advanced-section { margin-top: 0.75rem; }
  .advanced-toggle {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    background: none;
    border: none;
    color: var(--text-tertiary);
    font-size: 0.8rem;
    cursor: pointer;
    padding: 0.25rem 0;
    transition: color var(--transition);
  }
  .advanced-toggle:hover { color: var(--text-secondary); }
  .advanced-toggle svg { transition: transform var(--transition); }
  .advanced-toggle svg.rotated { transform: rotate(90deg); }
  .advanced-panel {
    margin-top: 0.5rem;
    padding: 0.75rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    animation: slideUp 0.2s ease;
  }
  .macros-area {
    width: 100%;
    padding: 0.5rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-xs);
    color: var(--text);
    font-family: var(--mono);
    font-size: 0.8rem;
    min-height: 50px;
    resize: vertical;
    margin-top: 0.25rem;
  }
  .macros-area:focus { outline: none; border-color: var(--accent); }

  .action-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 1.25rem;
  }
  .btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.65rem 1.5rem;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--btn-primary-text);
    background: var(--btn-primary);
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all var(--transition);
    box-shadow: 0 1px 8px rgba(99, 102, 241, 0.3);
  }
  .btn-primary:hover { background: var(--btn-primary-hover); box-shadow: 0 2px 12px rgba(99, 102, 241, 0.4); transform: translateY(-1px); }
  .btn-primary:active { transform: translateY(0); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }

  .btn-spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  .shortcut-hint {
    color: var(--text-tertiary);
    font-size: 0.75rem;
  }
  .shortcut-hint :global(kbd) {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.1rem 0.35rem;
    font-family: var(--mono);
    font-size: 0.7rem;
  }
</style>
