(() => {
  'use strict';

  type UiState =
    | 'NEW_CHAT' | 'SUBMITTING' | 'QUEUED' | 'RUNNING' | 'STREAMING'
    | 'COMPLETE' | 'PARTIAL' | 'CANCELLED' | 'FAILED' | 'BLOCKED' | 'REJECTED' | 'UNAVAILABLE'
    | 'UNKNOWN' | 'RECONNECTING' | 'RESUMED' | 'REPLAYED' | 'AUTH_EXPIRED';

  const STATES: readonly UiState[] = [
    'NEW_CHAT','SUBMITTING','QUEUED','RUNNING','STREAMING','COMPLETE','PARTIAL',
    'CANCELLED','FAILED','BLOCKED','REJECTED','UNAVAILABLE','UNKNOWN','RECONNECTING','RESUMED','REPLAYED','AUTH_EXPIRED',
  ];

  const BACKEND_TO_UI: Readonly<Record<string, UiState>> = Object.freeze({
    new:'NEW_CHAT',new_chat:'NEW_CHAT',submitting:'SUBMITTING',submitted:'QUEUED',queued:'QUEUED',
    running:'RUNNING',streaming:'STREAMING',complete:'COMPLETE',completed:'COMPLETE',success:'COMPLETE',
    succeeded:'COMPLETE',partial:'PARTIAL',cancelled:'CANCELLED',failed:'FAILED',blocked:'BLOCKED',rejected:'REJECTED',unavailable:'UNAVAILABLE',
    unknown:'UNKNOWN',reconnecting:'RECONNECTING',resumed:'RESUMED',replayed:'REPLAYED',auth_expired:'AUTH_EXPIRED',
    unauthorized:'AUTH_EXPIRED',forbidden:'AUTH_EXPIRED',paused:'RECONNECTING',
  });

  const ALLOWED: Record<UiState, ReadonlySet<UiState>> = {
    CANCELLED:new Set(['REPLAYED','NEW_CHAT','CANCELLED']),
    FAILED:new Set(['REPLAYED','NEW_CHAT','FAILED']),
    NEW_CHAT:new Set(['SUBMITTING','QUEUED','NEW_CHAT']),
    SUBMITTING:new Set(['QUEUED','RUNNING','STREAMING','COMPLETE','PARTIAL','CANCELLED','FAILED','BLOCKED','REJECTED','UNAVAILABLE','UNKNOWN','AUTH_EXPIRED']),
    QUEUED:new Set(['RUNNING','STREAMING','COMPLETE','PARTIAL','CANCELLED','FAILED','BLOCKED','REJECTED','UNAVAILABLE','UNKNOWN','RECONNECTING','AUTH_EXPIRED']),
    RUNNING:new Set(['STREAMING','COMPLETE','PARTIAL','CANCELLED','FAILED','BLOCKED','REJECTED','UNAVAILABLE','UNKNOWN','RECONNECTING','AUTH_EXPIRED']),
    STREAMING:new Set(['COMPLETE','PARTIAL','CANCELLED','FAILED','BLOCKED','REJECTED','UNAVAILABLE','UNKNOWN','RECONNECTING','AUTH_EXPIRED']),
    COMPLETE:new Set(['REPLAYED','NEW_CHAT','COMPLETE']),
    PARTIAL:new Set(['RECONNECTING','RESUMED','REPLAYED','COMPLETE','PARTIAL','UNKNOWN','UNAVAILABLE']),
    BLOCKED:new Set(['RECONNECTING','RESUMED','NEW_CHAT','BLOCKED']),
    REJECTED:new Set(['SUBMITTING','NEW_CHAT','REJECTED']),
    UNAVAILABLE:new Set(['RECONNECTING','RESUMED','NEW_CHAT','UNKNOWN','UNAVAILABLE']),
    UNKNOWN:new Set(['RECONNECTING','RESUMED','REPLAYED','RUNNING','STREAMING','COMPLETE','PARTIAL','BLOCKED','REJECTED','UNAVAILABLE','AUTH_EXPIRED','UNKNOWN']),
    RECONNECTING:new Set(['RESUMED','REPLAYED','RUNNING','STREAMING','COMPLETE','PARTIAL','UNAVAILABLE','UNKNOWN','AUTH_EXPIRED','RECONNECTING']),
    RESUMED:new Set(['RUNNING','STREAMING','COMPLETE','PARTIAL','UNKNOWN','RECONNECTING','RESUMED']),
    REPLAYED:new Set(['RUNNING','STREAMING','COMPLETE','PARTIAL','UNKNOWN','RECONNECTING','REPLAYED']),
    AUTH_EXPIRED:new Set(['SUBMITTING','RECONNECTING','NEW_CHAT','AUTH_EXPIRED']),
  };

  interface BackendStateEnvelope {
    ui_state?: unknown;
    state?: unknown;
    status?: unknown;
    run?: { ui_state?: unknown; state?: unknown; status?: unknown };
  }

  function normalizeKey(value: unknown): string {
    return String(value ?? '').trim().toLowerCase().replace(/[-\s]+/g, '_');
  }
  function normalize(value: unknown): UiState | null {
    return BACKEND_TO_UI[normalizeKey(value)] ?? null;
  }
  function canTransition(current: UiState, next: UiState): boolean {
    return STATES.includes(current) && STATES.includes(next) && (current === next || ALLOWED[current].has(next));
  }
  function advance(current: UiState | null | undefined, backendValue: unknown): UiState {
    const next = normalize(backendValue);
    if (!next) return 'UNKNOWN';
    if (!current) return next;
    return canTransition(current, next) ? next : 'UNKNOWN';
  }
  function fromBackend(body: unknown): UiState {
    const source = body && typeof body === 'object' ? body as BackendStateEnvelope : {};
    const raw = source.ui_state ?? source.state ?? source.status ?? source.run?.ui_state ?? source.run?.state ?? source.run?.status;
    return normalize(raw) ?? 'UNKNOWN';
  }

  const target = window;
  const registry = target.RIEFrontend ?? {};
  registry.lifecycleStateMachine = Object.freeze({ STATES, normalize, canTransition, advance, fromBackend });
  target.RIEFrontend = registry;
})();