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
    link.download = `heroic-ai-local-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
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

  function conversationHistory(chatId) {
    const chat = api.state.chats.find((item) => item.id === chatId);
    if (!chat) return [];
    return (chat.messages || [])
      .filter((message) => (message.role === 'user' || message.role === 'assistant') && message.text)
      .slice(-20)
      .map((message) => ({ role: message.role, text: String(message.text).slice(0, 12000) }));
  }

  async function submitChat(text, chatId = api.state.activeChatId) {
    if (!api.API_BASE) throw new Error('Heroic AI API base is not configured');
    if (!chatId) throw new Error('No active Heroic AI chat is available');
    const requestId = api.uuid();
    const userMessage = api.addMessage('user', text, { request_id: requestId, pending: true }, chatId);
    api.state.submitting = true;
    api.chatView.render();
    try {
      const response = await fetch(api.apiUrl('/api/v1/chat'), {
        method: 'POST',
        headers: { ...api.authHeaders(true), 'Idempotency-Key': requestId },
        body: JSON.stringify({
          chat_id: chatId,
          request_id: requestId,
          message: text,
          mode: 'chat',
          strict_zero_cost_only: true,
          history: conversationHistory(chatId),
        }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || !body.ok) throw new Error(body.error || `Heroic AI chat request failed (${response.status})`);
      const answer = body.response?.text || body.answer;
      if (!answer) throw new Error('Heroic AI returned no response text');
      api.updateMessage(userMessage.id, { meta: { ...(userMessage.meta || {}), pending: false } });
      api.addMessage('assistant', answer, {
        request_id: requestId,
        response_id: body.response?.response_id || body.response_id || null,
        status: body.response?.status || body.status || 'completed',
        operation: body.response?.operation || null,
        generation_status: body.response?.generation_status || null,
        provider: body.response?.provider || null,
        sources: body.response?.sources || body.sources || [],
      }, chatId);
      document.dispatchEvent(new CustomEvent('rie:chat-response', { detail: { chatId, requestId, body } }));
      return body;
    } catch (error) {
      api.updateMessage(userMessage.id, { meta: { ...(userMessage.meta || {}), pending: false, error: true } });
      throw error;
    } finally {
      api.state.submitting = false;
      api.chatView.render();
    }
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
      if (prompt) { prompt.value = start.dataset.starter || ''; api.composer.selectMode(start.dataset.starter?.toLowerCase().includes('research') ? 'research' : 'chat'); api.composer.resize(); prompt.focus(); }
    }
  });

  document.addEventListener('rie:composer-send', (event) => {
    const { text, mode } = event.detail || {};
    if (!text || mode === 'research') return;
    void submitChat(String(text).trim()).catch((error) => {
      api.addMessage('assistant', `Heroic AI could not complete this message: ${error.message || error}`, { error: true }, api.state.activeChatId);
      api.chatView.render();
    });
  });

  document.addEventListener('rie:composer-queue', (event) => {
    const { text, mode } = event.detail || {};
    if (!text || mode === 'research') return;
    api.addMessage('assistant', 'Chat messages use the canonical Heroic AI conversational lifecycle; Queue is reserved for Research capability follow-ups.', { informational: true }, api.state.activeChatId);
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
  api.submitChat = submitChat;

  api.load();
  api.chatView.render();
  void checkBackend();
  document.getElementById('prompt')?.focus();
})();
