(() => {
  'use strict';

  const CHAT_KEY = 'rie.frontend.chats.v2';
  const PROJECT_KEY = 'rie.frontend.projects.v1';
  const SAVED_KEY = 'rie.frontend.saved.v1';

  const read = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback)); }
    catch { return fallback; }
  };
  const write = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const activeChatId = () => document.querySelector('[data-chat].active')?.dataset.chat || null;

  const reloadToChat = (chatId) => {
    const chats = read(CHAT_KEY, []);
    const index = chats.findIndex((chat) => chat.id === chatId);
    if (index < 0) return false;
    const [chat] = chats.splice(index, 1);
    chats.unshift(chat);
    write(CHAT_KEY, chats);
    window.location.reload();
    return true;
  };

  function openProject(projectId) {
    const chats = read(CHAT_KEY, []);
    const chat = chats.find((item) => item.projectId === projectId);
    if (!chat) {
      const project = read(PROJECT_KEY, []).find((item) => item.id === projectId);
      window.alert(project ? `No chats in “${project.name}” yet.` : 'Project not found.');
      return;
    }
    reloadToChat(chat.id);
  }

  function openSaved(messageId) {
    const saved = read(SAVED_KEY, []);
    const item = saved.find((entry) => entry.messageId === messageId);
    if (!item || !item.chatId) {
      window.alert('This saved item is missing its owning chat.');
      return;
    }
    reloadToChat(item.chatId);
  }

  function saveVisibleMessage(messageId) {
    const chatId = activeChatId();
    if (!chatId) return;
    const chats = read(CHAT_KEY, []);
    const chat = chats.find((item) => item.id === chatId);
    const message = chat?.messages?.find((item) => item.id === messageId);
    if (!message) return;

    const saved = read(SAVED_KEY, []);
    const existing = saved.find((item) => item.messageId === messageId);
    const nextSaved = existing
      ? saved.filter((item) => item.messageId !== messageId)
      : [{ id: crypto.randomUUID?.() || `${Date.now()}-${Math.random()}`, messageId, chatId, text: message.text, at: Date.now() }, ...saved];
    message.meta = { ...(message.meta || {}), saved: !existing };
    write(SAVED_KEY, nextSaved);
    write(CHAT_KEY, chats);
    const node = document.querySelector(`[data-ui-guard-save="${CSS.escape(messageId)}"]`);
    if (node) node.textContent = existing ? 'Save' : 'Saved';
  }

  function stampMessageIds() {
    const chatId = activeChatId();
    if (!chatId) return;
    const chat = read(CHAT_KEY, []).find((item) => item.id === chatId);
    if (!chat) return;
    document.querySelectorAll('#conversation-scroll article.message').forEach((node, index) => {
      const message = chat.messages?.[index];
      if (message) node.dataset.messageId = message.id;
    });
  }

  function addSaveControls() {
    document.querySelectorAll('#conversation-scroll article.message').forEach((article) => {
      const id = article.dataset.messageId;
      if (!id || article.querySelector('[data-save-message], [data-ui-guard-save]')) return;
      const button = document.createElement('button');
      button.className = 'secondary';
      button.dataset.uiGuardSave = id;
      button.textContent = 'Save';
      article.appendChild(button);
    });

    if (document.body.contains(document.querySelector('[data-view="saved"].active'))) return;
    const savedItems = read(SAVED_KEY, []);
    if (!savedItems.length) return;
    const cards = document.querySelectorAll('#conversation-scroll .workspace-card');
    savedItems.forEach((item) => {
      const card = [...cards].find((node) => node.querySelector('strong')?.textContent === item.text);
      if (!card || card.querySelector('[data-saved-message]')) return;
      const button = document.createElement('button');
      button.className = 'secondary';
      button.dataset.savedMessage = item.messageId;
      button.textContent = 'Open chat';
      card.appendChild(button);
    });
  }

  document.addEventListener('click', (event) => {
    const project = event.target.closest('[data-project]');
    if (project) {
      event.preventDefault();
      openProject(project.dataset.project);
      return;
    }
    const saved = event.target.closest('[data-saved-message]');
    if (saved) {
      event.preventDefault();
      openSaved(saved.dataset.savedMessage);
      return;
    }
    const saveButton = event.target.closest('[data-ui-guard-save]');
    if (saveButton) {
      event.preventDefault();
      saveVisibleMessage(saveButton.dataset.uiGuardSave);
    }
  });

  const observer = new MutationObserver(() => {
    stampMessageIds();
    addSaveControls();
  });

  window.addEventListener('load', () => {
    observer.observe(document.getElementById('conversation-scroll') || document.body, { childList: true, subtree: true });
    stampMessageIds();
    addSaveControls();
  });
})();
