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

  async function consumeChatStream(response, onEvent) {
    if (!response.body) throw new Error('Heroic AI stream is unavailable in this browser');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    const dispatch = (block) => {
      const lines = block.split(/\r?\n/);
      let eventName = 'message';
      let data = '';
      for (const line of lines) {
        if (line.startsWith('event:')) eventName = line.slice(6).trim();
        else if (line.startsWith('data:')) data += `${line.slice(5).trim()}\n`;
      }
      if (!data) return;
      const payload = JSON.parse(data.trim());
      onEvent(eventName, payload);
    };
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split(/\r?\n\r?\n/);
      buffer = blocks.pop() || '';
      blocks.filter(Boolean).forEach(dispatch);
    }
    buffer += decoder.decode();
    if (buffer.trim()) dispatch(buffer);
  }

  async function submitChat(text, chatId = api.state.activeChatId) {
    if (!api.API_BASE) throw new Error('Heroic AI API base is not configured');
    if (!chatId) throw new Error('No active Heroic AI chat is available');
    const requestId = api.uuid();
    const userMessage = api.addMessage('user', text, { request_id: requestId, pending: true }, chatId);
    const assistantMessage = api.addMessage('assistant', '', { request_id: requestId, pending: true, streaming: true }, chatId);
    api.state.submitting = true;
    api.chatView.render();
    try {
      const response = await fetch(api.apiUrl('/api/v1/chat/stream'), {
        method: 'POST',
        headers: { ...api.authHeaders(true), Accept: 'text/event-stream', 'Idempotency-Key': requestId },
        body: JSON.stringify({
          chat_id: chatId,
          request_id: requestId,
          message: text,
          mode: 'chat',
          strict_zero_cost_only: true,
          history: conversationHistory(chatId),
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || `Heroic AI chat request failed (${response.status})`);
      }
      let answer = '';
      let responseId = null;
      let terminal = false;
      await consumeChatStream(response, (event, payload) => {
        if (event === 'start') {
          responseId = payload.response_id || null;
          api.updateMessage(assistantMessage.id, { meta: { ...assistantMessage.meta, response_id: responseId, status: 'streaming', pending: true, streaming: true } });
        } else if (event === 'delta') {
          answer += String(payload.text || '');
          api.updateMessage(assistantMessage.id, { text: answer, meta: { ...assistantMessage.meta, response_id: responseId, status: 'streaming', pending: true, streaming: true } });
          api.chatView.renderConversation();
        } else if (event === 'done') {
          terminal = true;
          responseId = payload.response_id || responseId;
          api.updateMessage(assistantMessage.id, { text: answer, meta: { ...assistantMessage.meta, response_id: responseId, status: payload.status || 'completed', pending: false, streaming: false } });
          api.updateMessage(userMessage.id, { meta: { ...(userMessage.meta || {}), pending: false } });
        }
      });
      if (!terminal) throw new Error('Heroic AI stream ended without a completion event');
      const body = { ok: true, request_id: requestId, chat_id: chatId, response: { response_id: responseId, status: 'completed', text: answer } };
      document.dispatchEvent(new CustomEvent('rie:chat-response', { detail: { chatId, requestId, body } }));
      return body;
    } catch (error) {
      api.updateMessage(userMessage.id, { meta: { ...(userMessage.meta || {}), pending: false, error: true } });
      api.updateMessage(assistantMessage.id, { meta: { ...(assistantMessage.meta || {}), pending: false, streaming: false, error: true }, text: answerOrFallback(assistantMessage.text, error) });
      throw error;
    } finally {
      api.state.submitting = false;
      api.chatView.render();
    }
  }

  function answerOrFallback(text, error) {
    return text || `Heroic AI could not complete this message: ${error.message || error}`;
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
    void submitChat(String(text).trim()).catch(() => {});
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
