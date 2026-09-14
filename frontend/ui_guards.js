(() => {
  'use strict';
  const CHAT_KEY = 'rie.frontend.chats.v2';
  const PROJECT_KEY = 'rie.frontend.projects.v1';
  const SAVED_KEY = 'rie.frontend.saved.v1';
  const read = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback)); } catch { return fallback; } };
  const write = (key, value) => localStorage.setItem(key, JSON.stringify(value));

  function repairSavedOwnership() {
    const chats = read(CHAT_KEY, []);
    const saved = read(SAVED_KEY, []);
    let changed = false;
    const next = saved.map((item) => {
      if (item.chatId) return item;
      const owner = chats.find((chat) => chat.messages?.some((message) => message.id === item.messageId));
      if (!owner) return item;
      changed = true;
      return { ...item, chatId: owner.id };
    });
    if (changed) write(SAVED_KEY, next);
  }

  function reloadToChat(chatId) {
    const chats = read(CHAT_KEY, []);
    const index = chats.findIndex((chat) => chat.id === chatId);
    if (index < 0) return false;
    const [chat] = chats.splice(index, 1);
    chats.unshift(chat);
    write(CHAT_KEY, chats);
    window.location.reload();
    return true;
  }

  document.addEventListener('click', (event) => {
    const project = event.target.closest('[data-project]');
    if (project && !event.defaultPrevented) { event.preventDefault(); const chats = read(CHAT_KEY, []); const chat = chats.find((c) => c.projectId === project.dataset.project); if (chat) reloadToChat(chat.id); else window.alert('Project has no chats yet.'); return; }
    const saved = event.target.closest('[data-saved-message]');
    if (saved && !event.defaultPrevented) { event.preventDefault(); repairSavedOwnership(); const item = read(SAVED_KEY, []).find((s) => s.messageId === saved.dataset.savedMessage); if (item?.chatId) reloadToChat(item.chatId); else window.alert('This saved item is missing its owning chat.'); return; }
  });

  window.addEventListener('load', repairSavedOwnership);
})();
