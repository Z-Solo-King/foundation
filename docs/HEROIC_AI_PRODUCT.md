# Heroic AI Product

**Status:** CURRENT  
**Owner:** Foundation public product boundary  
**Scope:** user journey and public/private capability boundary  
**Updated:** 2026-09-18

## Product identity

**Heroic AI** is the product and primary user journey. Research, extraction, comparison, file understanding, memory and model execution are capabilities behind the assistant, not competing architectural centers.

## Canonical user journey

```text
User
  -> Heroic AI frontend
  -> authenticated public chat contract
  -> private Operations control plane
  -> deterministic tools / evidence / approved model execution
  -> grounded response + citations + lifecycle state + artifacts
```

## Ownership

Foundation owns public-safe request/evidence contracts and deterministic correctness surfaces. Operations owns private chatbot orchestration and protected authority. The family ownership contract is canonical in `docs/FAMILY_CONTRACT.json`.

## Rules

1. Chat is the front door; research is a capability selected when evidence is required.
2. Production Chat mode never fabricates an assistant answer in the browser when the private runtime is unavailable.
3. Guest Test mode is a browser-local harness only; simulated responses are marked `TEST_ONLY`.
4. `/api/v1/chat` is authenticated and proxies only through an internal Operations service binding; the browser never receives a private Worker URL.
5. Model output is never authoritative evidence, policy, identity, access control, billing authority or promotion authority.
6. Unknown, blocked, partial, contradicted and stale states remain explicit.
7. Protected chat actions retain an idempotency/replay boundary and lifecycle state.
8. Each capability has one canonical owner.

## Stable implementation boundary

The frontend owns presentation and local-only UI state; Foundation owns the public request/evidence boundary; Operations owns protected routing, providers, resources, memory, evaluation and promotion. Live implementation and acceptance remain authoritative over this summary.
