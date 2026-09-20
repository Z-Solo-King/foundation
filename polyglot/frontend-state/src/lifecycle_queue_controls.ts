(() => {
  'use strict';

  interface QueueItem {
    id?: unknown;
    request_id?: unknown;
    text?: unknown;
  }

  interface FrontendApi {
    escapeHtml(value: unknown): string;
  }

  interface RIEWindow extends Window {
    RIEFrontend?: FrontendApi;
  }

  const api = (window as RIEWindow).RIEFrontend;
  if (!api) return;

  const QUEUE_KEY = 'rie.frontend.research.queue.v1';
  const panel = document.getElementById('message-queue');
  const overlay = document.querySelector<HTMLElement>('.queue-overlay');
  const queueList = document.getElementById('queue-list');
  const queueCount = document.getElementById('queue-count');
  const queueStatus = document.getElementById('queue-status');

  const readQueue = (): QueueItem[] => {
    try {
      const value: unknown = JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
      return Array.isArray(value)
        ? value.filter((item): item is QueueItem => Boolean(
            item && typeof item === 'object'
            && 'id' in item && 'request_id' in item && 'text' in item
            && (item as QueueItem).id && (item as QueueItem).request_id && (item as QueueItem).text,
          ))
        : [];
    } catch {
      return [];
    }
  };

  function render(): void {
    const items = readQueue();
    if (queueCount) {
      queueCount.textContent = String(items.length);
      queueCount.hidden = items.length === 0;
    }
    if (queueStatus) queueStatus.textContent = items.length ? `${items.length} waiting` : 'Nothing waiting';
    if (queueList) {
      queueList.innerHTML = items.length
        ? items.map((item, index) =>
            `<div class="queue-item"><b>${index + 1}</b><div><strong>Research</strong><p>${api.escapeHtml(item.text)}</p></div><button data-lifecycle-remove-queue="${api.escapeHtml(item.id)}" aria-label="Remove queued research">×</button></div>`
          ).join('')
        : '<div class="queue-empty">Queue is empty.</div>';
    }
  }

  function open(): void {
    panel?.classList.add('open');
    panel?.setAttribute('aria-hidden', 'false');
    overlay?.classList.add('show');
    render();
  }

  function close(): void {
    panel?.classList.remove('open');
    panel?.setAttribute('aria-hidden', 'true');
    overlay?.classList.remove('show');
  }

  document.addEventListener('click', (event: Event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (target?.closest('[data-action="open-queue"]')) {
      event.preventDefault();
      event.stopPropagation();
      open();
      return;
    }
    if (target?.closest('[data-action="clear-queue"]')) {
      event.preventDefault();
      event.stopPropagation();
      document.dispatchEvent(new Event('rie:queue-clear-requested'));
      return;
    }
    const remove = target?.closest<HTMLElement>('[data-lifecycle-remove-queue]');
    if (remove) {
      event.preventDefault();
      event.stopPropagation();
      document.dispatchEvent(new CustomEvent('rie:queue-remove-requested', {
        detail: { id: remove.dataset.lifecycleRemoveQueue },
      }));
      return;
    }
    if (target?.closest('[data-action="close-queue"]')) close();
  }, false);

  document.addEventListener('rie:queue-changed', render);
  window.addEventListener('storage', (event: StorageEvent) => {
    if (event.key === QUEUE_KEY) render();
  });
  render();
})();