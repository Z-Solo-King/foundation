(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api?.chatView || !api?.composer) return;
  const MAX_CHARS = 12_000;
  let stopRequested = false;

  const icons = {
    menu: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>',
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>',
    search: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/></svg>',
    chat: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 6h14v10H9l-4 3V6Z"/></svg>',
    folder: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h7l2 2h9v9H3z"/></svg>',
    star: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 4 2.5 5.1 5.5.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.5-.8z"/></svg>',
    settings: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-5v3m0 12v3m9-9h-3M6 12H3m15.4-6.4-2.1 2.1M7.7 16.3l-2.1 2.1m12.8 0-2.1-2.1M7.7 7.7 5.6 5.6"/></svg>',
    dashboard: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="6" height="6"/><rect x="14" y="4" width="6" height="6"/><rect x="4" y="14" width="6" height="6"/><rect x="14" y="14" width="6" height="6"/></svg>',
    workspace: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v14H4zM8 9h8M8 13h5"/></svg>',
    queue: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M5 12h14M5 17h9"/></svg>',
    send: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 14-7-4 14-3.2-5.8zM11.8 13.2 19 5"/></svg>',
    mic: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"/></svg>',
    copy: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="11" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h2"/></svg>',
    retry: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 11a8 8 0 0 1 14-5l2 2M20 7V3m0 4h-4M20 13a8 8 0 0 1-14 5l-2-2M4 17v4m0-4h4"/></svg>',
    stop: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>',
    check: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>',
  };

  const setIcon = (node, name) => {
    if (!node || !icons[name]) return;
    const svg = document.createElement('span');
    svg.className = 'ux-icon';
    svg.innerHTML = icons[name];
    node.prepend(svg);
    [...node.childNodes].filter((child) => child.nodeType === Node.TEXT_NODE).forEach((child) => { child.textContent = ''; });
  };

  function installIcons(root = document) {
    const iconMap = [
      ['.menu-button', 'menu'], ['.mobile-close', 'close'], ['[data-action="open-sidebar"]', 'menu'],
      ['[data-action="close-sidebar"]', 'close'], ['[data-action="open-system-dashboard"]', 'dashboard'],
      ['[data-action="toggle-workspace"]', 'workspace'], ['[data-action="open-queue"]', 'queue'],
      ['[data-action="voice"]', 'mic'], ['[data-action="send"]', 'send'], ['.new-chat-button', 'chat'],
      ['.search-box', 'search'], ['[data-action="close-workspace"]', 'close'], ['[data-action="close-queue"]', 'close'],
      ['[data-action="backend-check"]:not(.connection-pill)', 'check'],
    ];
    iconMap.forEach(([selector, name]) => root.querySelectorAll(selector).forEach((node) => {
      if (!node.querySelector('.ux-icon')) setIcon(node, name);
    }));
    root.querySelectorAll('.nav-item[data-view="chats"]').forEach((node) => { if (!node.querySelector('.ux-icon')) setIcon(node, 'chat'); });
    root.querySelectorAll('.nav-item[data-view="projects"]').forEach((node) => { if (!node.querySelector('.ux-icon')) setIcon(node, 'folder'); });
    root.querySelectorAll('.nav-item[data-view="saved"]').forEach((node) => { if (!node.querySelector('.ux-icon')) setIcon(node, 'star'); });
    root.querySelectorAll('.nav-item[data-view="settings"]').forEach((node) => { if (!node.querySelector('.ux-icon')) setIcon(node, 'settings'); });
    root.querySelectorAll('.brand-mark').forEach((node) => { if (!node.querySelector('.ux-icon')) { node.textContent = ''; node.innerHTML = icons.workspace; node.classList.add('ux-brand-icon'); } });
    root.querySelectorAll('.empty-mark').forEach((node) => { if (!node.querySelector('.ux-icon')) { node.textContent = ''; node.innerHTML = icons.workspace; node.classList.add('ux-brand-icon'); } });
    root.querySelectorAll('.chat-icon').forEach((node) => { if (!node.querySelector('.ux-icon')) { node.textContent = ''; node.innerHTML = icons.chat; } });
  }

  function updateLastAssistant(fn) {
    const chat = api.activeChat?.();
    if (!chat) return;
    const message = [...(chat.messages || [])].reverse().find((item) => item.role === 'assistant');
    if (!message) return;
    fn(message);
    api.chatView.render();
  }

  function submitGuidedMessage(text) {
    updateLastAssistant((message) => {
      if (typeof api.updateMessage === 'function') api.updateMessage(message.id, { text, meta: { ...(message.meta || {}), error: true, pending: false, streaming: false } });
      else message.text = text;
    });
  }

  async function enhancedSubmitChat(text, chatId) {
    stopRequested = false;
    activeController = new AbortController();
    try {
      return await api.__originalSubmitChat(text, chatId);
    } catch (error) {
      if (stopRequested) submitGuidedMessage('Response stopped by you. The backend request was cancelled.');
      else if (/unauthorized|401/i.test(String(error?.message || error))) {
        submitGuidedMessage('This backend requires a session token. Open Settings to enter one, or enable Guest test mode to try Heroic AI locally without credentials.');
      }
      throw error;
    } finally {
      activeController = null;
    }
  }

  function installSubmitWrapper() {
    if (api.__originalSubmitChat || typeof api.submitChat !== 'function') return;
    api.__originalSubmitChat = api.submitChat;
    api.submitChat = enhancedSubmitChat;
  }

  function addCounter() {
    const prompt = document.getElementById('prompt');
    const hint = document.querySelector('.composer-hint');
    if (!prompt || !hint || hint.querySelector('.ux-counter')) return;
    const counter = document.createElement('span');
    counter.className = 'ux-counter';
    counter.setAttribute('aria-live', 'polite');
    hint.append(counter);
    const sync = () => {
      const length = prompt.value.length;
      counter.textContent = `${length.toLocaleString()} / ${MAX_CHARS.toLocaleString()}`;
      counter.classList.toggle('warn', length >= MAX_CHARS * 0.9 && length <= MAX_CHARS);
      counter.classList.toggle('error', length > MAX_CHARS);
      const send = document.querySelector('[data-action="send"]');
      if (send) send.disabled = length > MAX_CHARS;
      if (length > MAX_CHARS) {
        const status = document.getElementById('composer-status');
        if (status) { status.textContent = `Message exceeds the ${MAX_CHARS.toLocaleString()} character limit.`; status.dataset.tone = 'error'; }
      }
    };
    prompt.addEventListener('input', sync);
    sync();
  }

  function ensureStopButton() {
    const composer = document.querySelector('.composer');
    if (!composer || composer.querySelector('.ux-stop')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'composer-icon ux-stop';
    button.title = 'Stop response';
    button.setAttribute('aria-label', 'Stop response');
    button.hidden = true;
    button.innerHTML = icons.stop;
    button.addEventListener('click', () => {
      if (!activeController) return;
      stopRequested = true;
      activeController.abort();
      button.hidden = true;
    });
    const send = composer.querySelector('[data-action="send"]');
    composer.insertBefore(button, send || null);
  }

  function syncStopButton() {
    const button = document.querySelector('.ux-stop');
    if (button) button.hidden = !Boolean(activeController) || !api.state.submitting;
  }

  function copyText(text, button) {
    const done = () => {
      if (!button) return;
      const original = button.textContent;
      button.textContent = 'Copied';
      button.disabled = true;
      setTimeout(() => { button.textContent = original; button.disabled = false; }, 1200);
    };
    if (navigator.clipboard?.writeText) navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
    else fallbackCopy(text, done);
  }

  function fallbackCopy(text, done) {
    const input = document.createElement('textarea');
    input.value = text;
    input.style.position = 'fixed'; input.style.opacity = '0';
    document.body.append(input); input.focus(); input.select();
    try { document.execCommand('copy'); done(); } finally { input.remove(); }
  }

  function addMessageControls(root = document) {
    root.querySelectorAll('.message.assistant-message').forEach((message) => {
      const actions = message.querySelector('.message-actions');
      if (!actions || actions.dataset.uxEnhanced === 'true') return;
      actions.dataset.uxEnhanced = 'true';
      const text = message.querySelector('.message-bubble')?.textContent || '';
      if (text) {
        const copy = document.createElement('button');
        copy.className = 'secondary ux-copy'; copy.type = 'button'; copy.textContent = 'Copy'; copy.title = 'Copy response';
        copy.addEventListener('click', () => copyText(text, copy));
        actions.append(copy);
      }
      if (message.classList.contains('message-error')) {
        const candidate = [...(api.activeChat?.()?.messages || [])].reverse().find((item) => item.role === 'user' && item.text);
        if (candidate?.text) {
          const retry = document.createElement('button');
          retry.className = 'secondary ux-retry'; retry.type = 'button'; retry.textContent = 'Retry'; retry.title = 'Retry this request';
          retry.addEventListener('click', () => {
            api.composer?.selectMode('chat');
            document.dispatchEvent(new CustomEvent('rie:composer-send', { detail: { text: candidate.text, mode: 'chat' } }));
          });
          actions.append(retry);
        }
      }
    });
  }

  function renderMarkdownMessages(root = document) {
    if (typeof api.renderMarkdown !== 'function') return;
    root.querySelectorAll('.message.assistant-message .message-bubble').forEach((bubble) => {
      if (bubble.dataset.markdownRendered === 'true') return;
      bubble.dataset.markdownRendered = 'true';
      bubble.innerHTML = api.renderMarkdown(bubble.textContent || '');
    });
  }

  function guideUnauthorized(root = document) {
    root.querySelectorAll('.message.message-error .message-bubble').forEach((bubble) => {
      if (!/unauthorized|HTTP\s*401/i.test(bubble.textContent || '') || bubble.dataset.guidedAuth === 'true') return;
      bubble.dataset.guidedAuth = 'true';
      bubble.textContent = 'This backend requires a session token. Open Settings to enter one, or enable Guest test mode to try Heroic AI locally without credentials.';
      const message = bubble.closest('.message');
      const actions = message?.querySelector('.message-actions');
      if (!actions || actions.querySelector('[data-auth-guidance]')) return;
      const settings = document.createElement('button');
      settings.className = 'secondary'; settings.type = 'button'; settings.textContent = 'Open Settings'; settings.dataset.authGuidance = 'settings';
      settings.addEventListener('click', () => { api.state.view = 'settings'; api.chatView.render(); });
      const guest = document.createElement('button');
      guest.className = 'secondary'; guest.type = 'button'; guest.textContent = 'Guest test mode'; guest.dataset.authGuidance = 'guest';
      guest.addEventListener('click', () => {
        if (!api.state.guestTestMode) document.querySelector('.guest-test-button')?.click();
      });
      actions.append(settings, guest);
    });
  }

  function observe() {
    installIcons(document);
    installSubmitWrapper();
    addCounter();
    ensureStopButton();
    addMessageControls(document);
    renderMarkdownMessages(document);
    guideUnauthorized(document);
    syncStopButton();
  }

  document.addEventListener('click', (event) => {
    if (event.target.closest('.ux-copy')) return;
    if (event.target.closest('[data-action="send"]') && (document.getElementById('prompt')?.value.length || 0) > MAX_CHARS) {
      event.preventDefault();
      api.chatView.toast(`Message exceeds the ${MAX_CHARS.toLocaleString()} character limit.`);
    }
  }, true);

  new MutationObserver(observe).observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener('DOMContentLoaded', observe);
  window.setInterval(observe, 250);
  observe();
})();
