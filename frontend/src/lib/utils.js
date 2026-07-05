export function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

const MAX_LINES = 80;

export function highlightLatex(text) {
  const lines = text.split('\n');
  const truncated = lines.length > MAX_LINES
    ? [...lines.slice(0, MAX_LINES), `… (${lines.length - MAX_LINES} more lines)`]
    : lines;
  return truncated.join('\n')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/(%.*)/g, '<span class="hl-comment">$1</span>')
    .replace(/(\$\$[\s\S]*?\$\$|\$[^$]*?\$)/g, '<span class="hl-math">$1</span>')
    .replace(/(\\(?:[a-zA-Z]+|.))/g, '<span class="hl-cmd">$1</span>')
    .replace(/(\{|\})/g, '<span class="hl-brace">$1</span>');
}

export function copyToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); } catch {}
  document.body.removeChild(ta);
}
