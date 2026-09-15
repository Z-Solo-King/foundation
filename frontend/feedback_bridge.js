/*
 * Purpose: add lightweight feedback controls without changing the existing chat renderer.
 * Ownership: public UI interaction layer; stored locally until an authorized backend contract consumes it.
 * Raw chat text is never sent by this bridge.
 */
(() => {
  'use strict';

  const KEY = 'rie.frontend.feedback.v1';
  const read = () => {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch { return []; }
  };
  const write = (items) => localStorage.setItem(KEY, JSON.stringify(items.slice(-256)));

  function addControls(message) {
    if (message.dataset.feedbackReady === 'true') return;
    if (!message.classList.contains('assistant-message')) return;
    const actions = message.querySelector('.message-actions');
    if (!actions) return;
    const positive = document.createElement('button');
    positive.className = 'secondary';
    positive.type = 'button';
    positive.textContent = 'Helpful';
    positive.dataset.feedback = 'task_success';
    const negative = document.createElement('button');
    negative.className = 'secondary';
    negative.type = 'button';
    negative.textContent = 'Not helpful';
    negative.dataset.feedback = 'task_failure';
    actions.append(positive, negative);
    message.dataset.feedbackReady = 'true';
  }

  function observe() {
    document.querySelectorAll('.message.assistant-message').forEach(addControls);
  }

  document.addEventListener('click', (event) => {
    const control = event.target.closest('[data-feedback]');
    if (!control || !window.RIEFeedback) return;
    const message = control.closest('[data-message-id]');
    if (!message) return;
    const runButton = message.querySelector('[data-open-run]');
    const item = window.RIEFeedback.createFeedback({
      messageId: message.dataset.messageId,
      runId: runButton?.dataset.openRun || null,
      kind: control.dataset.feedback,
    });
    const records = read();
    records.push(item);
    write(records);
    control.textContent = control.dataset.feedback === 'task_success' ? 'Marked helpful' : 'Marked not helpful';
    control.disabled = true;
  });

  new MutationObserver(observe).observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener('DOMContentLoaded', observe);
})();
