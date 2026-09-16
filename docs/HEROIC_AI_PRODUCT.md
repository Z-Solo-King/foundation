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

## Ownership

Foundation owns the public-safe request/evidence contracts and deterministic correctness surfaces. Operations owns private chatbot orchestration and protected authority.

| Capability | Foundation | Operations |
| --- | --- | --- |
| Heroic AI chat UI | canonical | consumes |
| public chat request schema | canonical | consumes |
| research/evidence semantics | canonical | orchestrates |
| deterministic extraction/mapping | canonical | consumes |
| private routing | boundary only | canonical |
| provider/model runtime | no secrets | canonical |
| user/project memory | no | canonical |
| protected policy/resource/security | no | canonical |

## Rules

1. Chat is the front door; research is a capability selected because a request needs evidence.
2. The frontend never invents assistant answers when the private runtime is unavailable.
3. `/api/v1/chat` is authenticated and proxies only through an internal Operations service binding; the browser never receives a private Worker URL.
4. Model output is never authoritative evidence, policy, identity, access control, billing authority or promotion authority.
5. Unknown, blocked, partial, contradicted and stale states remain explicit.
6. Every protected chat action has an idempotency/replay boundary and lifecycle state.
7. Each capability has one canonical owner.

## Current status

Foundation contains the public Heroic AI chat contract and the frontend sends Chat mode through it instead of fabricating a browser-local reply. The public Worker fails closed with `chat_backend_unavailable` when the Operations service binding is not configured.

Operations issue #197 remains the canonical private conversational-executor implementation and acceptance tracker. Production-shaped execution evidence is still required before Heroic AI can be considered a fully operational conversational backend.
