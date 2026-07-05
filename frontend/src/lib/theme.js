import { writable } from 'svelte/store';

function getPreferred() {
  try {
    const saved = localStorage.getItem('texdocx-theme');
    if (saved) return saved;
  } catch {}
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

export const theme = writable(getPreferred());

theme.subscribe(($t) => {
  document.documentElement.setAttribute('data-theme', $t);
  try { localStorage.setItem('texdocx-theme', $t); } catch {}
});

export function toggleTheme() {
  theme.update(($t) => ($t === 'dark' ? 'light' : 'dark'));
}
