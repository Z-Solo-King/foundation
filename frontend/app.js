(() => {
  'use strict';

  const state = {
    chats: [], activeChatId: null, queue: [], processing: false, research: null,
    backendOk: false, attachments: [], projects: [], activeProjectId: null,
    saved: [], view: 'chats', sessionToken: '', pollingRunId: null,
  };

  const $ = (id) => document.getElementById(id);
  const sidebar = $('sidebar');
  const sidebarOverlay = document.querySelector('.mobile-overlay');
  const workspace = $('workspace');
  const workspaceBody = $('workspace-body');
  const conversation = $('conversation-scroll');
  const prompt = $('prompt');
  const search = $('chat-search');
  const emptyState = $('empty-state');
  const composerStatus = $('composer-status');
  const queuePanel = $('message-queue');
  const queueList = $('queue-list');
  const queueCount = $('queue-count');
  const queueStatus = $('queue-status');
  const toast = $('toast');
  const connectionPill = $('connection-pill');
  const mobileTitle = $('mobile-title');
  const API_BASE = (document.body.dataset.apiBase || '').replace(/\/$/, '');
  const CHAT_KEY = 'rie.frontend.chats.v2';
  const PROJECT_KEY = 'rie.frontend.projects.v1';
  const SAVED_KEY = 'rie.frontend.saved.v1';

  const uuid = () => crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const escapeHtml = (v) => String(v).replace(/[&<>'\"]/g, (c) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c]));
  const read = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback)); } catch { return fallback; } };
  const apiUrl = (path) => `${API_BASE}${path}`;
  const currentMode = () => document.querySelector('.mode.active')?.dataset.mode || 'chat';
  const showToast = (message) => { toast.textContent = message; toast.classList.add('show'); clearTimeout(showToast.timer); showToast.timer = setTimeout(() => toast.classList.remove('show'), 2200); };
  const save = () => { localStorage.setItem(CHAT_KEY, JSON.stringify(state.chats)); localStorage.setItem(PROJECT_KEY, JSON.stringify(state.projects)); localStorage.setItem(SAVED_KEY, JSON.stringify(state.saved)); };
  const authHeaders = (json = false) => { const h = { Accept: 'application/json' }; if (json) h['Content-Type'] = 'application/json'; if (state.sessionToken) h.Authorization = `Bearer ${state.sessionToken}`; return h; };

  function load() {
    state.chats = read(CHAT_KEY, []).filter(Boolean);
    state.projects = read(PROJECT_KEY, []).filter(Boolean);
    state.saved = read(SAVED_KEY, []).filter(Boolean);
    state.chats.forEach((c) => { if (!Array.isArray(c.messages)) c.messages = []; });
    repairSavedOwnership();
    if (state.chats.length) state.activeChatId = state.chats[0].id;
  }

  function activeChat() { return state.chats.find((c) => c.id === state.activeChatId); }
  function ensureChat() {
    let chat = activeChat();
    if (!chat) {
      chat = { id: uuid(), title: 'New chat', messages: [], createdAt: Date.now(), projectId: state.activeProjectId || null };
      state.chats.unshift(chat);
      state.activeChatId = chat.id;
      save();
    }
    return chat;
  }
  function addMessage(role, text, meta = {}, chatId = state.activeChatId) {
    const chat = state.chats.find((c) => c.id === chatId) || ensureChat();
    const message = { id: uuid(), role, text: String(text || ''), meta, at: Date.now() };
    chat.messages.push(message);
    if (role === 'user' && chat.title === 'New chat') chat.title = message.text.slice(0, 48) || 'New chat';
    save();
    return message;
  }
  function newChat() {
    const chat = { id: uuid(), title: 'New chat', messages: [], createdAt: Date.now(), projectId: state.activeProjectId || null };
    state.chats.unshift(chat); state.activeChatId = chat.id; state.research = null; state.view = 'chats'; state.pollingRunId = null;
    save(); render(); prompt.focus();
  }

  function setView(view) {
    state.view = view;
    document.querySelectorAll('[data-view]').forEach((el) => {
      const active = el.dataset.view === view;
      el.classList.toggle('active', active);
      el.setAttribute('aria-current', active ? 'page' : 'false');
    });
  }

  function renderChats() {
    const q = search.value.trim().toLowerCase();
    $('chat-list').innerHTML = state.chats.filter((c) => !q || c.title.toLowerCase().includes(q)).slice(0, 50).map((c) => `
      <button class="chat-row ${c.id === state.activeChatId ? 'active' : ''}" data-chat="${c.id}" aria-label="Open chat ${escapeHtml(c.title)}">
        <span class="chat-icon">✦</span><span><strong>${escapeHtml(c.title)}</strong><small>${new Date(c.createdAt).toLocaleDateString()}</small></span>
      </button>`).join('');
  }

  function renderSources(sources = []) {
    return sources.map((s, i) => `<div><span>${i + 1}</span><a href="${escapeHtml(s.url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(s.title || s.url || 'source')}</a><small>${escapeHtml(s.access_state || s.state || s.retrieval_method || '')}</small></div>`).join('');
  }

  function renderConversation() {
    if (state.view !== 'chats') return renderView();
    const chat = activeChat();
    mobileTitle.textContent = chat?.title || 'New chat';
    if (!chat || chat.messages.length === 0) {
      conversation.innerHTML = ''; conversation.append(emptyState); emptyState.hidden = false; return;
    }
    emptyState.hidden = true;
    conversation.innerHTML = chat.messages.map((m) => `
      <article class="message ${m.role === 'user' ? 'user-message' : 'assistant-message'}" data-message-id="${m.id}">
        <div class="message-meta"><span>${m.role === 'user' ? 'You' : 'Research AI'}</span><time>${new Date(m.at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</time></div>
        <div class="message-bubble">${escapeHtml(m.text)}</div>
        <div class="message-actions">
          <button class="secondary" data-save-message="${m.id}" aria-label="${m.meta?.saved ? 'Remove from saved' : 'Save message'}">${m.meta?.saved ? 'Saved' : 'Save'}</button>
          ${m.meta?.runId ? `<button class="secondary" data-open-run="${escapeHtml(m.meta.runId)}">Open run</button>` : ''}
        </div>
        ${m.meta?.sources?.length ? `<div class="source-list">${renderSources(m.meta.sources)}</div>` : ''}
      </article>`).join('');
    conversation.scrollTop = conversation.scrollHeight;
  }

  function renderView() {
    mobileTitle.textContent = state.view[0].toUpperCase() + state.view.slice(1);
    emptyState.hidden = true;
    if (state.view === 'projects') {
      conversation.innerHTML = `<div class="message view-panel"><div class="view-heading"><div><span class="eyebrow">Workspace</span><h2>Projects</h2><p>Local organization only. Server-backed projects are not implied.</p></div><button class="primary" data-action="new-project">＋ New project</button></div>
        ${state.projects.length ? state.projects.map((p) => { const count = state.chats.filter((c) => c.projectId === p.id).length; return `<section class="workspace-card project-card"><div class="card-head"><strong>${escapeHtml(p.name)}</strong><span>${count} chat${count === 1 ? '' : 's'}</span></div><div class="card-actions"><button class="secondary" data-project="${p.id}">Open</button><button class="secondary" data-project-assign="${p.id}">Use for current chat</button></div></section>`; }).join('') : '<div class="workspace-card empty-card"><strong>No projects yet</strong><p>Create one to group browser-local chats.</p></div>'}</div>`;
      return;
    }
    if (state.view === 'saved') {
      conversation.innerHTML = `<div class="message view-panel"><div class="view-heading"><div><span class="eyebrow">Local library</span><h2>Saved</h2><p>Saved messages stay in this browser.</p></div></div>
        ${state.saved.length ? state.saved.map((s) => `<section class="workspace-card saved-card"><strong>${escapeHtml(s.text)}</strong><small>${new Date(s.at).toLocaleString()}</small><div class="card-actions"><button class="secondary" data-saved-message="${s.messageId}">Open chat</button><button class="secondary" data-remove-saved="${s.messageId}">Remove</button></div></section>`).join('') : '<div class="workspace-card empty-card"><strong>Nothing saved yet</strong><p>Use Save on any message.</p></div>'}</div>`;
      return;
    }
    if (state.view === 'settings') {
      conversation.innerHTML = `<div class="message view-panel"><div class="view-heading"><div><span class="eyebrow">Configuration</span><h2>Settings</h2><p>Browser-local controls for the current frontend surface.</p></div></div>
        <section class="workspace-card"><div class="card-head"><strong>Backend</strong><span class="status-dot ${state.backendOk ? 'ok' : ''}">${state.backendOk ? 'reachable' : 'unknown'}</span></div><p>${escapeHtml(API_BASE || 'Not configured')}</p><p class="muted">The optional bearer token is memory-only for this tab and is never persisted.</p><label class="field-label" for="session-token">Session token</label><input id="session-token" type="password" placeholder="Optional short-lived session token" autocomplete="off" value="${escapeHtml(state.sessionToken)}"><div class="card-actions"><button class="secondary" data-action="save-session-token">Use for this tab</button><button class="secondary" data-action="clear-session-token">Clear</button><button class="secondary" data-action="backend-check">Check backend</button></div></section>
        <section class="workspace-card"><div class="card-head"><strong>Local data</strong><span>${state.chats.length} chats · ${state.saved.length} saved</span></div><p class="muted">Exports include chats, projects and saved records. Imports are validated as local data only.</p><div class="card-actions"><button class="secondary" data-action="export-data">Export</button><button class="secondary" data-action="import-data">Import</button><button class="danger" data-action="clear-data">Clear local data</button></div></section></div>`;
    }
  }

  function renderQueue() {
    queueCount.textContent = state.queue.length;
    queueCount.hidden = !state.queue.length;
    queueStatus.textContent = state.processing ? 'Processing…' : (state.queue.length ? `${state.queue.length} waiting` : 'Nothing waiting');
    queueList.innerHTML = state.queue.length ? state.queue.map((q, i) => `<div class="queue-item"><b>${i + 1}</b><div><strong>${escapeHtml(q.mode)}</strong><p>${escapeHtml(q.text)}</p></div><button data-remove-queue="${q.id}" aria-label="Remove queued message">×</button></div>`).join('') : '<div class="queue-empty">Queue is empty.</div>';
  }

  function openQueue() { queuePanel.classList.add('open'); queuePanel.setAttribute('aria-hidden', 'false'); document.querySelector('.queue-overlay').classList.add('show'); renderQueue(); }
  function closeQueue() { queuePanel.classList.remove('open'); queuePanel.setAttribute('aria-hidden', 'true'); document.querySelector('.queue-overlay').classList.remove('show'); }
  function openSidebar() { sidebar.classList.add('open'); sidebarOverlay.classList.add('show'); }
  function closeSidebar() { sidebar.classList.remove('open'); sidebarOverlay.classList.remove('show'); }
  function openWorkspace() { workspace.classList.add('open'); }
  function closeWorkspace() { workspace.classList.remove('open'); }

  function setBackend(ok, text) { state.backendOk = ok; connectionPill.textContent = text; connectionPill.classList.toggle('ok', ok); }
  async function backendCheck() {
    if (!API_BASE) { setBackend(false, 'API not configured'); return false; }
    try {
      const r = await fetch(apiUrl('/readiness'), { headers: authHeaders() });
      setBackend(r.ok, r.ok ? 'Backend reachable' : `Backend ${r.status}`);
      return r.ok;
    } catch { setBackend(false, 'Backend unavailable'); return false; }
  }

  function normalizeResearchBody(body, prior = {}) {
    const run = body.run || body.research_run || prior.run || null;
    const result = body.result || body.synthesis || body.answer_result || prior.result || null;
    const observations = body.observations || run?.observations || prior.observations || [];
    const sources = body.sources || result?.sources || prior.sources || [];
    const status = String(body.status || run?.status || prior.status || 'observed').toLowerCase();
    const answer = body.answer || result?.answer || result?.text || result?.summary || prior.answer || '';
    return { ...prior, run, result, observations, sources, answer, status, stats: body.stats || run?.stats || prior.stats || null, metadata: body.metadata || prior.metadata || {} };
  }
  const terminalStatus = (status) => ['completed','complete','succeeded','success','failed','error','cancelled','canceled'].includes(String(status).toLowerCase());

  async function submitResearch(question, sourceUrls = []) {
    if (!API_BASE) throw new Error('Research API base is not configured');
    const chatId = state.activeChatId;
    addMessage('user', question, {sourceUrls}, chatId);
    renderConversation();
    openWorkspace();
    const payload = { question, depth: 'standard', require_citations: true, max_sources: 8, max_evidence_items: 24, strict_zero_cost_only: true, source_urls: sourceUrls.slice(0, 8) };
    const response = await fetch(apiUrl('/api/v1/research'), { method: 'POST', headers: authHeaders(true), body: JSON.stringify(payload) });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || !body.ok) throw new Error(body.error || `Research request failed (${response.status})`);
    state.research = normalizeResearchBody(body, { runId: body.run_id, status: 'submitted', metadata: body.metadata || {}, sources: body.sources || [], observations: [], answer: '' });
    addMessage('assistant', `Research run ${body.run_id} submitted. Tracking the backend run without changing the worker contract.`, { runId: body.run_id, sources: body.sources || [] }, chatId);
    render();
    state.pollingRunId = body.run_id;
    void pollResearch(body.run_id, chatId);
    return body;
  }

  async function pollResearch(runId, chatId) {
    if (!API_BASE || state.pollingRunId !== runId) return;
    for (let i = 0; i < 60; i += 1) {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      if (state.pollingRunId !== runId) return;
      try {
        const r = await fetch(apiUrl(`/api/v1/research/${encodeURIComponent(runId)}`), { headers: authHeaders() });
        if (!r.ok) throw new Error(`status ${r.status}`);
        const body = await r.json();
        state.research = normalizeResearchBody(body, state.research || { runId });
        renderResearch();
        if (terminalStatus(state.research.status)) {
          state.pollingRunId = null;
          const chat = state.chats.find((c) => c.id === chatId);
          if (chat && !chat.messages.some((m) => m.meta?.runId === runId && m.meta?.final)) {
            const observations = (state.research.observations || []).map((o) => ({ url: o.url, title: o.title, access_state: o.access_state || o.state, retrieval_method: o.retrieval_method }));
            const message = state.research.answer ? `Research run ${runId} completed.\n\n${state.research.answer}` : `Research run ${runId} finished with ${observations.length} observed source record(s).`;
            addMessage('assistant', message, { runId, sources: observations, final: true }, chatId);
            save();
            renderConversation();
          }
          renderResearch();
          return body;
        }
      } catch (err) {
        state.research = { ...(state.research || { runId }), status: 'polling', error: String(err.message || err) };
        renderResearch();
      }
    }
    if (state.pollingRunId === runId) { state.pollingRunId = null; state.research = { ...state.research, status: 'timeout' }; renderResearch(); }
  }

  function renderResearch() {
    if (!state.research) { workspaceBody.innerHTML = '<div class="workspace-card"><strong>No active research run</strong><p>Switch to Research mode to submit a real run.</p></div>'; return; }
    const r = state.research;
    const obs = (r.observations || []).map((o) => `<div class="evidence-row"><span class="state-dot">●</span><div><strong>${escapeHtml(o.title || o.url || 'source')}</strong><small>${escapeHtml(o.access_state || o.state || o.retrieval_method || 'observed')}</small>${o.url ? `<a href="${escapeHtml(o.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(o.url)}</a>` : ''}</div></div>`).join('');
    const answer = r.answer ? `<section class="workspace-card result-card"><div class="card-head"><strong>Result</strong><span>User-facing synthesis</span></div><p class="result-text">${escapeHtml(r.answer)}</p></section>` : '';
    const stats = r.stats ? `<section class="workspace-card"><div class="card-head"><strong>Run summary</strong><span>reported by backend</span></div><pre class="json-block">${escapeHtml(JSON.stringify(r.stats, null, 2))}</pre></section>` : '';
    const error = r.error ? `<div class="error-banner">${escapeHtml(r.error)}</div>` : '';
    workspaceBody.innerHTML = `${error}<section class="workspace-card accent-card"><div class="card-head"><span>Current run</span><b>${escapeHtml(r.status)}</b></div><h3>${escapeHtml(r.runId || r.run?.run_id || 'pending')}</h3><p>Bounded research lifecycle. Strict $0 mode remains enabled.</p><div class="card-actions"><button class="secondary" data-action="research-refresh">Refresh</button>${state.pollingRunId ? '<button class="secondary" data-action="research-stop">Stop polling</button>' : ''}</div></section>${answer}${stats}<section class="workspace-card"><div class="card-head"><strong>Evidence</strong><span>${(r.observations || []).length}</span></div>${obs || '<p class="muted">No observation records returned yet.</p>'}</section>`;
  }

  function render() { renderChats(); setView(state.view); renderConversation(); renderQueue(); renderResearch(); renderAttachments(); }
  function renderAttachments() {
    const host = $('attachment-list');
    if (!host) return;
    host.innerHTML = state.attachments.length ? state.attachments.map((f, i) => `<span class="attachment-chip">${escapeHtml(f.name)} <button data-remove-attachment="${i}" aria-label="Remove ${escapeHtml(f.name)}">×</button></span>`).join('') : '';
  }

  async function send() {
    const text = prompt.value.trim();
    if (!text) return;
    const files = state.attachments.splice(0);
    prompt.value = ''; prompt.style.height = 'auto'; renderAttachments();
    if (currentMode() === 'research') {
      try { composerStatus.textContent = 'Submitting research run…'; await submitResearch(text); composerStatus.textContent = 'Research run is being tracked in the workspace.'; }
      catch (e) { addMessage('assistant', `Research could not be submitted: ${e.message}`); renderConversation(); composerStatus.textContent = 'Research submission failed; inspect backend status and token configuration.'; }
      return;
    }
    addMessage('user', text, { attachments: files.map((f) => ({ name: f.name, size: f.size, type: f.type })) });
    addMessage('assistant', 'This message is stored locally. Switch to Research to send it to the backend research contract.');
    renderConversation();
  }

  function enqueueCurrent() {
    const text = prompt.value.trim();
    if (!text) return;
    const files = state.attachments.splice(0);
    state.queue.push({ id: uuid(), text, mode: currentMode(), attachments: files.map((f) => ({ name: f.name, size: f.size, type: f.type })) });
    prompt.value = ''; prompt.style.height = 'auto'; renderAttachments(); renderQueue(); openQueue(); showToast('Added to queue');
  }
  async function processQueue() {
    if (state.processing || !state.queue.length) return;
    state.processing = true; renderQueue();
    while (state.queue.length) {
      const item = state.queue.shift(); renderQueue();
      if (item.mode === 'research') { try { await submitResearch(item.text); } catch (e) { addMessage('assistant', `Queued research failed: ${e.message}`); renderConversation(); } }
      else { addMessage('user', item.text, { attachments: item.attachments || [] }); addMessage('assistant', 'Queued local chat message processed.'); renderConversation(); }
    }
    state.processing = false; renderQueue();
  }

  function saveMessage(id) {
    const chat = activeChat(); const message = chat?.messages.find((m) => m.id === id); if (!message) return;
    const existing = state.saved.find((s) => s.messageId === id);
    if (existing) { state.saved = state.saved.filter((s) => s.messageId !== id); message.meta = { ...message.meta, saved: false }; }
    else { state.saved.unshift({ id: uuid(), messageId: id, chatId: chat.id, text: message.text, at: Date.now() }); message.meta = { ...message.meta, saved: true }; }
    save(); renderConversation(); showToast(existing ? 'Removed from saved' : 'Saved');
  }
  function removeSaved(id) { state.saved = state.saved.filter((s) => s.messageId !== id); state.chats.forEach((chat) => chat.messages.forEach((m) => { if (m.id === id) m.meta = { ...m.meta, saved: false }; })); save(); renderView(); showToast('Removed from saved'); }
  function repairSavedOwnership() {
    let changed = false;
    state.saved = state.saved.map((item) => {
      if (item.chatId) return item;
      const owner = state.chats.find((chat) => chat.messages?.some((message) => message.id === item.messageId));
      if (!owner) return item;
      changed = true; return { ...item, chatId: owner.id };
    });
    if (changed) save();
  }

  function createProject() {
    const name = window.prompt('Project name'); if (!name?.trim()) return;
    state.projects.unshift({ id: uuid(), name: name.trim(), createdAt: Date.now() });
    save(); setView('projects'); render();
  }
  function assignProject(id) { const chat = activeChat(); if (!chat) return; chat.projectId = id; state.activeProjectId = id; save(); renderChats(); showToast('Current chat assigned to project'); }
  function openProject(id) { const chat = state.chats.find((c) => c.projectId === id); if (!chat) { showToast('Project has no chats yet'); return; } state.activeChatId = chat.id; setView('chats'); render(); closeSidebar(); }
  function openSaved(id) { repairSavedOwnership(); const item = state.saved.find((s) => s.messageId === id); if (!item?.chatId) { showToast('Saved item has no owning chat'); return; } state.activeChatId = item.chatId; setView('chats'); render(); }

  function exportData() {
    const payload = { schema: 'rie.frontend.local.v2', version: 2, chats: state.chats, projects: state.projects, saved: state.saved, exportedAt: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'research-ai-local-data-v2.json'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 0); showToast('Export created');
  }
  function importData() {
    const input = document.createElement('input'); input.type = 'file'; input.accept = 'application/json';
    input.onchange = () => { const file = input.files?.[0]; if (!file) return; const reader = new FileReader(); reader.onload = () => {
      try {
        const data = JSON.parse(reader.result);
        if (!Array.isArray(data.chats) && !Array.isArray(data.projects) && !Array.isArray(data.saved)) throw new Error('unsupported');
        state.chats = Array.isArray(data.chats) ? data.chats.filter((c) => c && c.id) : state.chats;
        state.projects = Array.isArray(data.projects) ? data.projects.filter((p) => p && p.id) : state.projects;
        state.saved = Array.isArray(data.saved) ? data.saved.filter((s) => s && s.messageId) : state.saved;
        state.activeChatId = state.chats[0]?.id || null; repairSavedOwnership(); save(); setView('chats'); render(); showToast('Imported local data');
      } catch { showToast('Invalid or unsupported local export'); }
    }; reader.readAsText(file); };
    input.click();
  }
  function clearData() {
    if (!window.confirm('Clear all browser-local chats, projects and saved items?')) return;
    localStorage.removeItem(CHAT_KEY); localStorage.removeItem(PROJECT_KEY); localStorage.removeItem(SAVED_KEY);
    state.chats = []; state.projects = []; state.saved = []; state.saved = []; state.activeProjectId = null; newChat(); showToast('Local data cleared');
  }

  function selectMode(mode) {
    document.querySelectorAll('[data-mode]').forEach((el) => { const active = el.dataset.mode === mode; el.classList.toggle('active', active); el.setAttribute('aria-selected', active ? 'true' : 'false'); el.tabIndex = active ? 0 : -1; });
    composerStatus.textContent = mode === 'research' ? 'Research uses the real Worker API and keeps evidence/run state explicit.' : 'Chat stays local until a conversational backend exists.';
  }

  function handleAction(action) {
    if (action === 'new-chat') return newChat();
    if (action === 'open-sidebar') return openSidebar();
    if (action === 'close-sidebar') return closeSidebar();
    if (action === 'open-queue') return openQueue();
    if (action === 'close-queue') return closeQueue();
    if (action === 'close-workspace') return closeWorkspace();
    if (action === 'toggle-workspace') return workspace.classList.contains('open') ? closeWorkspace() : openWorkspace();
    if (action === 'backend-check') return backendCheck();
    if (action === 'new-project') return createProject();
    if (action === 'queue') return enqueueCurrent();
    if (action === 'process-queue') return processQueue();
    if (action === 'clear-queue') { state.queue = []; renderQueue(); return; }
    if (action === 'research-refresh') { if (state.research?.runId) { openWorkspace(); state.pollingRunId = state.research.runId; void pollResearch(state.research.runId, state.activeChatId); } return; }
    if (action === 'research-stop') { state.pollingRunId = null; state.research = { ...(state.research || {}), status: 'paused' }; renderResearch(); return; }
    if (action === 'save-session-token') { state.sessionToken = $('session-token')?.value.trim() || ''; backendCheck(); renderView(); showToast(state.sessionToken ? 'Session token active for this tab' : 'Token cleared'); return; }
    if (action === 'clear-session-token') { state.sessionToken = ''; renderView(); backendCheck(); return; }
    if (action === 'export-data') return exportData();
    if (action === 'import-data') return importData();
    if (action === 'clear-data') return clearData();
    if (action === 'attachments') { const input = document.createElement('input'); input.type = 'file'; input.multiple = true; input.onchange = () => { state.attachments = [...input.files]; renderAttachments(); showToast(`${state.attachments.length} file(s) selected locally`); }; input.click(); return; }
    if (action === 'voice') { if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) { const Rec = window.SpeechRecognition || window.webkitSpeechRecognition; const rec = new Rec(); rec.lang = 'en-IN'; rec.onresult = (e) => { prompt.value = e.results[0][0].transcript; prompt.dispatchEvent(new Event('input')); }; rec.start(); showToast('Listening…'); } else showToast('Voice input is not available in this browser'); }
    if (action === 'send') return send();
  }

  document.addEventListener('click', (event) => {
    const action = event.target.closest('[data-action]');
    if (action) { event.preventDefault(); handleAction(action.dataset.action); return; }
    const chat = event.target.closest('[data-chat]');
    if (chat) { state.activeChatId = chat.dataset.chat; setView('chats'); closeSidebar(); render(); return; }
    const starter = event.target.closest('[data-starter]');
    if (starter) { selectMode('research'); prompt.value = starter.dataset.starter; prompt.focus(); return; }
    const mode = event.target.closest('[data-mode]');
    if (mode) { selectMode(mode.dataset.mode); return; }
    const saveButton = event.target.closest('[data-save-message]');
    if (saveButton) { event.preventDefault(); saveMessage(saveButton.dataset.saveMessage); return; }
    const saved = event.target.closest('[data-saved-message]');
    if (saved) { event.preventDefault(); openSaved(saved.dataset.savedMessage); return; }
    const removeSavedButton = event.target.closest('[data-remove-saved]');
    if (removeSavedButton) { event.preventDefault(); removeSaved(removeSavedButton.dataset.removeSaved); return; }
    const project = event.target.closest('[data-project]');
    if (project) { event.preventDefault(); openProject(project.dataset.project); return; }
    const assign = event.target.closest('[data-project-assign]');
    if (assign) { event.preventDefault(); assignProject(assign.dataset.projectAssign); return; }
    const removeQueue = event.target.closest('[data-remove-queue]');
    if (removeQueue) { state.queue = state.queue.filter((q) => q.id !== removeQueue.dataset.removeQueue); renderQueue(); return; }
    const removeAttachment = event.target.closest('[data-remove-attachment]');
    if (removeAttachment) { state.attachments.splice(Number(removeAttachment.dataset.removeAttachment), 1); renderAttachments(); return; }
    const openRun = event.target.closest('[data-open-run]');
    if (openRun) { const id = openRun.dataset.openRun; if (state.research?.runId === id) openWorkspace(); }
  });

  prompt.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); enqueueCurrent(); } });
  prompt.addEventListener('input', () => { prompt.style.height = 'auto'; prompt.style.height = `${Math.min(prompt.scrollHeight, 150)}px`; });
  search.addEventListener('input', renderChats);
  document.addEventListener('keydown', (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); prompt.focus(); } if (e.key === 'Escape') { closeSidebar(); closeQueue(); } });

  load();
  if (!state.chats.length) newChat();
  selectMode('chat');
  render();
  void backendCheck();
})();
