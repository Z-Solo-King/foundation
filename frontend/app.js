(() => {
  'use strict';

  const api = window.RIEFrontend;
  if (!api?.chatStore || !api?.chatView || !api?.composer) throw new Error('Frontend modules must load before app.js');

  const connectionPill = document.getElementById('connection-pill');
  const workspace = document.getElementById('workspace');
  const composerHint = document.querySelector('.composer-hint');
  let activeChatAbortController = null;
  let activeChatRequestId = null;
  const cancelButton = document.createElement('button');
  cancelButton.type = 'button';
  cancelButton.className = 'secondary cancel-chat-button';
  cancelButton.textContent = 'Cancel';
  cancelButton.hidden = true;
  cancelButton.setAttribute('aria-label', 'Cancel active chat stream');
  if (composerHint) composerHint.prepend(cancelButton);
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'application/json,.json';
  fileInput.hidden = true;
  document.body.append(fileInput);

  const guestTestButton = document.createElement('button');
  guestTestButton.type = 'button';
  guestTestButton.className = 'secondary guest-test-button';
  guestTestButton.textContent = api.state.guestTestMode ? 'Exit guest test mode' : 'Guest test mode';
  guestTestButton.setAttribute('aria-pressed', String(Boolean(api.state.guestTestMode)));
  if (composerHint) composerHint.prepend(guestTestButton);

  function syncGuestTestButton() {
    guestTestButton.textContent = api.state.guestTestMode ? 'Exit guest test mode' : 'Guest test mode';
    guestTestButton.setAttribute('aria-pressed', String(Boolean(api.state.guestTestMode)));
    guestTestButton.title = api.state.guestTestMode
      ? 'Return to the authenticated Heroic AI backend'
      : 'Run a local deterministic chat lifecycle without credentials or network calls';
  }

  async function checkBackend() {
    if (api.state.guestTestMode) {
      api.state.backendOk = false;
      api.state.backendText = 'Guest test mode · local only';
    } else if (!api.API_BASE) {
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
    syncGuestTestButton();
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

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function submitGuestTestChat(text, chatId) {
    const normalizedText = String(text || '').trim();
    if (!normalizedText) throw new Error('Message is required');
    if (normalizedText.length > 12_000) throw new Error('Message exceeds the 12000 character limit');
    if (!chatId) throw new Error('No active Heroic AI chat is available');

    const requestId = api.uuid();
    const responseId = `guest-test-${requestId}`;
    const userMessage = api.addMessage('user', normalizedText, { request_id: requestId, guest_test: true, pending: true }, chatId);
    const assistantMessage = api.addMessage('assistant', '', { request_id: requestId, response_id: responseId, guest_test: true, pending: true, streaming: true }, chatId);
    api.state.submitting = true;
    api.chatView.render();

    try {
      api.updateMessage(assistantMessage.id, {
        meta: {
          ...assistantMessage.meta,
          status: 'streaming',
          pending: true,
          streaming: true,
          guest_test: true,
        },
      });
      const deltas = [
        'Guest test mode is active. ',
        'This is a local deterministic simulation of the authenticated chat lifecycle; no credentials, private binding, model provider, or remote request are used. ',
        `Echo: ${normalizedText.slice(0, 1200)}`,
      ];
      let answer = '';
      for (const delta of deltas) {
        await sleep(15);
        answer += delta;
        api.updateMessage(assistantMessage.id, {
          text: answer,
          meta: {
            ...assistantMessage.meta,
            response_id: responseId,
            status: 'streaming',
            pending: true,
            streaming: true,
            guest_test: true,
          },
        });
        api.chatView.renderConversation();
      }
      api.updateMessage(assistantMessage.id, {
        text: answer,
        meta: {
          ...assistantMessage.meta,
          response_id: responseId,
          status: 'completed',
          pending: false,
          streaming: false,
          guest_test: true,
          result_state: 'TEST_ONLY',
        },
      });
      api.updateMessage(userMessage.id, { meta: { ...(userMessage.meta || {}), pending: false, guest_test: true } });
      const body = {
        ok: true,
        request_id: requestId,
        chat_id: chatId,
        response: {
          response_id: responseId,
          status: 'completed',
          result_state: 'TEST_ONLY',
          generation_status: 'deterministic_test',
          guest_test: true,
          text: answer,
          sources: [],
        },
      };
      document.dispatchEvent(new CustomEvent('rie:chat-response', { detail: { chatId, requestId, body } }));
      return body;
    } finally {
      api.state.submitting = false;
      api.chatView.render();
    }
  }

  async function consumeChatStream(response, onEvent, signal) {
    if (!response.body) throw new Error('Heroic AI stream is unavailable in this browser');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    const onAbort = () => { void reader.cancel(); };
    if (signal) {
      if (signal.aborted) throw new DOMException('Chat stream was cancelled', 'AbortError');
      signal.addEventListener('abort', onAbort, { once: true });
    }
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
    if (signal) signal.removeEventListener('abort', onAbort);
  }

  function cancelActiveChat() {
    if (activeChatAbortController && !activeChatAbortController.signal.aborted) {
      activeChatAbortController.abort();
      return true;
    }
    return false;
  }

  async function submitChat(text, chatId = api.state.activeChatId) {
    if (!chatId) throw new Error('No active Heroic AI chat is available');
    if (api.state.guestTestMode) return submitGuestTestChat(text, chatId);
    if (!api.API_BASE) throw new Error('Heroic AI API base is not configured');
    const requestId = api.uuid();
    const abortController = new AbortController();
    activeChatAbortController = abortController;
    activeChatRequestId = requestId;
    cancelButton.hidden = false;
    const userMessage = api.addMessage('user', text, { request_id: requestId, pending: true }, chatId);
    const assistantMessage = api.addMessage('assistant', '', { request_id: requestId, pending: true, streaming: true }, chatId);
    api.state.submitting = true;
    api.chatView.render();
    try {
      const response = await fetch(api.apiUrl('/api/v1/chat/stream'), {
        method: 'POST',
        signal: abortController.signal,
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
      }, abortController.signal);
      if (abortController.signal.aborted) throw new DOMException('Chat stream was cancelled', 'AbortError');
      if (!terminal) throw new Error('Heroic AI stream ended without a completion event');
      const body = { ok: true, request_id: requestId, chat_id: chatId, response: { response_id: responseId, status: 'completed', text: answer } };
      document.dispatchEvent(new CustomEvent('rie:chat-response', { detail: { chatId, requestId, body } }));
      return body;
    } catch (error) {
      if (error?.name === 'AbortError' || abortController.signal.aborted) {
        api.updateMessage(userMessage.id, {
          meta: { ...(userMessage.meta || {}), pending: false, cancelled: true },
        });
        api.updateMessage(assistantMessage.id, {
          meta: {
            ...(assistantMessage.meta || {}),
            pending: false,
            streaming: false,
            cancelled: true,
            backend_state: 'UNKNOWN',
          },
          text: answer || 'Chat streaming was cancelled in the browser. Backend completion state is unknown; reconnect or retry to observe it.',
        });
        document.dispatchEvent(new CustomEvent('rie:chat-stream-cancelled', {
          detail: { chatId, requestId, responseId, partial: Boolean(answer) },
        }));
        return {
          ok: false,
          request_id: requestId,
          chat_id: chatId,
          response: {
            response_id: responseId,
            status: 'cancelled',
            result_state: answer ? 'PARTIAL' : 'UNKNOWN',
            client_cancelled: true,
            backend_state: 'UNKNOWN',
            text: answer,
          },
        };
      }
      api.updateMessage(userMessage.id, { meta: { ...(userMessage.meta || {}), pending: false, error: true } });
      api.updateMessage(assistantMessage.id, { meta: { ...(assistantMessage.meta || {}), pending: false, streaming: false, error: true }, text: answerOrFallback(assistantMessage.text, error) });
      throw error;
    } finally {
      activeChatAbortController = null;
      activeChatRequestId = null;
      cancelButton.hidden = true;
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
    if (event.target.closest('.cancel-chat-button')) {
      event.preventDefault();
      cancelActiveChat();
      return;
    }
    if (event.target.closest('.guest-test-button')) {
      event.preventDefault();
      if (api.state.guestTestMode) api.disableGuestTestMode();
      else api.enableGuestTestMode();
      syncGuestTestButton();
      void checkBackend();
      api.chatView.toast(api.state.guestTestMode ? 'Guest test mode enabled. No network or credentials are used.' : 'Guest test mode disabled. Authenticated backend mode restored.');
      return;
    }
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
  api.cancelActiveChat = cancelActiveChat;
  api.getActiveChatRequestId = () => activeChatRequestId;
  api.submitGuestTestChat = submitGuestTestChat;

  api.load();
  api.chatView.render();
  syncGuestTestButton();
  void checkBackend();
  document.getElementById('prompt')?.focus();
})();
