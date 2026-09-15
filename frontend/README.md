# Heroic AI frontend

This frontend is a production-oriented UI shell with the real Foundation research lifecycle plus a complete browser-local personal workspace.

## Canonical frontend ownership

The frontend has one owner per behavior:

- `frontend_state.js` — shared UI state facade and storage/auth helpers.
- `chat_store.js` — browser-local chat/project/saved persistence and export/import validation.
- `chat_view.js` — sidebar, conversation, Projects, Saved, Settings rendering.
- `workspace_view.js` — research-run status, answer, evidence, metadata, capability and metric rendering.
- `composer.js` — Chat/Research mode, input, attachments, voice and composer events.
- `lifecycle_controller.js` — **sole Research transport/lifecycle authority**: submission, Idempotency-Key, polling, reconnect, active-run state and durable FIFO queue data.
- `lifecycle_queue_controls.js` — queue presentation/open/clear/remove controls only; it does not own queue state.
- `app.js` — bootstrap/orchestration only. It must not implement a second Research transport, polling loop, queue, or active-run state.
- `ui_guards.js` — compatibility repair only.
- `session_bridge.js` — short-lived browser-tab session credential bridge.
- `feedback_bridge.js` / `feedback_contract.js` — feedback UI boundary.

## Real backend integration

Heroic AI uses the existing Foundation Worker contract:

- `GET /readiness` — readiness check.
- `POST /api/v1/research` — submits a strict-$0 research request.
- `GET /api/v1/research/{run_id}` — reads persisted run/source observations.

Research results are never fabricated by the UI. The workspace displays backend run identifiers and returned observation/evidence records. Unknown, blocked, partial, failed and timeout states remain distinct from successful completion.

## Browser authentication boundary

Production research requests remain protected by the Worker authorization contract. The frontend never ships a long-lived infrastructure token in source code, localStorage, or the public bundle.

An optional bearer token can be entered from Settings for a controlled personal/browser session. It is stored in **sessionStorage only**, not localStorage, and is scoped to the current browser tab/session. This is a compatibility bridge, not an identity provider, and should only be used with an appropriately scoped/short-lived session credential.

The production completion item remains a user-scoped authentication/session bridge backed by a real trust source (for example an authenticated same-origin gateway or identity provider). The Worker authorization contract is not weakened to make the browser public.

## Local personal workspace

- Browser-local chat history and search.
- Browser-local Projects with chat assignment, rename and delete.
- Browser-local Saved messages with ownership repair.
- Durable browser-local FIFO Research follow-up queue.
- Local file selection metadata; files are **not uploaded** until an authenticated ingestion API exists.
- Browser speech recognition when supported.
- Versioned export/import of browser-local chats, projects, and saved items.
- Settings with backend status and session-only token handling.
- Mobile sidebar/workspace/queue surfaces and reduced-motion/keyboard-focus support.

## Non-goals until backend contracts exist

The frontend does not pretend to provide:

- conversational LLM token streaming;
- server-side chat/project persistence;
- authenticated file upload/ingestion;
- server-side voice transcription;
- an identity provider or login system.

Those require backend/session contracts rather than UI-only behavior.
