(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api) return;
  const QUEUE_KEY = 'rie.frontend.research.queue.v1';
  const panel = document.getElementById('message-queue');
  const overlay = document.querySelector('.queue-overlay');
  const queueList = document.getElementById('queue-list');
  const queueCount = document.getElementById('queue-count');
  const queueStatus = document.getElementById('queue-status');

  const readQueue = () => {
    try {
      const value = JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
      return Array.isArray(value) ? value.filter((item) => item && item.id && item.request_id && item.text) : [];
    } catch {
      return [];
    }
  };

  function render() {
    const items = readQueue();
    if (queueCount) { queueCount.textContent = String(items.length); queueCount.hidden = items.length === 0; }
    if (queueStatus) queueStatus.textContent = items.length ? `${items.length} waiting` : 'Nothing waiting';
    if (queueList) {
      queueList.innerHTML = items.length
        ? items.map((item, index) => `<div class="queue-item"><b>${index + 1}</b><div><strong>Research</strong><p>${api.escapeHtml(item.text)}</p></div><button data-lifecycle-remove-queue="${api.escapeHtml(item.id)}" aria-label="Remove queued research">×</button></div>`).join('')
        : '<div class="queue-empty">Queue is empty.</div>';
    }
  }

  function open() {
    panel?.classList.add('open');
    panel?.setAttribute('aria-hidden', 'false');
    overlay?.classList.add('show');
    render();
  }
  function close() {
    panel?.classList.remove('open');
    panel?.setAttribute('aria-hidden', 'true');
    overlay?.classList.remove('show');
  }

  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-action="open-queue"]')) { event.preventDefault(); event.stopPropagation(); open(); return; }
    if (event.target.closest('[data-action="clear-queue"]')) {
      event.preventDefault(); event.stopPropagation();
      document.dispatchEvent(new Event('rie:queue-clear-requested'));
      return;
    }
    const remove = event.target.closest('[data-lifecycle-remove-queue]');
    if (remove) {
      event.preventDefault(); event.stopPropagation();
      document.dispatchEvent(new CustomEvent('rie:queue-remove-requested', { detail: { id: remove.dataset.lifecycleRemoveQueue } }));
      return;
    }
    if (event.target.closest('[data-action="close-queue"]')) close();
  }, false);

  document.addEventListener('rie:queue-changed', render);
  window.addEventListener('storage', (event) => { if (event.key === QUEUE_KEY) render(); });
  render();
})();