(() => {
  'use strict';

  // Backend state is authoritative. Unknown/missing/illegal state transitions fail closed to UNKNOWN.
  const STATES = Object.freeze([
    'NEW_CHAT',
    'SUBMITTING',
    'QUEUED',
    'RUNNING',
    'STREAMING',
    'COMPLETE',
    'PARTIAL',
    'BLOCKED',
    'REJECTED',
    'UNAVAILABLE',
    'UNKNOWN',
    'RECONNECTING',
    'RESUMED',
    'REPLAYED',
    'AUTH_EXPIRED',
  ]);

  const BACKEND_TO_UI = Object.freeze({
    new: 'NEW_CHAT',
    new_chat: 'NEW_CHAT',
    submitting: 'SUBMITTING',
    submitted: 'QUEUED',
    queued: 'QUEUED',
    running: 'RUNNING',
    streaming: 'STREAMING',
    complete: 'COMPLETE',
    completed: 'COMPLETE',
    success: 'COMPLETE',
    succeeded: 'COMPLETE',
    partial: 'PARTIAL',
    blocked: 'BLOCKED',
    rejected: 'REJECTED',
    unavailable: 'UNAVAILABLE',
    unknown: 'UNKNOWN',
    reconnecting: 'RECONNECTING',
    resumed: 'RESUMED',
    replayed: 'REPLAYED',
    auth_expired: 'AUTH_EXPIRED',
    unauthorized: 'AUTH_EXPIRED',
    forbidden: 'AUTH_EXPIRED',
    paused: 'RECONNECTING',
  });

  const ALLOWED = Object.freeze({
    NEW_CHAT: new Set(['SUBMITTING', 'QUEUED', 'NEW_CHAT']),
    SUBMITTING: new Set(['QUEUED', 'RUNNING', 'STREAMING', 'COMPLETE', 'PARTIAL', 'BLOCKED', 'REJECTED', 'UNAVAILABLE', 'UNKNOWN', 'AUTH_EXPIRED']),
    QUEUED: new Set(['RUNNING', 'STREAMING', 'COMPLETE', 'PARTIAL', 'BLOCKED', 'REJECTED', 'UNAVAILABLE', 'UNKNOWN', 'RECONNECTING', 'AUTH_EXPIRED']),
    RUNNING: new Set(['STREAMING', 'COMPLETE', 'PARTIAL', 'BLOCKED', 'REJECTED', 'UNAVAILABLE', 'UNKNOWN', 'RECONNECTING', 'AUTH_EXPIRED']),
    STREAMING: new Set(['COMPLETE', 'PARTIAL', 'BLOCKED', 'REJECTED', 'UNAVAILABLE', 'UNKNOWN', 'RECONNECTING', 'AUTH_EXPIRED']),
    COMPLETE: new Set(['REPLAYED', 'NEW_CHAT', 'COMPLETE']),
    PARTIAL: new Set(['RECONNECTING', 'RESUMED', 'REPLAYED', 'COMPLETE', 'PARTIAL', 'UNKNOWN', 'UNAVAILABLE']),
    BLOCKED: new Set(['RECONNECTING', 'RESUMED', 'NEW_CHAT', 'BLOCKED']),
    REJECTED: new Set(['SUBMITTING', 'NEW_CHAT', 'REJECTED']),
    UNAVAILABLE: new Set(['RECONNECTING', 'RESUMED', 'NEW_CHAT', 'UNKNOWN', 'UNAVAILABLE']),
    UNKNOWN: new Set(['RECONNECTING', 'RESUMED', 'REPLAYED', 'RUNNING', 'STREAMING', 'COMPLETE', 'PARTIAL', 'BLOCKED', 'REJECTED', 'UNAVAILABLE', 'AUTH_EXPIRED', 'UNKNOWN']),
    RECONNECTING: new Set(['RESUMED', 'REPLAYED', 'RUNNING', 'STREAMING', 'COMPLETE', 'PARTIAL', 'UNAVAILABLE', 'UNKNOWN', 'AUTH_EXPIRED', 'RECONNECTING']),
    RESUMED: new Set(['RUNNING', 'STREAMING', 'COMPLETE', 'PARTIAL', 'UNKNOWN', 'RECONNECTING', 'RESUMED']),
    REPLAYED: new Set(['RUNNING', 'STREAMING', 'COMPLETE', 'PARTIAL', 'UNKNOWN', 'RECONNECTING', 'REPLAYED']),
    AUTH_EXPIRED: new Set(['SUBMITTING', 'RECONNECTING', 'NEW_CHAT', 'AUTH_EXPIRED']),
  });

  const normalize = (value) => {
    const key = String(value || '').trim().toLowerCase().replace(/[-\s]+/g, '_');
    return BACKEND_TO_UI[key] || null;
  };

  const canTransition = (current, next) => {
    if (!STATES.includes(current) || !STATES.includes(next)) return false;
    return current === next || ALLOWED[current].has(next);
  };

  const advance = (current, backendValue) => {
    const next = normalize(backendValue);
    if (!next) return 'UNKNOWN';
    if (!current) return next;
    return canTransition(current, next) ? next : 'UNKNOWN';
  };

  const fromBackend = (body) => {
    const source = body && typeof body === 'object' ? body : {};
    const raw = source.ui_state || source.state || source.status || source.run?.ui_state || source.run?.state || source.run?.status;
    return normalize(raw) || 'UNKNOWN';
  };

  window.RIEFrontend = window.RIEFrontend || {};
  window.RIEFrontend.lifecycleStateMachine = Object.freeze({
    STATES,
    normalize,
    canTransition,
    advance,
    fromBackend,
  });
})();
