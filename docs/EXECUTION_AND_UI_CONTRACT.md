# Execution and UI State Contract

**Status:** CURRENT  
**Owner:** Foundation frontend/public boundary  
**Scope:** lifecycle states, transitions, retry/replay and public execution semantics  
**Updated:** 2026-09-18

## State layers

Request/UI lifecycle: `NEW_CHAT`, `SUBMITTING`, `QUEUED`, `RUNNING`, `STREAMING`, `COMPLETE`, `PARTIAL`, `BLOCKED`, `REJECTED`, `UNAVAILABLE`, `UNKNOWN/NOT_ATTEMPTED`, `RECONNECTING`, `RESUMED`, `REPLAYED`, `AUTH_EXPIRED`.

Stage outcomes: `completed`, `blocked`, `retryable_failure`, `permanent_failure`, `invalid_input`, `partial`, `evidence_incomplete`, `cancelled`.

Public answer results: `COMPLETED`, `PARTIAL`, `DEGRADED`, `BLOCKED`, `FAILED`, `CANCELLED`.

A completed lower-level stage does not imply a completed answer.

## Transition rules

Submission may become queued, blocked or failed. Queued may become running, blocked or cancelled. Running/streaming may become terminal or partial/degraded. Partial may resume while preserving execution identity and consumed budget. Replayed events are render-only and cannot create duplicate completion. Authentication expiry remains distinct from provider failure.

## Frontend/backend split

The request and response surface is defined in `docs/FRONTEND_BACKEND_SYNC_CONTRACT.md`. This document owns lifecycle semantics: backend state is authoritative, the UI cannot invent completion, and browser-local state cannot impersonate server state.

## Retry/replay

Duplicate submissions are distinct from retries. Idempotency prevents duplicate side effects. Retries occur only when the backend explicitly identifies the operation as retryable. Replayed events cannot create duplicate completion or charges.

## Research boundary

The public research endpoint remains a bounded source-URL ingestion/persistence/publication capability. It is not unrestricted general web discovery or autonomous synthesis.

## Security

Provider names, policy internals, credentials, protected prompts and protected diagnostics are never UI state. Public readiness does not certify private control-plane execution.

## Validation

Acceptance tests verify lifecycle semantics, backend authority, retry/replay behavior and public-boundary disclosure rather than merely DOM presence.
