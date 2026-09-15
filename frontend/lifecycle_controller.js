(() => {
  'use strict';

  const API_BASE = (document.body.dataset.apiBase || '').replace(/\/$/, '');
  const QUEUE_KEY = 'rie.frontend.research.queue.v1';
  const ACTIVE_KEY = 'rie.frontend.research.active.v1';
  const CHAT_KEY = 'rie.frontend.chats.v2';
  const CHAT_ID_KEY = 'rie.frontend.research.activeChat.v1';
  const MAX_POLL_MS = 10 * 60 * 1000;
  const BASE_DELAY_MS = 1500;
  const MAX_DELAY_MS = 10000;

  const prompt = document.getElementById('prompt');
  const composerStatus = document.getElementById('composer-status');
  const workspaceBody = document.getElementById('workspace-body');
  const conversation = document.getElementById('conversation-scroll');
  const queueList = document.getElementById('queue-list');
  const queueCount = document.getElementById('queue-count');
  const queueStatus = document.getElementById('queue-status');
  const queuePanel = document.getElementById('message-queue');

  const read = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback)); } catch { return fallback; }
  };
  const write = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const uuid = () => crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>\"']/g, (c) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
  const currentMode = () => document.querySelector('.mode.active')?.dataset.mode || 'chat';
  const token = () => sessionStorage.getItem('rie.frontend.sessionToken.v1') || '';
  const headers = (json = false, requestId = '') => {
    const result = { Accept: 'application/json' };
    if (json) result['Content-Type'] = 'application/json';
    if (requestId) result['Idempotency-Key'] = requestId;
    if (token()) result.Authorization = `Bearer ${token()}`;
    return result;
  };
  const activeChatId = () => localStorage.getItem(CHAT_ID_KEY) || read(CHAT_KEY, [])[0]?.id || null;

  const queue = () => read(QUEUE_KEY, []).filter((item) => item && item.id && item.text);
  const saveQueue = (items) => { write(QUEUE_KEY, items); renderQueue(); };
  const active = () => read(ACTIVE_KEY, null);
  const setActive = (value) => value ? write(ACTIVE_KEY, value) : localStorage.removeItem(ACTIVE_KEY);

  function addLocalMessage(chatId, role, text, meta = {}) {
    if (!chatId) return null;
    const chats = read(CHAT_KEY, []);
    const chat = chats.find((item) => item?.id === chatId);
    if (!chat) return null;
    if (!Array.isArray(chat.messages)) chat.messages = [];
    const message = { id: uuid(), role, text: String(text || ''), meta, at: Date.now() };
    chat.messages.push(message);
    if (role === 'user' && chat.title === 'New chat') chat.title = message.text.slice(0, 48) || 'New chat';
    write(CHAT_KEY, chats);
    return message;
  }

  function appendConversationFallback(role, text, meta = {}) {
    const article = document.createElement('article');
    article.className = `message ${role === 'user' ? 'user-message' : 'assistant-message'}`;
    article.dataset.lifecycleManaged = 'true';
    article.innerHTML = `<div class="message-meta"><span>${role === 'user' ? 'You' : 'Research AI'}</span><time>${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</time></div><div class="message-bubble">${escapeHtml(text)}</div>`;
    if (meta.sources?.length) {
      const sourceList = document.createElement('div');
      sourceList.className = 'source-list';
      sourceList.innerHTML = meta.sources.map((source, index) => `<div><span>${index + 1}</span><a href="${escapeHtml(source.url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title || source.url || 'source')}</a><small>${escapeHtml(source.access_state || source.state || source.retrieval_method || '')}</small></div>`).join('');
      article.append(sourceList);
    }
    conversation?.append(article);
    conversation?.scrollTo(0, conversation.scrollHeight);
  }

  function renderQueue() {
    const items = queue();
    if (queueCount) { queueCount.textContent = String(items.length); queueCount.hidden = items.length === 0; }
    if (queueStatus) queueStatus.textContent = items.length ? `${items.length} waiting` : 'Nothing waiting';
    if (!queueList) return;
    queueList.innerHTML = items.length
      ? items.map((item, index) => `<div class="queue-item"><b>${index + 1}</b><div><strong>Research</strong><p>${escapeHtml(item.text)}</p></div><button data-lifecycle-remove-queue="${item.id}" aria-label="Remove queued research">×</button></div>`).join('')
      : '<div class="queue-empty">Queue is empty.</div>';
  }

  function renderWorkspace(data, error = '') {
    if (!workspaceBody) return;
    const run = data?.run || {};
    const status = String(data?.status || run?.status || 'unknown').toLowerCase();
    const observations = Array.isArray(data?.observations) ? data.observations : [];
    const capabilities = data?.capabilities || {};
    const errorHtml = error ? `<div class="error-banner">${escapeHtml(error)}</div>` : '';
    const observationHtml = observations.map((observation, index) => `<div class="evidence-row"><span class="state-dot">●</span><div><strong>${escapeHtml(observation.url || `source ${index + 1}`)}</strong><small>${escapeHtml(observation.access_state || observation.integrity_state || observation.retrieval_method || 'observed')}</small></div></div>`).join('');
    workspaceBody.innerHTML = `${errorHtml}<section class="workspace-card accent-card"><div class="card-head"><span>Current run</span><b>${escapeHtml(status)}</b></div><h3>${escapeHtml(run.run_id || data?.run_id || 'unknown')}</h3><p>Backend state only. Browser reconnects resume observation; they do not invent completion.</p><div class="card-actions"><button class="secondary" data-lifecycle-refresh="true">Refresh</button><button class="secondary" data-lifecycle-stop="true">Stop polling</button></div></section><section class="workspace-card"><div class="card-head"><strong>Backend capabilities</strong></div><pre class="json-block">${escapeHtml(JSON.stringify(capabilities, null, 2))}</pre></section><section class="workspace-card"><div class="card-head"><strong>Evidence</strong><span>${observations.length}</span></div>${observationHtml || '<p class="muted">No observation records returned yet.</p>'}</section>`;
  }

  function terminal(status) {
    return new Set(['completed', 'complete', 'success', 'succeeded', 'failed', 'error', 'cancelled', 'canceled', 'blocked', 'partial']).has(String(status || '').toLowerCase());
  }

  async function fetchRun(runId) {
    const response = await fetch(`${API_BASE}/api/v1/research/${encodeURIComponent(runId)}`, { headers: headers(false) });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || !body.ok) throw new Error(body.error || `Run lookup failed (${response.status})`);
    return body;
  }

  async function track(runId, chatId) {
    const started = Date.now();
    let delay = BASE_DELAY_MS;
    while (Date.now() - started < MAX_POLL_MS) {
      const current = active();
      if (!current || current.run_id !== runId || current.stopped) return;
      try {
        const body = await fetchRun(runId);
        renderWorkspace(body);
        setActive({ ...current, status: body.status, last_checked_at: Date.now() });
        if (terminal(body.status)) {
          const observations = (body.observations || []).map((item) => ({ url: item.url, title: item.title, access_state: item.access_state, retrieval_method: item.retrieval_method }));
          const message = body.result?.answer || body.answer
            ? `Research run ${runId} completed.\n\n${body.result?.answer || body.answer}`
            : `Research run ${runId} finished with ${observations.length} observed source record(s); backend status: ${body.status}.`;
          addLocalMessage(chatId, 'assistant', message, { runId, final: true, sources: observations });
          appendConversationFallback('assistant', message, { runId, sources: observations });
          localStorage.removeItem(ACTIVE_KEY);
          composerStatus.textContent = `Research ${body.status}; backend state recorded.`;
          return;
        }
        delay = BASE_DELAY_MS;
      } catch (error) {
        renderWorkspace(read(ACTIVE_KEY, current), error.message || 'Transient run lookup failure');
        delay = Math.min(delay * 2, MAX_DELAY_MS);
      }
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
    const current = active();
    if (current?.run_id === runId) {
      setActive({ ...current, status: 'unknown', stopped: false, last_error: 'poll timeout; refresh/reconnect required' });
      renderWorkspace(current, 'Run state could not be confirmed within the browser polling window. The backend run was not marked failed.');
      composerStatus.textContent = 'Research state unknown; refresh/reconnect to resume observation.';
    }
  }

  async function submit(item) {
    if (!API_BASE) throw new Error('Research API base is not configured');
    const chatId = item.chat_id || activeChatId();
    addLocalMessage(chatId, 'user', item.text, { request_id: item.request_id });
    appendConversationFallback('user', item.text);
    composerStatus.textContent = 'Submitting research run…';
    const response = await fetch(`${API_BASE}/api/v1/research`, {
      method: 'POST',
      headers: headers(true, item.request_id),
      body: JSON.stringify({
        question: item.text,
        depth: 'standard',
        require_citations: true,
        max_sources: 8,
        max_evidence_items: 24,
        strict_zero_cost_only: true,
        source_urls: item.source_urls || [],
      }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || !body.ok) throw new Error(body.error || `Research request failed (${response.status})`);
    const runId = body.run_id;
    const current = { run_id: runId, request_id: item.request_id, chat_id: chatId, status: 'submitted', created_at: Date.now(), stopped: false };
    setActive(current);
    renderWorkspace(body);
    composerStatus.textContent = `Research run ${runId} is being tracked from backend state.`;
    void track(runId, chatId);
  }

  async function submitNext() {
    const items = queue();
    if (!items.length || active()) return;
    const next = items[0];
    saveQueue(items.slice(1));
    try {
      await submit(next);
    } catch (error) {
      const message = `Queued research failed to submit: ${error.message || error}`;
      addLocalMessage(next.chat_id, 'assistant', message, { request_id: next.request_id, error: true });
      appendConversationFallback('assistant', message);
      composerStatus.textContent = 'Queued research failed; the item was consumed once and can be re-queued explicitly.';
    }
  }

  function enqueue(text) {
    const item = { id: uuid(), request_id: uuid(), text, chat_id: activeChatId(), source_urls: [], created_at: Date.now() };
    saveQueue([...queue(), item]);
    queuePanel?.classList.add('open');
    queuePanel?.setAttribute('aria-hidden', 'false');
    composerStatus.textContent = 'Follow-up queued FIFO; current research is not interrupted.';
    void submitNext();
  }

  function recover() {
    const current = active();
    if (!current?.run_id) { void submitNext(); return; }
    composerStatus.textContent = `Reconnecting to research run ${current.run_id}…`;
    void track(current.run_id, current.chat_id);
  }

  document.addEventListener('click', (event) => {
    const remove = event.target.closest('[data-lifecycle-remove-queue]');
    if (remove) {
      event.preventDefault(); event.stopPropagation();
      saveQueue(queue().filter((item) => item.id !== remove.dataset.lifecycleRemoveQueue));
      return;
    }
    if (event.target.closest('[data-lifecycle-refresh]')) {
      event.preventDefault(); event.stopPropagation();
      const current = active(); if (current?.run_id) recover();
      return;
    }
    if (event.target.closest('[data-lifecycle-stop]')) {
      event.preventDefault(); event.stopPropagation();
      const current = active();
      if (current) {
        setActive({ ...current, stopped: true, status: 'paused' });
        composerStatus.textContent = 'Polling paused. Backend run state is unchanged.';
        renderWorkspace({ run: current, status: 'paused', observations: [], capabilities: {} });
      }
      return;
    }
    if (event.target.closest('[data-action="send"]') && currentMode() === 'research') {
      event.preventDefault(); event.stopPropagation();
      const text = prompt?.value.trim(); if (!text || active()) return;
      prompt.value = ''; prompt.style.height = 'auto';
      const item = { id: uuid(), request_id: uuid(), text, chat_id: activeChatId(), source_urls: [], created_at: Date.now() };
      void submit(item).catch((error) => { appendConversationFallback('assistant', `Research could not be submitted: ${error.message || error}`); composerStatus.textContent = 'Research submission failed; backend truth is unchanged.'; });
      return;
    }
    if (event.target.closest('[data-action="queue"]') && currentMode() === 'research') {
      event.preventDefault(); event.stopPropagation();
      const text = prompt?.value.trim(); if (!text) return;
      prompt.value = ''; prompt.style.height = 'auto'; enqueue(text);
    }
  }, true);

  document.addEventListener('keydown', (event) => {
    if (event.target !== prompt || currentMode() !== 'research') return;
    if (event.key !== 'Enter') return;
    event.preventDefault(); event.stopPropagation();
    const text = prompt.value.trim();
    if (!text) return;
    prompt.value = ''; prompt.style.height = 'auto';
    if (event.shiftKey) { prompt.value = `${text}\n`; return; }
    if (event.ctrlKey || event.metaKey || active()) { enqueue(text); return; }
    const item = { id: uuid(), request_id: uuid(), text, chat_id: activeChatId(), source_urls: [], created_at: Date.now() };
    void submit(item).catch((error) => { appendConversationFallback('assistant', `Research could not be submitted: ${error.message || error}`); composerStatus.textContent = 'Research submission failed; backend truth is unchanged.'; });
  }, true);

  document.addEventListener('click', (event) => {
    const chat = event.target.closest('[data-chat]');
    if (chat) localStorage.setItem(CHAT_ID_KEY, chat.dataset.chat);
    const action = event.target.closest('[data-action="new-chat"]');
    if (action) setTimeout(() => { const chats = read(CHAT_KEY, []); if (chats[0]?.id) localStorage.setItem(CHAT_ID_KEY, chats[0].id); }, 0);
  }, true);
  window.addEventListener('online', recover);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') recover(); });

  renderQueue();
  recover();
})();
