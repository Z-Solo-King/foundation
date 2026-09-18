# Execution State and Failure Semantics

Status: Canonical Foundation contract
Scope: public-safe execution semantics for research/chat work
Owner: Foundation execution and public-boundary contracts

## 1. State layers

Foundation uses three related state layers. They must not be conflated.

| Layer | Canonical states | Meaning |
|---|---|---|
| Request/UI lifecycle | NEW_CHAT, SUBMITTING, QUEUED, RUNNING, STREAMING, COMPLETE, PARTIAL, BLOCKED, UNAVAILABLE, UNKNOWN, RECONNECTING, RESUMED, REPLAYED, AUTH_EXPIRED | User-visible lifecycle only |
| Stage outcome | completed, blocked, retryable_failure, permanent_failure, invalid_input, partial, evidence_incomplete, cancelled | Deterministic result of one execution stage |
| Public answer result | COMPLETED, PARTIAL, DEGRADED, BLOCKED, FAILED, CANCELLED | Public-safe answer semantics |

A lower-level completed result never implies public answer COMPLETED. Answer completion requires the applicable completeness, evidence, freshness and publication gates to pass.

## 2. State transition rules

| From | Allowed next states | Notes |
|---|---|---|
| NEW_CHAT | SUBMITTING | Request begins |
| SUBMITTING | QUEUED, BLOCKED, FAILED | Admission/auth/validation may terminate early |
| QUEUED | RUNNING, BLOCKED, CANCELLED | No provider execution before governed admission |
| RUNNING | STREAMING, COMPLETE, PARTIAL, DEGRADED, BLOCKED, FAILED, CANCELLED | Terminal reason must remain explicit |
| STREAMING | COMPLETE, PARTIAL, DEGRADED, BLOCKED, FAILED, CANCELLED | Stream completion is not proof of answer completion |
| COMPLETE | terminal | Must never be downgraded silently |
| PARTIAL | RESUMED or terminal | Resume keeps the same execution identity and preserves consumed budget |
| RECONNECTING | RESUMED, REPLAYED, UNAVAILABLE, FAILED | Reconnection must not manufacture duplicate completion |
| RESUMED | RUNNING, STREAMING, PARTIAL, terminal | Existing execution identity is preserved |
| REPLAYED | render-only | Replayed events do not create a second completion side effect |

## 3. Stage-outcome semantics

StageOutcome.RETRYABLE_FAILURE is the only retryable stage class. It is not terminal.

The following are terminal stage outcomes:

- COMPLETED
- BLOCKED
- PERMANENT_FAILURE
- INVALID_INPUT
- PARTIAL
- EVIDENCE_INCOMPLETE
- CANCELLED

UNKNOWN or unrecognized stored outcome values fail closed rather than being treated as success.

## 4. Terminal reasons

Budget exhaustion, deadline expiry, policy denial, unsupported capability, invalid input, dependency failure, explicit cancellation, and evidence incompleteness remain distinct reasons. A generic FAILED label must not erase the more specific lower-level reason.

## 5. Retry and resume

Retries must be bounded by the existing execution/resource authority. Every retry and resume preserves:

- original execution identity;
- already-consumed budget;
- source/evidence lineage;
- idempotency scope;
- terminal reason history.

A retryable stage may re-enter execution. A terminal stage may not be silently rewritten into a successful stage.

## 6. Public serialization

The public result envelope exposes only:

- status;
- result;
- requested/completed/missing/failed scope;
- claim/evidence support state;
- warnings and limitations;
- freshness;
- provenance/execution identity.

Private provider names, runtime topology, credentials, protected diagnostics and unrestricted exception payloads are excluded.

COMPLETED is invalid when required scope is missing/failed, claim support is unresolved, or evidence is stale.

## 7. Evidence of correctness

The canonical implementation is enforced by:

- foundation_core/outcome.py stage-outcome validation;
- the public result-envelope contract;
- the frontend/UI state-machine contract;
- existing lifecycle, outcome, governance and public-boundary tests.

This document is descriptive of those authorities; it does not create a second runtime state authority.