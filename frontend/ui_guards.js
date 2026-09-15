(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before ui_guards.js');

  function repairSavedOwnership() {
    if (!api.chatStore?.repairSavedOwnership) return;
    api.chatStore.repairSavedOwnership();
  }

  function openChat(chatId) {
    if (!api.setActiveChat(chatId)) return false;
    api.state.view = 'chats';
    api.chatView?.render();
    return true;
  }

  document.addEventListener('click', (event) => {
    const project = event.target.closest('[data-project]');
    if (project && !event.defaultPrevented) {
      event.preventDefault();
      const chat = api.state.chats.find((candidate) => candidate.projectId === project.dataset.project);
      if (chat) openChat(chat.id);
      else api.chatView?.toast('Project has no chats yet.');
      return;
    }
    const saved = event.target.closest('[data-saved-message]');
    if (saved && !event.defaultPrevented) {
      event.preventDefault();
      const item = api.state.saved.find((candidate) => candidate.messageId === saved.dataset.savedMessage);
      if (item?.chatId) openChat(item.chatId);
      else api.chatView?.toast('This saved item is missing its owning chat.');
    }
  });

  window.addEventListener('load', repairSavedOwnership);
})();
