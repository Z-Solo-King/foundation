# Research Intelligence frontend

This frontend is a production-oriented UI shell with a real integration for the Foundation research lifecycle and a deliberately local chat fallback.

## Real backend integration

The UI uses the existing Foundation Worker contract:

- `GET /readiness` — readiness check.
- `POST /api/v1/research` — submits a strict-$0 research request.
- `GET /api/v1/research/{run_id}` — reads persisted run/source observations.

Research results are never fabricated by the UI. The workspace displays the backend run identifier and returned observation records.

## Browser boundary

Production research requests require the Worker authorization contract. The frontend must **not** ship a long-lived bearer token in source code, localStorage, or a public bundle. A future deployment/authentication bridge must supply user-scoped authorization without exposing infrastructure secrets.

Until that bridge exists, a browser client may correctly show `Backend unauthorized/unavailable`; this is preferable to weakening the Worker authorization gate.

## Local capabilities

- Chat history is persisted in browser localStorage and is explicitly labeled as local state.
- FIFO follow-up queue is implemented locally.
- File selection is local-only until a file-ingestion API is available.
- Browser speech recognition is used opportunistically when supported; no provider claim is made.
- Research mode uses the actual backend run/readback contract.

## Non-goals until backend contracts exist

The frontend does not pretend to provide conversational token streaming, server-side chat history, persistent Projects/Saved state, authenticated file upload, or server-side voice transcription when those APIs are not currently exposed.
