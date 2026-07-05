<script>
  import { _ } from '../lib/i18n.js';
  import { theme, toggleTheme } from '../lib/theme.js';
  import { lang } from '../lib/i18n.js';
</script>

<header class="header">
  <div class="brand">
    <div class="brand-icon">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2h2"/>
        <path d="M18 14h-8"/>
        <path d="M15 18h-5"/>
        <path d="M10 6h8v4h-8V6Z"/>
      </svg>
    </div>
    <div class="brand-text">
      <h1>{$_('title')}</h1>
      <span class="brand-sub">{$_('subtitle')}</span>
    </div>
  </div>
  <div class="actions">
    <select bind:value={$lang} aria-label="Language" class="lang-select">
      <option value="en">EN</option>
      <option value="es">ES</option>
      <option value="fr">FR</option>
      <option value="de">DE</option>
      <option value="zh">中文</option>
    </select>
    <button class="theme-btn" onclick={toggleTheme} aria-label="Toggle theme" title={$theme === 'dark' ? 'Light mode' : 'Dark mode'}>
      {#if $theme === 'dark'}
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
      {:else}
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      {/if}
    </button>
  </div>
</header>

<style>
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid var(--border);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .brand-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: var(--accent-bg);
    color: var(--accent-light);
    flex-shrink: 0;
  }
  .brand-text h1 {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.3;
  }
  .brand-sub {
    display: block;
    font-size: 0.78rem;
    color: var(--text-tertiary);
    font-weight: 400;
    letter-spacing: normal;
  }
  .actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .lang-select {
    background: var(--bg-elevated);
    color: var(--text-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius-xs);
    padding: 0.35rem 0.5rem;
    font-size: 0.78rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition);
    font-family: var(--font);
    appearance: none;
    -webkit-appearance: none;
    padding-right: 1.5rem;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0.4rem center;
  }
  .lang-select:hover {
    border-color: var(--border-hover);
  }
  .lang-select:focus {
    outline: none;
    border-color: var(--accent);
  }
  .theme-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: var(--radius-xs);
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition);
  }
  .theme-btn:hover {
    border-color: var(--border-hover);
    color: var(--text);
    background: var(--bg-hover);
  }

  @media (max-width: 600px) {
    .header { flex-direction: column; align-items: flex-start; gap: 0.75rem; }
    .brand-sub { display: none; }
  }
</style>
