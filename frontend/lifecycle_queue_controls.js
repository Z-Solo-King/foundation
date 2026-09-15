(() => {
  'use strict';

  const QUEUE_KEY = 'rie.frontend.research.queue.v1';
  const panel = document.getElementById('message-queue');
  const overlay = document.querySelector('.queue-overlay');
  const queueList = document.getElementById('queue-list');
  const queueCount = document.getElementById('queue-count');
  const queueStatus = document.getElementById('queue-status');

  const readQueue = () => {
    try {
      const value = JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
      return Array.isArray(value) ? value.filter((item) => item && item.id && item.text) : [];
    } catch {
      return [];
    }
  };
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>\"']/g, (c) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));

  function render() {
    const items = readQueue();
    if (queueCount) {
      queueCount.textContent = String(items.length);
      queueCount.hidden = items.length === 0;
    }
    if (queueStatus) queueStatus.textContent = items.length ? `${items.length} waiting` : 'Nothing waiting';
    if (queueList) {
      queueList.innerHTML = items.length
        ? items.map((item, index) => `<div class="queue-item"><b>${index + 1}</b><div><strong>Research</strong><p>${escapeHtml(item.text)}</p></div><button data-lifecycle-remove-queue="${item.id}" aria-label="Remove queued research">×</button></div>`).join('')
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
    const openButton = event.target.closest('[data-action="open-queue"]');
    if (openButton) {
      event.preventDefault();
      event.stopPropagation();
      open();
      return;
    }

    const clearButton = event.target.closest('[data-action="clear-queue"]');
    if (clearButton) {
      event.preventDefault();
      event.stopPropagation();
      localStorage.removeItem(QUEUE_KEY);
      render();
      return;
    }

    const removeButton = event.target.closest('[data-lifecycle-remove-queue]');
    if (removeButton) {
      event.preventDefault();
      event.stopPropagation();
      const items = readQueue().filter((item) => item.id !== removeButton.dataset.lifecycleRemoveQueue);
      localStorage.setItem(QUEUE_KEY, JSON.stringify(items));
      render();
      return;
    }

    if (event.target.closest('[data-action="close-queue"]')) close();
  }, true);

  window.addEventListener('storage', (event) => {
    if (event.key === QUEUE_KEY) render();
  });

  render();
})();
