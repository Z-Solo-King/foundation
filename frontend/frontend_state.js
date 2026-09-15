(() => {
  'use strict';

  const API_BASE = (document.body.dataset.apiBase || '').replace(/\/$/, '');
  const keys = Object.freeze({
    chats: 'rie.frontend.chats.v2',
    projects: 'rie.frontend.projects.v1',
    saved: 'rie.frontend.saved.v1',
    session: 'rie.frontend.sessionToken.v1',
    activeChat: 'rie.frontend.research.activeChat.v1',
  });

  const state = {
    chats: [],
    projects: [],
    saved: [],
    activeChatId: null,
    activeProjectId: null,
    view: 'chats',
    mode: 'chat',
    backendOk: false,
    backendText: 'Checking backend…',
  };

  const read = (key, fallback) => {
    try {
      const value = JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback));
      return value ?? fallback;
    } catch {
      return fallback;
    }
  };

  const write = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const uuid = () => crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>\"']/g, (c) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
  const apiUrl = (path) => `${API_BASE}${path}`;
  const token = () => sessionStorage.getItem(keys.session) || '';
  const authHeaders = (json = false) => {
    const headers = { Accept: 'application/json' };
    if (json) headers['Content-Type'] = 'application/json';
    if (token()) headers.Authorization = `Bearer ${token()}`;
    return headers;
  };

  function load() {
    state.chats = read(keys.chats, []).filter(Boolean);
    state.projects = read(keys.projects, []).filter(Boolean);
    state.saved = read(keys.saved, []).filter(Boolean);
    state.chats.forEach((chat) => {
      if (!Array.isArray(chat.messages)) chat.messages = [];
    });
    const remembered = localStorage.getItem(keys.activeChat);
    state.activeChatId = remembered && state.chats.some((chat) => chat.id === remembered)
      ? remembered
      : state.chats[0]?.id || null;
    state.activeProjectId = state.chats.find((chat) => chat.id === state.activeChatId)?.projectId || null;
  }

  function persist() {
    write(keys.chats, state.chats);
    write(keys.projects, state.projects);
    write(keys.saved, state.saved);
  }

  function activeChat() {
    return state.chats.find((chat) => chat.id === state.activeChatId) || null;
  }

  function ensureChat() {
    let chat = activeChat();
    if (!chat) {
      chat = { id: uuid(), title: 'New chat', messages: [], createdAt: Date.now(), projectId: state.activeProjectId || null };
      state.chats.unshift(chat);
      state.activeChatId = chat.id;
      localStorage.setItem(keys.activeChat, chat.id);
      persist();
    }
    return chat;
  }

  function setActiveChat(chatId) {
    if (!state.chats.some((chat) => chat.id === chatId)) return false;
    state.activeChatId = chatId;
    state.activeProjectId = activeChat()?.projectId || null;
    localStorage.setItem(keys.activeChat, chatId);
    return true;
  }

  function addMessage(role, text, meta = {}, chatId = state.activeChatId) {
    const chat = state.chats.find((item) => item.id === chatId) || ensureChat();
    const message = { id: uuid(), role, text: String(text || ''), meta: meta || {}, at: Date.now() };
    chat.messages.push(message);
    if (role === 'user' && chat.title === 'New chat') chat.title = message.text.slice(0, 48) || 'New chat';
    persist();
    document.dispatchEvent(new CustomEvent('rie:chat-updated', { detail: { chatId: chat.id, messageId: message.id } }));
    return message;
  }

  function updateMessage(messageId, patch) {
    for (const chat of state.chats) {
      const message = chat.messages?.find((item) => item.id === messageId);
      if (message) {
        Object.assign(message, patch);
        persist();
        document.dispatchEvent(new CustomEvent('rie:chat-updated', { detail: { chatId: chat.id, messageId } }));
        return message;
      }
    }
    return null;
  }

  function newChat() {
    const chat = { id: uuid(), title: 'New chat', messages: [], createdAt: Date.now(), projectId: state.activeProjectId || null };
    state.chats.unshift(chat);
    setActiveChat(chat.id);
    state.view = 'chats';
    persist();
    document.dispatchEvent(new CustomEvent('rie:chat-updated', { detail: { chatId: chat.id } }));
    return chat;
  }

  window.RIEFrontend = window.RIEFrontend || {};
  Object.assign(window.RIEFrontend, {
    state,
    keys,
    API_BASE,
    read,
    write,
    uuid,
    escapeHtml,
    apiUrl,
    token,
    authHeaders,
    load,
    persist,
    activeChat,
    ensureChat,
    setActiveChat,
    addMessage,
    updateMessage,
    newChat,
  });
})();
