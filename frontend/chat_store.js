(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before chat_store.js');

  function repairSavedOwnership() {
    let changed = false;
    const next = api.state.saved.map((item) => {
      if (item.chatId) return item;
      const owner = api.state.chats.find((chat) => chat.messages?.some((message) => message.id === item.messageId));
      if (!owner) return item;
      changed = true;
      return { ...item, chatId: owner.id };
    });
    if (changed) {
      api.state.saved = next;
      api.persist();
    }
  }

  function createProject(name) {
    const trimmed = String(name || '').trim();
    if (!trimmed) return null;
    const project = { id: api.uuid(), name: trimmed, createdAt: Date.now() };
    api.state.projects.unshift(project);
    api.state.activeProjectId = project.id;
    api.persist();
    return project;
  }

  function renameProject(projectId, name) {
    const project = api.state.projects.find((item) => item.id === projectId);
    const trimmed = String(name || '').trim();
    if (!project || !trimmed) return false;
    project.name = trimmed;
    api.persist();
    return true;
  }

  function deleteProject(projectId) {
    if (!api.state.projects.some((item) => item.id === projectId)) return false;
    api.state.projects = api.state.projects.filter((item) => item.id !== projectId);
    api.state.chats.forEach((chat) => {
      if (chat.projectId === projectId) chat.projectId = null;
    });
    if (api.state.activeProjectId === projectId) api.state.activeProjectId = null;
    api.persist();
    return true;
  }

  function assignCurrentChat(projectId) {
    const chat = api.activeChat();
    if (!chat || !api.state.projects.some((item) => item.id === projectId)) return false;
    chat.projectId = projectId;
    api.state.activeProjectId = projectId;
    api.persist();
    document.dispatchEvent(new CustomEvent('rie:chat-updated', { detail: { chatId: chat.id } }));
    return true;
  }

  function saveMessage(messageId) {
    repairSavedOwnership();
    const existing = api.state.saved.find((item) => item.messageId === messageId);
    if (existing) {
      api.state.saved = api.state.saved.filter((item) => item.messageId !== messageId);
      api.updateMessage(messageId, { meta: { ...(api.state.chats.flatMap((c) => c.messages || []).find((m) => m.id === messageId)?.meta || {}), saved: false } });
      return false;
    }
    const owner = api.state.chats.find((chat) => chat.messages?.some((message) => message.id === messageId));
    const message = owner?.messages?.find((item) => item.id === messageId);
    if (!owner || !message) return false;
    api.state.saved.unshift({ id: api.uuid(), messageId, chatId: owner.id, text: message.text, at: Date.now() });
    api.updateMessage(messageId, { meta: { ...(message.meta || {}), saved: true } });
    return true;
  }

  function removeSaved(messageId) {
    api.state.saved = api.state.saved.filter((item) => item.messageId !== messageId);
    const owner = api.state.chats.find((chat) => chat.messages?.some((message) => message.id === messageId));
    const message = owner?.messages?.find((item) => item.id === messageId);
    if (message) message.meta = { ...(message.meta || {}), saved: false };
    api.persist();
    document.dispatchEvent(new CustomEvent('rie:chat-updated', { detail: { chatId: owner?.id || null } }));
  }

  function openSaved(messageId) {
    repairSavedOwnership();
    const item = api.state.saved.find((saved) => saved.messageId === messageId);
    return item?.chatId && api.setActiveChat(item.chatId) ? item.chatId : null;
  }

  function exportData() {
    return JSON.stringify({ schema: 'rie.frontend.local-data/v2', exported_at: new Date().toISOString(), chats: api.state.chats, projects: api.state.projects, saved: api.state.saved }, null, 2);
  }

  function importData(raw) {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
    if (!parsed || parsed.schema !== 'rie.frontend.local-data/v2' || !Array.isArray(parsed.chats) || !Array.isArray(parsed.projects) || !Array.isArray(parsed.saved)) {
      throw new Error('Invalid frontend export schema');
    }
    const chats = parsed.chats.filter((chat) => chat && typeof chat.id === 'string' && Array.isArray(chat.messages));
    const projects = parsed.projects.filter((project) => project && typeof project.id === 'string' && typeof project.name === 'string');
    const saved = parsed.saved.filter((item) => item && typeof item.messageId === 'string');
    if (chats.length !== parsed.chats.length || projects.length !== parsed.projects.length || saved.length !== parsed.saved.length) throw new Error('Import contains malformed records');
    api.state.chats = chats;
    api.state.projects = projects;
    api.state.saved = saved;
    api.state.activeChatId = chats[0]?.id || null;
    api.state.activeProjectId = chats[0]?.projectId || null;
    api.persist();
    repairSavedOwnership();
    document.dispatchEvent(new CustomEvent('rie:chat-updated', { detail: { imported: true } }));
  }

  function clearData() {
    api.state.chats = [];
    api.state.projects = [];
    api.state.saved = [];
    api.state.activeChatId = null;
    api.state.activeProjectId = null;
    api.persist();
    localStorage.removeItem(api.keys.activeChat);
    document.dispatchEvent(new CustomEvent('rie:chat-updated', { detail: { cleared: true } }));
  }

  api.chatStore = Object.freeze({ repairSavedOwnership, createProject, renameProject, deleteProject, assignCurrentChat, saveMessage, removeSaved, openSaved, exportData, importData, clearData });
  repairSavedOwnership();
})();
