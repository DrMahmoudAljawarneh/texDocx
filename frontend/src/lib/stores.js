import { writable, derived } from 'svelte/store';

export const view = writable('upload');
export const currentTaskId = writable(null);
export const status = writable('PENDING');
export const progress = writable(0);
export const logs = writable([]);
export const startTime = writable(null);

export const elapsed = derived(startTime, ($t) => {
  if (!$t) return '';
  const s = Math.floor((Date.now() - $t) / 1000);
  const m = Math.floor(s / 60);
  return `${m}m ${s % 60}s`;
});

export const history = writable([]);

export function addHistoryItem(taskId, st, format, filename) {
  history.update((h) => {
    const item = { taskId, status: st, format, filename, date: Date.now() };
    const next = [item, ...h].slice(0, 50);
    try { localStorage.setItem('texdocx-history', JSON.stringify(next)); } catch {}
    return next;
  });
}

export function updateHistoryItem(taskId, st) {
  history.update((h) => {
    const next = h.map((i) => (i.taskId === taskId ? { ...i, status: st } : i));
    try { localStorage.setItem('texdocx-history', JSON.stringify(next)); } catch {}
    return next;
  });
}

export function clearHistory() {
  history.set([]);
  try { localStorage.removeItem('texdocx-history'); } catch {}
}

function loadHistory() {
  try {
    const raw = localStorage.getItem('texdocx-history');
    if (raw) history.set(JSON.parse(raw));
  } catch {}
}
loadHistory();
