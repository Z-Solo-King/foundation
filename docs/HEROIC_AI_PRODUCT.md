# Heroic AI Product

## Product identity

**Heroic AI** is the product and the primary user journey. The repository family exists to make Heroic AI a reliable, evidence-grounded assistant.

Research, extraction, comparison, file understanding, memory and model execution are capabilities behind the assistant. They are not competing products or parallel architectural centers.

## Canonical user journey

```text
User
  -> Heroic AI frontend
  -> authenticated public chat contract
  -> private Operations control plane
  -> deterministic tools / evidence / approved model execution
  -> grounded response + citations + lifecycle state + artifacts
```

Research is one Heroic AI capability. The user should not need to understand the internal capability boundary just to use the assistant.

## Repository ownership

Foundation owns the public-safe contract and deterministic correctness surfaces. Operations owns private orchestration and protected authority.

| Heroic AI capability | Foundation | Operations |
| --- | --- | --- |
| user-facing chat UI | canonical | consumes contract |
| public chat request schema | canonical | consumes |
| research/evidence semantics | canonical | orchestrates |
| deterministic extraction/mapping primitives | canonical | consumes |
| private chat routing | contract boundary | canonical |
| provider/model eligibility and runtime | no secrets | canonical |
| user/project memory | no | canonical |
| protected policy/security/resource authority | no | canonical |
| production deployment owner | canonical public workflow | no competing deployer |

## Non-negotiable product rules

1. Chat is the front door. Research is invoked because the user's request needs it.
2. The frontend never invents an assistant answer when the private conversational runtime is unavailable.
3. The public `/api/v1/chat` contract is authenticated and uses an internal Operations service binding; the browser never receives a private Worker URL.
4. Model output is never evidence, policy, identity, access control, billing authority or promotion authority.
5. Search visibility is not authorization; undocumented endpoints are not automatically executable.
6. Unknown, blocked, partial, contradicted and stale states remain explicit.
7. Every protected chat action has an idempotency/replay boundary and an observable lifecycle state.
8. A capability has one canonical owner; adapters may expose it but may not fork it.

## Current product status

The public Heroic AI chat contract is implemented in Foundation. The frontend sends Chat mode through `/api/v1/chat` and no longer fabricates a browser-local assistant answer. The public Worker proxies only through the configured private Operations service binding and fails closed with `chat_backend_unavailable` when that binding is absent.

The remaining product-critical implementation is in Operations issue #197: `POST /v1/chat` must execute the routed capability/model path and return a versioned grounded response. Until that path has current production-shaped execution evidence, Heroic AI must not be described as having a fully operational conversational backend.
