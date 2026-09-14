(() => {
  const root = document.documentElement;
  const sidebar = document.getElementById('sidebar');
  const overlay = document.querySelector('.mobile-overlay');
  const workspace = document.getElementById('workspace');
  const queuePanel = document.getElementById('message-queue');
  const queueOverlay = document.querySelector('.queue-overlay');
  const queueList = document.getElementById('queue-list');
  const queueCount = document.getElementById('queue-count');
  const queuedInline = document.getElementById('queued-inline');
  const queueFooterStatus = document.getElementById('queue-footer-status');
  const composerStatus = document.getElementById('composer-status');
  const toast = document.getElementById('toast');
  const prompt = document.getElementById('prompt');
  const search = document.getElementById('chat-search');
  const settingsDialog = document.getElementById('settings-dialog');
  const conversation = document.getElementById('conversation-scroll');
  const queue = [];
  let processing = false;
  let toastTimer;

  const showToast = (message) => {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 1700);
  };
  const openSidebar = () => { sidebar.classList.add('open'); overlay.classList.add('show'); };
  const closeSidebar = () => { sidebar.classList.remove('open'); overlay.classList.remove('show'); };
  const openWorkspace = () => workspace.classList.add('open');
  const closeWorkspace = () => workspace.classList.remove('open');
  const openQueue = () => { queuePanel.classList.add('open'); queueOverlay.classList.add('show'); queuePanel.setAttribute('aria-hidden', 'false'); renderQueue(); };
  const closeQueue = () => { queuePanel.classList.remove('open'); queueOverlay.classList.remove('show'); queuePanel.setAttribute('aria-hidden', 'true'); };
  const scrollToBottom = () => conversation.scrollTo({ top: conversation.scrollHeight, behavior: 'smooth' });
  const activeMode = () => document.querySelector('.mode.active')?.dataset.mode || 'chat';
  const escapeHtml = (value) => value.replace(/[&<>'"]/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[char]));

  const appendUserMessage = (text, queued = false) => {
    const message = document.createElement('article');
    message.className = `message user-message${queued ? ' queued-message' : ''}`;
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble user-bubble';
    bubble.textContent = text;
    if (queued) bubble.insertAdjacentHTML('beforeend', '<span class="queued-label">Queued</span>');
    message.appendChild(bubble);
    conversation.appendChild(message);
    scrollToBottom();
  };

  const appendAssistantMessage = (text) => {
    const message = document.createElement('article');
    message.className = 'message assistant-message queue-generated-answer';
    message.innerHTML = `<div class="assistant-avatar">✦</div><div class="message-content"><div class="message-meta"><strong>My AI</strong><span>Now</span></div><div class="message-text"><p></p></div><div class="message-actions"><button data-action="copy">Copy</button><button data-action="save">Save</button></div></div>`;
    message.querySelector('.message-text p').textContent = text;
    conversation.appendChild(message);
    scrollToBottom();
  };

  const setBusy = (busy) => {
    processing = busy;
    document.body.classList.toggle('ai-busy', busy);
    composerStatus.textContent = busy
      ? (queue.length ? `My AI is responding · ${queue.length} follow-up${queue.length === 1 ? '' : 's'} waiting` : 'My AI is responding · you can keep sending messages')
      : (activeMode() === 'research' ? 'Research checks sources and shows citations.' : 'Chat is fast. You can queue follow-ups while a response is running.');
  };

  const renderQueue = () => {
    queueCount.textContent = String(queue.length);
    queueCount.hidden = queue.length === 0;
    queueFooterStatus.textContent = queue.length ? `${queue.length} waiting` : 'Nothing waiting';
    queuedInline.hidden = queue.length === 0;
    if (queue.length) queuedInline.innerHTML = `<button data-action="open-queue"><span class="queue-mini-dot"></span>${queue.length} follow-up${queue.length === 1 ? '' : 's'} queued <span>›</span></button>`;
    queueList.innerHTML = queue.map((item, index) => `<div class="queue-item"><div class="queue-number">${index + 1}</div><div class="queue-item-copy"><strong>${item.mode === 'research' ? 'Research' : 'Chat'}</strong><p>${escapeHtml(item.text)}</p></div><button class="queue-remove" data-remove-queue="${item.id}" aria-label="Remove queued message">×</button></div>`).join('');
  };

  const simulateResponse = (item) => new Promise((resolve) => {
    const delay = item.mode === 'research' ? 1700 : 950;
    window.setTimeout(() => {
      appendAssistantMessage(item.mode === 'research'
        ? `Research follow-up complete: I checked the requested angle and would now return verified findings with citations for “${item.text}”.`
        : `Follow-up received: “${item.text}”`);
      resolve();
    }, delay);
  });

  const processQueue = async () => {
    if (processing || queue.length === 0) return;
    setBusy(true);
    while (queue.length) {
      const item = queue.shift();
      renderQueue();
      await simulateResponse(item);
    }
    setBusy(false);
    renderQueue();
  };

  const enqueueMessage = (text) => {
    const item = { id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, text, mode: activeMode() };
    queue.push(item);
    appendUserMessage(text, processing);
    renderQueue();
    showToast(processing ? 'Added to message queue' : 'Starting response');
    void processQueue();
  };

  const sendMessage = () => {
    const value = prompt.value.trim();
    if (!value) return;
    prompt.value = '';
    prompt.style.height = 'auto';
    enqueueMessage(value);
  };

  const removeQueued = (id) => {
    const index = queue.findIndex((item) => item.id === id);
    if (index < 0) return;
    queue.splice(index, 1);
    renderQueue();
    showToast('Removed from queue');
  };

  const copyAnswer = () => {
    const text = document.querySelector('.queue-generated-answer:last-of-type .message-text')?.innerText || document.querySelector('.assistant-message .message-text')?.innerText || '';
    if (navigator.clipboard && text) navigator.clipboard.writeText(text).catch(() => {});
    showToast('Answer copied');
  };

  const setTheme = (theme) => {
    if (theme === 'system') root.removeAttribute('data-theme'); else root.dataset.theme = theme;
    document.querySelectorAll('[data-theme]').forEach((button) => button.classList.toggle('active', button.dataset.theme === theme));
    localStorage.setItem('my-ai-theme', theme);
  };
  const setAccent = (accent) => {
    root.dataset.accent = accent === 'blue' ? 'blue' : accent;
    document.querySelectorAll('[data-accent]').forEach((button) => button.classList.toggle('active', button.dataset.accent === accent));
    localStorage.setItem('my-ai-accent', accent);
  };
  const setDensity = (density) => {
    document.body.classList.toggle('compact', density === 'compact');
    document.querySelectorAll('[data-density]').forEach((button) => button.classList.toggle('active', button.dataset.density === density));
    localStorage.setItem('my-ai-density', density);
  };
  const filterChats = () => {
    const q = search.value.toLowerCase().trim();
    document.querySelectorAll('.chat-row').forEach((row) => { row.hidden = Boolean(q && !row.innerText.toLowerCase().includes(q)); });
  };

  const handleAction = (action) => {
    switch (action) {
      case 'new-chat': closeSidebar(); showToast('New chat'); prompt.focus(); break;
      case 'open-sidebar': openSidebar(); break;
      case 'close-sidebar': closeSidebar(); break;
      case 'close-workspace': closeWorkspace(); break;
      case 'open-sources': openWorkspace(); showToast('Sources opened'); break;
      case 'show-research': openWorkspace(); break;
      case 'copy': copyAnswer(); break;
      case 'save': showToast('Saved to Saved'); break;
      case 'regenerate': showToast('Regeneration requested'); break;
      case 'attachments': showToast('Attach a file or image'); break;
      case 'voice': showToast('Voice input is ready for integration'); break;
      case 'send': sendMessage(); break;
      case 'share': showToast('Share link ready for integration'); break;
      case 'search': search.focus(); openSidebar(); break;
      case 'more': showToast('More options'); break;
      case 'more-message': showToast('More message actions'); break;
      case 'profile': settingsDialog.showModal(); break;
      case 'close-settings': settingsDialog.close(); break;
      case 'open-queue': openQueue(); break;
      case 'close-queue': closeQueue(); break;
      case 'clear-queue': queue.splice(0, queue.length); renderQueue(); showToast('Queue cleared'); break;
      default: break;
    }
  };

  document.addEventListener('click', (event) => {
    const actionButton = event.target.closest('[data-action]');
    if (actionButton) handleAction(actionButton.dataset.action);
    const removeButton = event.target.closest('[data-remove-queue]');
    if (removeButton) removeQueued(removeButton.dataset.removeQueue);
    const mode = event.target.closest('[data-mode]');
    if (mode) {
      document.querySelectorAll('[data-mode]').forEach((button) => button.classList.toggle('active', button === mode));
      composerStatus.textContent = mode.dataset.mode === 'research' ? 'Research checks sources and shows citations.' : (processing ? `My AI is responding · ${queue.length} follow-ups waiting` : 'Chat is fast. You can queue follow-ups while a response is running.');
    }
    const view = event.target.closest('[data-view]');
    if (view) {
      document.querySelectorAll('[data-view]').forEach((button) => button.classList.toggle('active', button === view));
      if (view.dataset.view === 'settings') settingsDialog.showModal(); else showToast(`${view.innerText.trim()} view`);
      closeSidebar();
    }
    const chat = event.target.closest('[data-chat]');
    if (chat) { document.querySelectorAll('[data-chat]').forEach((row) => row.classList.toggle('active', row === chat)); closeSidebar(); showToast(`Opened ${chat.querySelector('strong')?.textContent || 'chat'}`); }
    const theme = event.target.closest('[data-theme]'); if (theme) setTheme(theme.dataset.theme);
    const accent = event.target.closest('[data-accent]'); if (accent) setAccent(accent.dataset.accent);
    const density = event.target.closest('[data-density]'); if (density) setDensity(density.dataset.density);
  });

  prompt.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); }
  });
  prompt.addEventListener('input', () => { prompt.style.height = 'auto'; prompt.style.height = `${Math.min(prompt.scrollHeight, 130)}px`; });
  search.addEventListener('input', filterChats);
  window.addEventListener('keydown', (event) => {
    const key = event.key.toLowerCase();
    if ((event.metaKey || event.ctrlKey) && key === 'k') { event.preventDefault(); prompt.focus(); }
    if (event.key === 'Escape') { closeSidebar(); closeWorkspace(); closeQueue(); if (settingsDialog.open) settingsDialog.close(); }
  });
  const storedTheme = localStorage.getItem('my-ai-theme');
  const storedAccent = localStorage.getItem('my-ai-accent');
  const storedDensity = localStorage.getItem('my-ai-density');
  if (storedTheme) setTheme(storedTheme);
  if (storedAccent) setAccent(storedAccent);
  if (storedDensity) setDensity(storedDensity);
  renderQueue();
})();
