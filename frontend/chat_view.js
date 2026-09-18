(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api?.chatStore) throw new Error('chat_store.js must load before chat_view.js');

  const el = {
    sidebar: document.getElementById('sidebar'), sidebarOverlay: document.querySelector('.mobile-overlay'), conversation: document.getElementById('conversation-scroll'), emptyState: document.getElementById('empty-state'), chatList: document.getElementById('chat-list'), search: document.getElementById('chat-search'), mobileTitle: document.getElementById('mobile-title'), toast: document.getElementById('toast'), connectionPill: document.getElementById('connection-pill'),
  };
  const safeSourceUrl = (value) => {
    try {
      const url = new URL(String(value || ''), window.location.origin);
      return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : '';
    } catch {
      return '';
    }
  };
  const renderSources = (sources = []) => sources.map((source, index) => {
    const safeUrl = safeSourceUrl(source.url);
    const title = source.title || source.url || 'source';
    const label = api.escapeHtml(title);
    return `<div class="source-row"><span>${index + 1}</span>${safeUrl ? `<a href="${api.escapeHtml(safeUrl)}" target="_blank" rel="noopener noreferrer">${label}</a>` : `<span class="source-label">${label}</span>`}<small>${api.escapeHtml(source.access_state || source.state || source.retrieval_method || 'observed')}</small></div>`;
  }).join('');
  function toast(message) { if (!el.toast) return; el.toast.textContent = message; el.toast.classList.add('show'); clearTimeout(toast.timer); toast.timer = setTimeout(() => el.toast.classList.remove('show'), 2400); }

  function renderSidebar() {
    if (!el.chatList) return;
    const query = el.search?.value.trim().toLowerCase() || '';
    const chats = api.state.chats.filter((chat) => !query || String(chat.title || '').toLowerCase().includes(query)).slice(0, 100);
    el.chatList.innerHTML = chats.length ? chats.map((chat) => `<button class="chat-row ${chat.id === api.state.activeChatId ? 'active' : ''}" data-chat="${api.escapeHtml(chat.id)}" aria-label="Open chat ${api.escapeHtml(chat.title || 'New chat')}" aria-current="${chat.id === api.state.activeChatId ? 'page' : 'false'}"><span class="chat-icon">✦</span><span><strong>${api.escapeHtml(chat.title || 'New chat')}</strong><small>${chat.messages?.length || 0} message${(chat.messages?.length || 0) === 1 ? '' : 's'} · ${new Date(chat.createdAt || Date.now()).toLocaleDateString()}</small></span></button>`).join('') : '<div class="sidebar-empty">No matching chats.</div>';
  }

  function messageRenderSignature(message) {
    return JSON.stringify({
      id: message.id,
      role: message.role,
      text: message.text,
      at: message.at,
      runId: message.meta?.runId || '',
      saved: Boolean(message.meta?.saved),
      pending: Boolean(message.meta?.pending),
      error: Boolean(message.meta?.error),
      operation: message.meta?.operation || '',
      sources: Array.isArray(message.meta?.sources) ? message.meta.sources : [],
    });
  }

  function messageHtml(message) {
    const runButton = message.meta?.runId ? `<button class="secondary" data-open-run="${api.escapeHtml(message.meta.runId)}">Open run</button>` : '';
    const saveLabel = message.meta?.saved ? 'Saved' : 'Save';
    const sources = Array.isArray(message.meta?.sources) && message.meta.sources.length ? `<div class="source-list" aria-label="Sources">${renderSources(message.meta.sources)}</div>` : '';
    const pending = message.meta?.pending ? '<span class="message-state">Sending…</span>' : '';
    const error = message.meta?.error ? '<span class="message-state error">Request failed</span>' : '';
    const operation = message.meta?.operation ? `<span class="message-state">${api.escapeHtml(message.meta.operation)}</span>` : '';
    const label = message.role === 'user' ? 'You' : 'Heroic AI';
    const signature = api.escapeHtml(messageRenderSignature(message));
    return `<article class="message ${message.role === 'user' ? 'user-message' : 'assistant-message'} ${message.meta?.error ? 'message-error' : ''}" data-message-id="${api.escapeHtml(message.id)}" data-render-signature="${signature}"><div class="message-meta"><span>${label}</span><time datetime="${new Date(message.at || Date.now()).toISOString()}">${new Date(message.at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>${pending}${error}${operation}</div><div class="message-bubble">${api.escapeHtml(message.text)}</div><div class="message-actions"><button class="secondary" data-save-message="${api.escapeHtml(message.id)}" aria-label="${saveLabel} message">${saveLabel}</button>${runButton}</div>${sources}</article>`;
  }

  function renderConversation() {
    if (api.state.view !== 'chats') return;
    const chat = api.activeChat();
    if (el.mobileTitle) el.mobileTitle.textContent = chat?.title || 'New chat';
    if (!chat || chat.messages.length === 0) {
      el.conversation.innerHTML = '';
      if (el.emptyState) { el.emptyState.hidden = false; el.conversation.append(el.emptyState); }
      return;
    }
    if (el.emptyState) el.emptyState.hidden = true;

    const existing = Array.from(el.conversation.querySelectorAll(':scope > article.message'));
    const sameCount = existing.length === chat.messages.length;
    const sameOrder = sameCount && chat.messages.every((message, index) => existing[index]?.dataset.messageId === message.id);

    if (!sameCount || !sameOrder) {
      el.conversation.innerHTML = chat.messages.map(messageHtml).join('');
      el.conversation.scrollTop = el.conversation.scrollHeight;
      return;
    }

    let changed = false;
    chat.messages.forEach((message, index) => {
      const node = existing[index];
      const signature = messageRenderSignature(message);
      if (node.dataset.renderSignature === signature) return;
      node.outerHTML = messageHtml(message);
      changed = true;
    });
    if (changed) el.conversation.scrollTop = el.conversation.scrollHeight;
  }

  function renderProjects() {
    const projects = api.state.projects;
    return `<div class="message view-panel"><div class="view-heading"><div><span class="eyebrow">Workspace</span><h2>Projects</h2><p>Browser-local organization. Projects do not imply a server-backed authority.</p></div><button class="primary" data-action="new-project">＋ New project</button></div><div class="view-grid">${projects.length ? projects.map((project) => { const count = api.state.chats.filter((chat) => chat.projectId === project.id).length; return `<section class="workspace-card project-card"><div class="card-head"><strong>${api.escapeHtml(project.name)}</strong><span>${count} chat${count === 1 ? '' : 's'}</span></div><div class="card-actions"><button class="secondary" data-project="${api.escapeHtml(project.id)}">Open</button><button class="secondary" data-project-assign="${api.escapeHtml(project.id)}">Use for current chat</button><button class="secondary" data-project-rename="${api.escapeHtml(project.id)}">Rename</button><button class="danger" data-project-delete="${api.escapeHtml(project.id)}">Delete</button></div></section>`; }).join('') : '<div class="workspace-card empty-card"><strong>No projects yet</strong><p>Create one to group browser-local chats.</p></div>'}</div></div>`;
  }

  function renderSaved() {
    api.chatStore.repairSavedOwnership();
    const saved = api.state.saved;
    return `<div class="message view-panel"><div class="view-heading"><div><span class="eyebrow">Local library</span><h2>Saved</h2><p>Saved messages stay in this browser.</p></div></div><div class="view-grid">${saved.length ? saved.map((item) => `<section class="workspace-card saved-card"><strong>${api.escapeHtml(item.text)}</strong><small>${new Date(item.at || Date.now()).toLocaleString()}</small><div class="card-actions"><button class="secondary" data-saved-message="${api.escapeHtml(item.messageId)}">Open chat</button><button class="danger" data-remove-saved="${api.escapeHtml(item.messageId)}">Remove</button></div></section>`).join('') : '<div class="workspace-card empty-card"><strong>Nothing saved yet</strong><p>Use Save on a research or chat message.</p></div>'}</div></div>`;
  }

  function renderSettings() {
    const tokenPresent = Boolean(api.token());
    return `<div class="message view-panel"><div class="view-heading"><div><span class="eyebrow">Configuration</span><h2>Settings</h2><p>Browser-local controls for this frontend surface.</p></div></div><section class="workspace-card"><div class="card-head"><strong>Backend</strong><span class="status-dot ${api.state.backendOk ? 'ok' : ''}">${api.escapeHtml(api.state.backendText)}</span></div><p class="mono">${api.escapeHtml(api.API_BASE || 'Not configured')}</p><p class="muted">Session authentication is held only in session storage for this browser session.</p><label class="field-label" for="session-token">Session token</label><input id="session-token" type="password" placeholder="${tokenPresent ? 'Token already set for this session' : 'Optional short-lived token'}" autocomplete="off" value=""><div class="card-actions"><button class="secondary" data-action="save-session-token">Use for this tab</button><button class="secondary" data-action="clear-session-token">Clear</button><button class="secondary" data-action="backend-check">Check backend</button></div></section><section class="workspace-card"><div class="card-head"><strong>Local data</strong><span>${api.state.chats.length} chats · ${api.state.projects.length} projects · ${api.state.saved.length} saved</span></div><p class="muted">Exports are versioned local data only. Imports are schema-validated before replacing local state.</p><div class="card-actions"><button class="secondary" data-action="export-data">Export</button><button class="secondary" data-action="import-data">Import</button><button class="danger" data-action="clear-data">Clear local data</button></div></section></div>`;
  }
  function renderView() {
    if (api.state.view === 'chats') return renderConversation();
    if (el.mobileTitle) el.mobileTitle.textContent = api.state.view[0].toUpperCase() + api.state.view.slice(1);
    if (el.emptyState) el.emptyState.hidden = true;
    const html = api.state.view === 'projects' ? renderProjects() : api.state.view === 'saved' ? renderSaved() : renderSettings();
    el.conversation.innerHTML = html || '';
  }
  function render() {
    renderSidebar(); renderView();
    document.querySelectorAll('[data-view]').forEach((node) => { const active = node.dataset.view === api.state.view; node.classList.toggle('active', active); node.setAttribute('aria-current', active ? 'true' : 'false'); });
  }
  function openSidebar() { el.sidebar?.classList.add('open'); el.sidebarOverlay?.classList.add('show'); }
  function closeSidebar() { el.sidebar?.classList.remove('open'); el.sidebarOverlay?.classList.remove('show'); }

  document.addEventListener('click', (event) => {
    const chat = event.target.closest('[data-chat]');
    if (chat) { event.preventDefault(); api.setActiveChat(chat.dataset.chat); api.state.view = 'chats'; closeSidebar(); render(); return; }
    const nav = event.target.closest('[data-view]');
    if (nav) { event.preventDefault(); api.state.view = nav.dataset.view; closeSidebar(); render(); return; }
    if (event.target.closest('[data-action="new-chat"]')) { event.preventDefault(); api.newChat(); closeSidebar(); render(); document.getElementById('prompt')?.focus(); return; }
    if (event.target.closest('[data-action="open-sidebar"]')) { event.preventDefault(); openSidebar(); return; }
    if (event.target.closest('[data-action="close-sidebar"]')) { event.preventDefault(); closeSidebar(); return; }
    const save = event.target.closest('[data-save-message]');
    if (save) { event.preventDefault(); api.chatStore.saveMessage(save.dataset.saveMessage); render(); return; }
    const removeSaved = event.target.closest('[data-remove-saved]');
    if (removeSaved) { event.preventDefault(); api.chatStore.removeSaved(removeSaved.dataset.removeSaved); render(); return; }
    const openSaved = event.target.closest('[data-saved-message]');
    if (openSaved) { event.preventDefault(); const chatId = api.chatStore.openSaved(openSaved.dataset.savedMessage); if (chatId) { api.state.view = 'chats'; render(); } else toast('Saved item has no owning chat.'); return; }
    if (event.target.closest('[data-action="new-project"]')) { event.preventDefault(); const name = window.prompt('Project name'); if (name) { api.chatStore.createProject(name); render(); } return; }
    const assign = event.target.closest('[data-project-assign]');
    if (assign) { event.preventDefault(); api.chatStore.assignCurrentChat(assign.dataset.projectAssign); render(); return; }
    const rename = event.target.closest('[data-project-rename]');
    if (rename) { event.preventDefault(); const p = api.state.projects.find((item) => item.id === rename.dataset.projectRename); const name = window.prompt('Rename project', p?.name || ''); if (name) { api.chatStore.renameProject(rename.dataset.projectRename, name); render(); } return; }
    const removeProject = event.target.closest('[data-project-delete]');
    if (removeProject) { event.preventDefault(); if (window.confirm('Delete this browser-local project? Chats will remain.')) { api.chatStore.deleteProject(removeProject.dataset.projectDelete); render(); } return; }
    if (event.target.closest('[data-action="backend-check"]')) { event.preventDefault(); void api.checkBackend?.(); return; }
    if (event.target.closest('[data-action="export-data"]')) { event.preventDefault(); api.exportLocalData?.(); return; }
    if (event.target.closest('[data-action="import-data"]')) { event.preventDefault(); api.importLocalData?.(); return; }
    if (event.target.closest('[data-action="clear-data"]')) { event.preventDefault(); if (window.confirm('Clear chats, projects and saved items from this browser?')) { api.chatStore.clearData(); render(); } return; }
    if (event.target.closest('[data-action="save-session-token"]')) {
      event.preventDefault();
      const input = document.getElementById('session-token');
      const value = input?.value.trim() || '';
      if (!value) { toast('Enter a session token first.'); return; }
      sessionStorage.setItem(api.keys.session, value);
      document.dispatchEvent(new Event('rie:session-changed'));
      void api.checkBackend?.();
      toast('Session token stored for this tab.');
      return;
    }
    if (event.target.closest('[data-action="clear-session-token"]')) {
      event.preventDefault();
      sessionStorage.removeItem(api.keys.session);
      document.dispatchEvent(new Event('rie:session-changed'));
      void api.checkBackend?.();
      toast('Session token cleared.');
      return;
    }
  }, false);

  el.search?.addEventListener('input', renderSidebar);
  document.addEventListener('rie:chat-updated', render);
  document.addEventListener('rie:session-changed', render);
  window.addEventListener('storage', (event) => { if ([api.keys.chats, api.keys.projects, api.keys.saved].includes(event.key)) { api.load(); render(); } });

  api.chatView = Object.freeze({ render, renderSidebar, renderConversation, renderView, toast });
})();