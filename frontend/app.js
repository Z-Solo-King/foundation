(() => {
  const root = document.documentElement;
  const sidebar = document.getElementById('sidebar');
  const overlay = document.querySelector('.mobile-overlay');
  const workspace = document.getElementById('workspace');
  const toast = document.getElementById('toast');
  const prompt = document.getElementById('prompt');
  const search = document.getElementById('chat-search');
  const settingsDialog = document.getElementById('settings-dialog');
  let toastTimer;

  const showToast = (message) => {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 1700);
  };

  const openSidebar = () => {
    sidebar.classList.add('open');
    overlay.classList.add('show');
  };

  const closeSidebar = () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
  };

  const openWorkspace = () => workspace.classList.add('open');
  const closeWorkspace = () => workspace.classList.remove('open');

  const sendMessage = () => {
    const value = prompt.value.trim();
    if (!value) return;
    const scroll = document.getElementById('conversation-scroll');
    const message = document.createElement('article');
    message.className = 'message user-message';
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble user-bubble';
    bubble.textContent = value;
    message.appendChild(bubble);
    scroll.appendChild(message);
    prompt.value = '';
    prompt.style.height = 'auto';
    scroll.scrollTo({ top: scroll.scrollHeight, behavior: 'smooth' });
    showToast(document.querySelector('.mode.active')?.dataset.mode === 'research' ? 'Research request queued' : 'Message sent');
  };

  const copyAnswer = () => {
    const text = document.querySelector('.assistant-message .message-text')?.innerText || '';
    if (navigator.clipboard && text) navigator.clipboard.writeText(text).catch(() => {});
    showToast('Answer copied');
  };

  const setTheme = (theme) => {
    if (theme === 'system') root.removeAttribute('data-theme');
    else root.dataset.theme = theme;
    document.querySelectorAll('[data-theme]').forEach((button) => button.classList.toggle('active', button.dataset.theme === theme));
    localStorage.setItem('my-ai-theme', theme);
  };

  const setAccent = (accent) => {
    root.dataset.accent = accent === 'blue' ? 'blue' : accent;
    document.querySelectorAll('[data-accent]').forEach((button) => button.classList.toggle('active', button.dataset.accent === accent));
    localStorage.setItem('my-ai-accent', accent);
  };

  const setDensity = (density) => {
    document.body.classList.toggle('compact', density === 'compact');
    document.querySelectorAll('[data-density]').forEach((button) => button.classList.toggle('active', button.dataset.density === density));
    localStorage.setItem('my-ai-density', density);
  };

  const filterChats = () => {
    const q = search.value.toLowerCase().trim();
    document.querySelectorAll('.chat-row').forEach((row) => {
      row.hidden = Boolean(q && !row.innerText.toLowerCase().includes(q));
    });
  };

  const handleAction = (action) => {
    switch (action) {
      case 'new-chat':
        closeSidebar();
        showToast('New chat');
        prompt.focus();
        break;
      case 'open-sidebar': openSidebar(); break;
      case 'close-sidebar': closeSidebar(); break;
      case 'close-workspace': closeWorkspace(); break;
      case 'open-sources': openWorkspace(); showToast('Sources opened'); break;
      case 'show-research': openWorkspace(); break;
      case 'copy': copyAnswer(); break;
      case 'save': showToast('Saved to Saved'); break;
      case 'regenerate': showToast('Regeneration requested'); break;
      case 'attachments': showToast('Attach a file or image'); break;
      case 'voice': showToast('Voice input is ready for integration'); break;
      case 'send': sendMessage(); break;
      case 'share': showToast('Share link ready for integration'); break;
      case 'search': search.focus(); openSidebar(); break;
      case 'more': showToast('More options'); break;
      case 'more-message': showToast('More message actions'); break;
      case 'profile': settingsDialog.showModal(); break;
      case 'close-settings': settingsDialog.close(); break;
      default: break;
    }
  };

  document.addEventListener('click', (event) => {
    const actionButton = event.target.closest('[data-action]');
    if (actionButton) handleAction(actionButton.dataset.action);

    const mode = event.target.closest('[data-mode]');
    if (mode) {
      document.querySelectorAll('[data-mode]').forEach((button) => button.classList.toggle('active', button === mode));
      showToast(mode.dataset.mode === 'research' ? 'Research mode selected' : 'Chat mode selected');
    }

    const view = event.target.closest('[data-view]');
    if (view) {
      document.querySelectorAll('[data-view]').forEach((button) => button.classList.toggle('active', button === view));
      showToast(`${view.innerText.trim()} view`);
      closeSidebar();
    }

    const chat = event.target.closest('[data-chat]');
    if (chat) {
      document.querySelectorAll('[data-chat]').forEach((row) => row.classList.toggle('active', row === chat));
      closeSidebar();
      showToast(`Opened ${chat.querySelector('strong')?.textContent || 'chat'}`);
    }

    const theme = event.target.closest('[data-theme]');
    if (theme) setTheme(theme.dataset.theme);
    const accent = event.target.closest('[data-accent]');
    if (accent) setAccent(accent.dataset.accent);
    const density = event.target.closest('[data-density]');
    if (density) setDensity(density.dataset.density);
  });

  prompt.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  prompt.addEventListener('input', () => {
    prompt.style.height = 'auto';
    prompt.style.height = `${Math.min(prompt.scrollHeight, 130)}px`;
  });

  search.addEventListener('input', filterChats);

  window.addEventListener('keydown', (event) => {
    const key = event.key.toLowerCase();
    if ((event.metaKey || event.ctrlKey) && key === 'k') {
      event.preventDefault();
      prompt.focus();
    }
    if (event.key === 'Escape') {
      closeSidebar();
      closeWorkspace();
      if (settingsDialog.open) settingsDialog.close();
    }
  });

  const storedTheme = localStorage.getItem('my-ai-theme');
  const storedAccent = localStorage.getItem('my-ai-accent');
  const storedDensity = localStorage.getItem('my-ai-density');
  if (storedTheme) setTheme(storedTheme);
  if (storedAccent) setAccent(storedAccent);
  if (storedDensity) setDensity(storedDensity);
})();
