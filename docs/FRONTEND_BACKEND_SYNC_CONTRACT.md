# Frontend ↔ Backend Sync Contract

**Status:** CURRENT  
**Owner:** Foundation public frontend/backend contract boundary  
**Scope:** public request/response and browser/backend capability synchronization  
**Updated:** 2026-09-18

## Purpose

The browser UI is a contract consumer of the Foundation backend. A feature must either call an existing backend contract, use an explicitly browser-local contract, or be marked unavailable. The UI must not imply backend behavior the Worker does not execute.

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

`GET /api/v1/research/{run_id}` returns the persisted run plus observed source records.

## Research boundary

The public Worker provides bounded source-URL ingestion/publication behavior. It does not by itself imply general web search, autonomous multi-source discovery or unrestricted synthesis.

When a research prompt contains explicit `http://` or `https://` URLs, the UI extracts bounded source URLs and passes them to the Worker so the supported ingestion path is exercised.

## Browser-local state

Chats, projects, saved messages, queue UI state and tab-scoped session-token input remain browser-local until a server-backed contract exists. Such state must be labeled local and never presented as durable backend state.

## Contract split

Lifecycle states, transitions, retry/replay, authentication, and public-boundary disclosure are defined in `docs/EXECUTION_AND_UI_CONTRACT.md`. This document owns the request/response surface and the browser/backend capability split.

## Invariants

- Strict `$0` mode remains enabled.
- Production authorization is fail-closed.
- Session bearer tokens are memory-only in the browser.
- The UI never claims research completion before backend terminal state.
- Async completion retains the originating chat identity.
- Backend-returned evidence/source state is authoritative for displayed research observations.
