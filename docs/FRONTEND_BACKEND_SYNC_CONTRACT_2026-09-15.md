# Frontend ↔ Backend Sync Contract — 2026-09-15

**Status:** current — please confirm against latest API/frontend state before relying on this for new work

## Purpose

The browser UI is a contract consumer of the Foundation backend. A frontend feature MUST either:

1. call an existing backend contract and expose its returned data;
2. persist against a documented browser-local contract when the backend does not own that state; or
3. be explicitly marked as unavailable/not implemented.

The frontend must not imply backend capabilities that the Worker does not execute.

## Current research contract

`POST /api/v1/research`

Request fields consumed by the Worker:

- `question`
- `depth`: `quick | standard | deep`
- `require_citations`
- `max_sources`
- `max_evidence_items`
- `strict_zero_cost_only` (must remain `true`)
- `source_urls`

Optional `Idempotency-Key` prevents duplicate submissions for the same request intent.

`GET /api/v1/research/{run_id}` returns the persisted run plus observed source records. The UI must treat `planned`, `running`, `completed`, `failed`, and `cancelled` as backend lifecycle states, not invent a completion state locally.

## Backend capability boundary

The public Worker currently provides bounded source-URL ingestion and persistence. It does not by itself imply general web search, autonomous multi-source discovery, or synthesis for every request. The UI must surface that distinction rather than claiming a full conversational/research backend.

When a research prompt contains explicit `http://` or `https://` URLs, the UI extracts bounded source URLs and passes them to the Worker so the existing ingestion path is actually exercised.

## Local-only capabilities

Chats, projects, saved messages, queue UI state, and tab-scoped session-token input remain browser-local until a server-backed contract exists. These features must be labeled local and must not be described as durable backend state.

## Invariants

- Strict `$0` mode remains enabled.
- Authorization remains fail-closed in production.
- Session bearer tokens are memory-only in the browser.
- The UI must never claim a run completed until the backend reports a terminal lifecycle state.
- Async completion must retain the originating chat identity.
- Backend-returned evidence/source state is authoritative for displayed research observations.
