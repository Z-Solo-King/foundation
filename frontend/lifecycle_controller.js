(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api?.workspaceView) throw new Error('frontend_state.js and workspace_view.js must load before lifecycle_controller.js');

  const API_BASE = api.API_BASE;
  const QUEUE_KEY = 'rie.frontend.research.queue.v1';
  const ACTIVE_KEY = 'rie.frontend.research.active.v1';
  const CHAT_ID_KEY = api.keys.activeChat;
  const MAX_POLL_MS = 10 * 60 * 1000;
  const BASE_DELAY_MS = 1500;
  const MAX_DELAY_MS = 10000;

  const composerStatus = document.getElementById('composer-status');

  const readQueue = () => {
    try {
      const value = JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
      return Array.isArray(value) ? value.filter((item) => item && item.id && item.request_id && item.text) : [];
    } catch {
      return [];
    }
  };
  const saveQueue = (items) => localStorage.setItem(QUEUE_KEY, JSON.stringify(items));
  const active = () => {
    try { return JSON.parse(localStorage.getItem(ACTIVE_KEY) || 'null'); } catch { return null; }
  };
  const setActive = (value) => value ? localStorage.setItem(ACTIVE_KEY, JSON.stringify(value)) : localStorage.removeItem(ACTIVE_KEY);
  const currentChatId = () => localStorage.getItem(CHAT_ID_KEY) || api.state.activeChatId;
  const headers = (json = false, requestId = '') => {
    const result = api.authHeaders(json);
    if (requestId) result['Idempotency-Key'] = requestId;
    return result;
  };

  const setStatus = (text) => { if (composerStatus) composerStatus.textContent = text; };
  const terminal = (status) => new Set(['completed', 'complete', 'success', 'succeeded', 'failed', 'error', 'cancelled', 'canceled', 'blocked', 'partial']).has(String(status || '').toLowerCase());

  async function fetchRun(runId) {
    const response = await fetch(`${API_BASE}/api/v1/research/${encodeURIComponent(runId)}`, { headers: headers(false) });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.ok === false) throw new Error(body.error || `Run lookup failed (${response.status})`);
    return body;
  }

  function addFinalMessage(body, runId, chatId) {
    const observations = (body.observations || body.sources || []).map((item) => ({ url: item.url, title: item.title, access_state: item.access_state || item.state, retrieval_method: item.retrieval_method, integrity_state: item.integrity_state }));
    const answer = body.result?.answer || body.result?.text || body.result?.summary || body.answer || '';
    const status = String(body.status || '').toLowerCase();
    const message = answer ? `Research run ${runId} ${terminal(status) ? 'finished' : 'updated'}.\n\n${answer}` : `Research run ${runId} finished with ${observations.length} observed source record(s); backend status: ${status || 'unknown'}.`;
    const chat = api.state.chats.find((item) => item.id === chatId);
    if (!chat || chat.messages?.some((item) => item.meta?.runId === runId && item.meta?.final)) return;
    api.addMessage('assistant', message, { runId, final: true, sources: observations }, chatId);
  }

  async function track(runId, chatId) {
    const started = Date.now();
    let delay = BASE_DELAY_MS;
    while (Date.now() - started < MAX_POLL_MS) {
      const current = active();
      if (!current || current.run_id !== runId || current.stopped) return;
      try {
        const body = await fetchRun(runId);
        api.workspaceView.render(body);
        setActive({ ...current, status: body.status, last_checked_at: Date.now(), last_error: null });
        if (terminal(body.status)) {
          addFinalMessage(body, runId, chatId);
          localStorage.removeItem(ACTIVE_KEY);
          setStatus(`Research ${body.status}; backend state recorded.`);
          document.dispatchEvent(new CustomEvent('rie:chat-updated', { detail: { chatId, runId, final: true } }));
          void submitNext();
          return;
        }
        setStatus(`Research ${runId} · ${body.status || 'running'} · observing backend state`);
        delay = BASE_DELAY_MS;
      } catch (error) {
        setActive({ ...(current || {}), status: 'unknown', last_error: error.message || String(error), last_checked_at: Date.now() });
        api.workspaceView.render(current || {}, error.message || 'Transient run lookup failure');
        setStatus(`Research state temporarily unavailable; retrying in ${Math.round(delay / 1000)}s.`);
        delay = Math.min(delay * 2, MAX_DELAY_MS);
      }
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
    const current = active();
    if (current?.run_id === runId) {
      setActive({ ...current, status: 'unknown', stopped: false, last_error: 'poll timeout; refresh/reconnect required' });
      api.workspaceView.render(current, 'Run state could not be confirmed within the browser polling window. The backend run was not marked failed.');
      setStatus('Research state unknown; refresh or reconnect to resume observation.');
    }
  }

  async function submit(item) {
    if (!API_BASE) throw new Error('Research API base is not configured');
    // A brand-new session has no chat yet (state.chats is empty, activeChatId is
    // null). The chat-mode path never hits this because api.addMessage() falls
    // back to api.ensureChat() internally. Research mode had no equivalent
    // fallback and threw here instead, so the very first research submission
    // in a fresh session always failed with "No active chat is available for
    // this research run" even though nothing was actually wrong.
    const chatId = item.chat_id || currentChatId() || api.ensureChat().id;
    api.setActiveChat(chatId);
    api.addMessage('user', item.text, { request_id: item.request_id }, chatId);
    setStatus('Submitting research run…');
    const response = await fetch(`${API_BASE}/api/v1/research`, { method: 'POST', headers: headers(true, item.request_id), body: JSON.stringify({ question: item.text, depth: 'standard', require_citations: true, max_sources: 8, max_evidence_items: 24, strict_zero_cost_only: true, source_urls: item.source_urls || [] }) });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || !body.ok) throw new Error(body.error || `Research request failed (${response.status})`);
    const runId = body.run_id;
    setActive({ run_id: runId, request_id: item.request_id, chat_id: chatId, status: 'submitted', created_at: Date.now(), stopped: false });
    api.openWorkspace?.();
    api.workspaceView.render(body);
    setStatus(`Research run ${runId} is being tracked from backend state.`);
    void track(runId, chatId);
  }

  async function submitNext() {
    const items = readQueue();
    if (!items.length || active()) return;
    const next = items[0];
    saveQueue(items.slice(1));
    document.dispatchEvent(new Event('rie:queue-changed'));
    try {
      await submit(next);
    } catch (error) {
      api.addMessage('assistant', `Queued research failed to submit: ${error.message || error}`, { request_id: next.request_id, error: true }, next.chat_id);
      setStatus('Queued research failed; the item was consumed once and can be re-queued explicitly.');
      document.dispatchEvent(new Event('rie:queue-changed'));
    }
  }

  function enqueue(text, chatId = currentChatId()) {
    const item = { id: api.uuid(), request_id: api.uuid(), text: String(text || '').trim(), chat_id: chatId, source_urls: [], created_at: Date.now() };
    if (!item.text) return;
    saveQueue([...readQueue(), item]);
    setStatus('Follow-up queued FIFO; current research is not interrupted.');
    document.dispatchEvent(new Event('rie:queue-changed'));
    void submitNext();
  }

  function recover() {
    const current = active();
    if (!current?.run_id) { void submitNext(); return; }
    api.openWorkspace?.();
    setStatus(`Reconnecting to research run ${current.run_id}…`);
    void track(current.run_id, current.chat_id);
  }

  document.addEventListener('rie:composer-send', (event) => {
    if (event.detail?.mode !== 'research') return;
    const text = String(event.detail?.text || '').trim();
    if (!text) return;
    if (active()) { enqueue(text, currentChatId()); return; }
    void submit({ id: api.uuid(), request_id: api.uuid(), text, chat_id: currentChatId(), source_urls: [], created_at: Date.now() }).catch((error) => {
      api.addMessage('assistant', `Research could not be submitted: ${error.message || error}`, { error: true }, currentChatId());
      api.chatView.render();
      setStatus('Research submission failed; backend truth is unchanged.');
    });
  });

  document.addEventListener('rie:composer-queue', (event) => {
    if (event.detail?.mode === 'research') enqueue(event.detail.text, currentChatId());
  });
  document.addEventListener('rie:queue-clear-requested', () => {
    saveQueue([]);
    document.dispatchEvent(new Event('rie:queue-changed'));
  });
  document.addEventListener('rie:queue-remove-requested', (event) => {
    const id = event.detail?.id;
    if (!id) return;
    saveQueue(readQueue().filter((item) => item.id !== id));
    document.dispatchEvent(new Event('rie:queue-changed'));
  });

  document.addEventListener('click', (event) => {
    const openRun = event.target.closest('[data-open-run]');
    if (openRun) {
      event.preventDefault();
      const runId = openRun.dataset.openRun;
      const item = api.state.chats.flatMap((chat) => chat.messages || []).find((message) => message.meta?.runId === runId);
      const chat = api.state.chats.find((candidate) => candidate.messages?.some((message) => message.meta?.runId === runId));
      if (chat) api.setActiveChat(chat.id);
      setActive({ run_id: runId, request_id: item?.meta?.request_id || api.uuid(), chat_id: chat?.id || currentChatId(), status: 'reconnecting', created_at: Date.now(), stopped: false });
      recover();
      return;
    }
    if (event.target.closest('[data-lifecycle-refresh]') || event.target.closest('[data-lifecycle-reconnect]')) { event.preventDefault(); recover(); return; }
    if (event.target.closest('[data-lifecycle-stop]')) {
      event.preventDefault();
      const current = active();
      if (current) {
        setActive({ ...current, stopped: true, status: 'paused' });
        api.workspaceView.render({ run: current, status: 'paused', observations: [], capabilities: {} });
        setStatus('Polling paused. Backend run state is unchanged.');
      }
    }
  }, false);

  window.addEventListener('online', recover);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') recover(); });
  window.addEventListener('storage', (event) => { if (event.key === QUEUE_KEY || event.key === ACTIVE_KEY) { document.dispatchEvent(new Event('rie:queue-changed')); if (event.key === ACTIVE_KEY) recover(); } });

  api.researchLifecycle = Object.freeze({ recover, enqueue, submitNext, active, queue: readQueue });
  recover();
})();
