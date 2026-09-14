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
    if (!item) return;
    if (!reloadToChat(item.chatId)) {
      window.alert('The saved message no longer has an available chat.');
    }
  }

  function addSaveControls() {
    const articles = document.querySelectorAll('#conversation-scroll article.message');
    articles.forEach((article) => {
      if (article.querySelector('[data-ui-guard-save]')) return;
      const bubble = article.querySelector('.message-bubble');
      const id = article.dataset.messageId;
      if (!bubble || !id) return;
      const controls = document.createElement('div');
      controls.innerHTML = `<button class="secondary" data-ui-guard-save="${id}">Save</button>`;
      article.appendChild(controls.firstElementChild);
    });
  }

  function stampMessageIds() {
    const chats = read(CHAT_KEY, []);
    const activeId = chats[0]?.id;
    if (!activeId) return;
    const active = chats.find((chat) => chat.id === activeId);
    if (!active) return;
    const nodes = document.querySelectorAll('#conversation-scroll article.message');
    nodes.forEach((node, index) => {
      const message = active.messages?.[index];
      if (message) node.dataset.messageId = message.id;
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
