(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api) throw new Error('frontend_state.js must load before composer.js');

  const prompt = document.getElementById('prompt');
  const modeButtons = [...document.querySelectorAll('.mode')];
  const attachmentList = document.getElementById('attachment-list');
  const composerStatus = document.getElementById('composer-status');
  const workspace = document.getElementById('workspace');

  function setStatus(text, tone = '') {
    if (!composerStatus) return;
    composerStatus.textContent = text;
    composerStatus.dataset.tone = tone;
  }

  function renderMode() {
    modeButtons.forEach((button) => {
      const active = button.dataset.mode === api.state.mode;
      button.classList.toggle('active', active);
      button.setAttribute('aria-selected', active ? 'true' : 'false');
      button.tabIndex = active ? 0 : -1;
    });
    if (prompt) {
      prompt.placeholder = api.state.mode === 'research' ? 'What should the engine research and verify?' : 'Ask Heroic AI…';
      prompt.setAttribute('aria-label', api.state.mode === 'research' ? 'Research question' : 'Message');
    }
  }

  function selectMode(mode) {
    if (!['chat', 'research'].includes(mode)) return;
    api.state.mode = mode;
    renderMode();
    if (mode === 'research') workspace?.classList.add('open');
    setStatus(mode === 'research' ? 'Research uses the canonical backend lifecycle and evidence contract.' : 'Chat uses the authenticated Heroic AI backend and canonical Operations routing.');
    document.dispatchEvent(new CustomEvent('rie:mode-changed', { detail: { mode } }));
  }

  function resize() {
    if (!prompt) return;
    prompt.style.height = 'auto';
    prompt.style.height = `${Math.min(prompt.scrollHeight, 150)}px`;
  }

  function addAttachmentChip(name) {
    if (!attachmentList) return;
    const chip = document.createElement('span');
    chip.className = 'attachment-chip';
    chip.dataset.attachment = name;
    chip.textContent = name;
    attachmentList.append(chip);
  }

  function handleAttachments() {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '*/*';
    input.addEventListener('change', () => {
      const files = [...(input.files || [])];
      if (!files.length) return;
      if (api.state.mode !== 'research') {
        setStatus('Attachments are selected locally; this chat contract does not upload file contents yet.');
      } else {
        setStatus('Attachments are selected locally; the public research contract does not upload file contents yet.');
      }
      files.forEach((file) => addAttachmentChip(file.name));
    }, { once: true });
    input.click();
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
    const text = prompt?.value.trim() || '';
    if (!text) return;
    prompt.value = '';
    resize();
    document.dispatchEvent(new CustomEvent('rie:composer-queue', { detail: { text, mode: api.state.mode } }));
  }

  document.addEventListener('click', (event) => {
    const mode = event.target.closest('[data-mode]');
    if (mode) { event.preventDefault(); selectMode(mode.dataset.mode); return; }
    if (event.target.closest('[data-action="attachments"]')) { event.preventDefault(); handleAttachments(); return; }
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
