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
2. Production Chat mode never fabricates an assistant answer in the browser when the private runtime is unavailable.
3. Guest Test mode is an explicit browser-local test harness only; its deterministic simulated responses are marked `TEST_ONLY` and are never production or model output.
4. `/api/v1/chat` is authenticated and proxies only through an internal Operations service binding; the browser never receives a private Worker URL.
5. Model output is never authoritative evidence, policy, identity, access control, billing authority or promotion authority.
6. Unknown, blocked, partial, contradicted and stale states remain explicit.
7. Every protected chat action has an idempotency/replay boundary and lifecycle state.
8. Each capability has one canonical owner.

## Current status

Foundation contains the public Heroic AI chat contract and the frontend sends Chat mode through the authenticated canonical lifecycle. Guest Test mode exists solely for local UI/lifecycle verification when authenticated/private execution is unavailable. The public Worker fails closed with `chat_backend_unavailable` when the Operations service binding is not configured.

Operations issue #197 remains the canonical private conversational-executor implementation and acceptance tracker. Production-shaped execution evidence is still required before Heroic AI can be considered a fully operational conversational backend.
