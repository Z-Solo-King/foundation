# Execution and UI State Contract

**Status:** canonical public execution-state contract
**Owner:** Foundation frontend/public boundary

## State layers
Request/UI lifecycle: `NEW_CHAT`, `SUBMITTING`, `QUEUED`, `RUNNING`, `STREAMING`, `COMPLETE`, `PARTIAL`, `BLOCKED`, `REJECTED`, `UNAVAILABLE`, `UNKNOWN/NOT_ATTEMPTED`, `RECONNECTING`, `RESUMED`, `REPLAYED`, `AUTH_EXPIRED`.

Stage outcomes: `completed`, `blocked`, `retryable_failure`, `permanent_failure`, `invalid_input`, `partial`, `evidence_incomplete`, `cancelled`.

Public answer results: `COMPLETED`, `PARTIAL`, `DEGRADED`, `BLOCKED`, `FAILED`, `CANCELLED`.

A completed lower-level stage does not imply a completed answer.

## Transition rules
Submission may become queued, blocked or failed. Queued may become running, blocked or cancelled. Running/streaming may become terminal or partial/degraded. Partial may resume while preserving execution identity and consumed budget. Replayed events are render-only and cannot create duplicate completion. Authentication expiry remains distinct from provider failure.

## Frontend/backend contract
The UI either calls an existing backend contract, uses an explicitly browser-local contract, or marks a capability unavailable. It must never imply backend behavior that the Worker does not execute.

For research, the UI sends only the bounded supported contract: question, depth, citation/size limits, strict-zero-cost state and explicit source URLs when present. Backend lifecycle state is authoritative; the UI never invents completion.

## Research boundary
The public research endpoint currently provides bounded source-URL ingestion/persistence/publication behavior, not unrestricted general web discovery or full autonomous synthesis.

Local-only chats, projects, saved messages, queue state and session-token input remain labeled local until a server-backed contract exists.

## Retry/replay
Duplicate submissions are distinct from retries. Idempotency prevents duplicate side effects. Retries occur only when the backend explicitly identifies the operation as retryable.

## Security
Provider names, policy internals, credentials, prompts and protected diagnostics are never UI state.

## Validation
Acceptance tests verify lifecycle semantics, backend authority, replay behavior and public-boundary disclosure rather than merely DOM presence.
