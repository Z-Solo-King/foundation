(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api?.chatStore || !api?.chatView || !api?.composer) throw new Error('Frontend modules must load before app.js');

  const connectionPill = document.getElementById('connection-pill');
  const workspace = document.getElementById('workspace');
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'application/json,.json';
  fileInput.hidden = true;
  document.body.append(fileInput);

  async function checkBackend() {
    if (!api.API_BASE) {
      api.state.backendOk = false;
      api.state.backendText = 'API not configured';
    } else {
      try {
        const response = await fetch(api.apiUrl('/readiness'), { headers: api.authHeaders() });
        api.state.backendOk = response.ok;
        api.state.backendText = response.ok ? 'Backend reachable' : `Backend ${response.status}`;
      } catch {
        api.state.backendOk = false;
        api.state.backendText = 'Backend unavailable';
      }
    }
    if (connectionPill) {
      connectionPill.textContent = api.state.backendText;
      connectionPill.classList.toggle('ok', api.state.backendOk);
    }
    api.chatView.render();
    return api.state.backendOk;
  }

  function exportLocalData() {
    const blob = new Blob([api.chatStore.exportData()], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `research-intelligence-local-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function importLocalData() {
    fileInput.value = '';
    fileInput.onchange = async () => {
      const file = fileInput.files?.[0];
      if (!file) return;
      try {
        const text = await file.text();
        api.chatStore.importData(text);
        api.chatView.render();
        api.chatView.toast('Local data imported.');
      } catch (error) {
        api.chatView.toast(`Import rejected: ${error.message || error}`);
      }
    };
    fileInput.click();
  }

  function openWorkspace() { workspace?.classList.add('open'); }
  function closeWorkspace() { workspace?.classList.remove('open'); }

  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-action="toggle-workspace"]')) { event.preventDefault(); openWorkspace(); return; }
    if (event.target.closest('[data-action="close-workspace"]')) { event.preventDefault(); closeWorkspace(); return; }
    const start = event.target.closest('[data-starter]');
    if (start) {
      event.preventDefault();
      const prompt = document.getElementById('prompt');
      if (prompt) { prompt.value = start.dataset.starter || ''; api.composer.selectMode('research'); api.composer.resize(); prompt.focus(); }
    }
  });

  document.addEventListener('rie:composer-send', (event) => {
    const { text, mode } = event.detail || {};
    if (!text || mode === 'research') return;
    api.addMessage('user', text);
    api.addMessage('assistant', 'Chat mode is browser-local in this public frontend. Switch to Research mode to submit the real backend research contract.');
    api.chatView.render();
  });

  document.addEventListener('rie:composer-queue', (event) => {
    const { text, mode } = event.detail || {};
    if (!text || mode === 'research') return;
    api.addMessage('user', text);
    api.addMessage('assistant', 'Queueing is currently reserved for Research mode so queued work always targets the canonical backend lifecycle.');
    api.chatView.render();
  });

  document.addEventListener('rie:mode-changed', (event) => {
    if (event.detail?.mode === 'research') openWorkspace();
  });

  api.checkBackend = checkBackend;
  api.exportLocalData = exportLocalData;
  api.importLocalData = importLocalData;
  api.openWorkspace = openWorkspace;
  api.closeWorkspace = closeWorkspace;

  api.load();
  api.chatView.render();
  void checkBackend();
  document.getElementById('prompt')?.focus();
})();
