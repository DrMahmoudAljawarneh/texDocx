const BASE = '';

export async function submitJob(file, format, macros, citationStyle = 'ieee', algorithmRender = 'text', templateFile = null) {
  const fd = new FormData();
  fd.append('file', file);
  if (templateFile) fd.append('template', templateFile);
  fd.append('format', format);
  fd.append('citation_style', citationStyle);
  fd.append('algorithm_render', algorithmRender);
  if (macros) fd.append('macros', macros);

  const res = await fetch(`${BASE}/jobs/submit`, { method: 'POST', body: fd });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

export async function getStatus(taskId) {
  const res = await fetch(`${BASE}/jobs/${taskId}/status`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getLogs(taskId) {
  const res = await fetch(`${BASE}/jobs/${taskId}/logs`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

export function createLogStream(taskId, onLog, onComplete) {
  const es = new EventSource(`${BASE}/jobs/${taskId}/logs/stream`);

  es.addEventListener('log', (e) => {
    try {
      const data = JSON.parse(e.data);
      onLog(data.severity || 'Info', data.message, data.line_number);
    } catch {
      onLog('Info', e.data);
    }
  });

  es.addEventListener('complete', () => {
    es.close();
    onComplete?.();
  });

  es.onerror = () => {};

  return () => es.close();
}

export function getDownloadUrl(taskId, type) {
  return `${BASE}/jobs/${taskId}/output/${type}`;
}
