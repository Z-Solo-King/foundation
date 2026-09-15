# Research Intelligence frontend

This frontend is a production-oriented UI shell with the real Foundation research lifecycle plus a complete browser-local personal workspace.

## Real backend integration

The UI uses the existing Foundation Worker contract:

- `GET /readiness` — readiness check.
- `POST /api/v1/research` — submits a strict-$0 research request.
- `GET /api/v1/research/{run_id}` — reads persisted run/source observations.

Research results are never fabricated by the UI. The workspace displays backend run identifiers and returned observation records.

## Browser authentication boundary

Production research requests remain protected by the Worker authorization contract. The frontend never ships a long-lived infrastructure token in source code, localStorage, or the public bundle.

An optional **session-memory-only** bearer token can be entered from Settings for a controlled personal/browser session. It is stored only in JavaScript memory, is not written to localStorage, and disappears on reload. This is a compatibility bridge, not an identity provider, and should only be used with an appropriately scoped/short-lived session credential.

The production completion item remains a user-scoped authentication/session bridge backed by a real trust source (for example an authenticated same-origin gateway or identity provider). The Worker authorization contract is not weakened to make the browser public.

## Local personal workspace

- Browser-local chat history and search.
- Browser-local Projects with chat assignment.
- Browser-local Saved messages.
- Local FIFO follow-up queue.
- Local file selection and attachment metadata; files are **not uploaded** until an authenticated ingestion API exists.
- Browser speech recognition when supported.
- Export/import of browser-local chats, projects, and saved items.
- Settings with backend status and session-memory-only token handling.

## Non-goals until backend contracts exist

The frontend does not pretend to provide:

- conversational LLM token streaming;
- server-side chat/project persistence;
- authenticated file upload/ingestion;
- server-side voice transcription;
- an identity provider or login system.

Those require backend/session contracts rather than UI-only behavior.

## Research lifecycle ownership

`lifecycle_controller.js` is the canonical owner of Research-mode transport, polling, reconnect/recovery, durable research queueing, active-run state, and idempotency. `app.js` remains the general UI/bootstrap boundary. `lifecycle_queue_controls.js` owns queue presentation controls and `session_bridge.js` owns the browser session bridge.

Research-mode interactions are intercepted by the canonical lifecycle controller so the runtime has one Research transport/queue/active-run owner. Broader `app.js` decomposition remains tracked under #114.
