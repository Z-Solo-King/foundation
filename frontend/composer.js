(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before composer.js');

  const prompt = document.getElementById('prompt');
  const modeButtons = [...document.querySelectorAll('.mode')];
  const composerStatus = document.getElementById('composer-status');
  const queueButton = document.getElementById('queue-button');
  const workspace = document.getElementById('workspace');

  function setStatus(text, tone = '') {
    if (!composerStatus) return;
    composerStatus.textContent = text;
    composerStatus.dataset.tone = tone;
  }

  function renderMode() {
    const researchMode = api.state.mode === 'research';
    modeButtons.forEach((button) => {
      const active = button.dataset.mode === api.state.mode;
      button.classList.toggle('active', active);
      button.setAttribute('aria-selected', active ? 'true' : 'false');
      button.tabIndex = active ? 0 : -1;
    });
    if (prompt) {
      prompt.placeholder = researchMode ? 'What should the engine research and verify?' : 'Ask Heroic AI…';
      prompt.setAttribute('aria-label', researchMode ? 'Research question' : 'Message');
    }
    if (queueButton) {
      queueButton.hidden = !researchMode;
      queueButton.disabled = !researchMode;
      queueButton.setAttribute('aria-hidden', researchMode ? 'false' : 'true');
      queueButton.title = researchMode ? 'Queue research (Ctrl/Cmd+Enter)' : 'Queue is available in Research mode';
    }
  }

  function selectMode(mode) {
    if (!['chat', 'research'].includes(mode)) return;
    api.state.mode = mode;
    renderMode();
    if (mode === 'research') workspace?.classList.add('open');
    setStatus(mode === 'research' ? 'Research uses the canonical backend lifecycle and evidence contract.' : 'Chat uses the public governed Heroic AI endpoint; a session token is only needed for protected operational features.');
    document.dispatchEvent(new CustomEvent('rie:mode-changed', { detail: { mode } }));
  }

  function resize() {
    if (!prompt) return;
    prompt.style.height = 'auto';
    prompt.style.height = `${Math.min(prompt.scrollHeight, 150)}px`;
  }

  function handleVoice() {
    const supported = Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
    if (!supported) {
      setStatus('Voice input is unavailable in this browser.');
      return;
    }
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Recognition();
    recognition.lang = navigator.language || 'en-IN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    setStatus('Listening…');
    recognition.onresult = (event) => {
      const text = event.results?.[0]?.[0]?.transcript || '';
      prompt.value = `${prompt.value}${prompt.value ? ' ' : ''}${text}`;
      resize();
      setStatus('Voice input inserted locally.');
    };
    recognition.onerror = () => setStatus('Voice input failed; no backend request was created.');
    recognition.onend = () => {
      if (composerStatus?.textContent === 'Listening…') setStatus('Voice input ended.');
    };
    recognition.start();
  }

  function send() {
    const text = prompt?.value.trim() || '';
    if (!text) return;
    prompt.value = '';
    resize();
    document.dispatchEvent(new CustomEvent('rie:composer-send', { detail: { text, mode: api.state.mode } }));
  }

  function queue() {
    if (api.state.mode !== 'research' || queueButton?.disabled) return;
    const text = prompt?.value.trim() || '';
    if (!text) return;
    prompt.value = '';
    resize();
    document.dispatchEvent(new CustomEvent('rie:composer-queue', { detail: { text, mode: api.state.mode } }));
  }

  document.addEventListener('click', (event) => {
    const mode = event.target.closest('[data-mode]');
    if (mode) { event.preventDefault(); selectMode(mode.dataset.mode); return; }
    if (event.target.closest('[data-action="voice"]')) { event.preventDefault(); handleVoice(); return; }
    if (event.target.closest('[data-action="send"]')) { event.preventDefault(); send(); return; }
    if (event.target.closest('[data-action="queue"]')) { event.preventDefault(); queue(); return; }
  }, true);

  prompt?.addEventListener('input', resize);
  prompt?.addEventListener('keydown', (event) => {
    if (event.isComposing) return;
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (event.ctrlKey || event.metaKey) queue();
      else send();
    }
  });

  window.addEventListener('keydown', (event) => {
    if (!(event.ctrlKey || event.metaKey)) return;
    if (event.key.toLowerCase() === 'k') {
      event.preventDefault();
      api.newChat();
      api.chatView?.render();
      prompt?.focus();
    }
  });

  api.composer = Object.freeze({ selectMode, renderMode, setStatus, resize });
  renderMode();
  resize();
})();
