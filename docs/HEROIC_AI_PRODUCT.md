# Heroic AI Product

## Product identity

**Heroic AI** is the product and the primary user journey. The repository family exists to make Heroic AI a reliable, evidence-grounded assistant.

Research, extraction, comparison, file understanding, memory and model execution are capabilities behind the assistant. They are not competing products or parallel architectural centers.

## Canonical user journey

```text
User
  |
  v
Heroic AI chat UI
  |
  v
Typed chat request
  |
  +--> deterministic/local capability
  |
  +--> research capability
  |       |
  |       +--> source resolution
  |       +--> acquisition
  |       +--> extraction/mapping
  |       +--> evidence/claim verification
  |
  +--> approved model capability
  |
  v
Grounded response
  |
  +--> citations / evidence state
  +--> uncertainty / blocked / partial state
  +--> artifacts when applicable
  +--> memory/learning signals when explicitly allowed
```

## Repository ownership

Foundation owns the public-safe contract and deterministic correctness surfaces. Operations owns private orchestration and protected authority.

| Heroic AI capability | Foundation | Operations |
| --- | --- | --- |
| user-facing chat UI | canonical | consumes contract |
| public request schema | canonical | consumes |
| research/evidence semantics | canonical | orchestrates |
| deterministic extraction/mapping primitives | canonical | consumes |
| private chat routing | contract boundary | canonical |
| provider/model eligibility and runtime | no secrets | canonical |
| user/project memory | no | canonical |
| protected policy/security/resource authority | no | canonical |
| production deployment owner | canonical public workflow | no competing deployer |

## Non-negotiable product rules

1. Chat is the front door. Research is invoked because the user's request needs it.
2. The UI must not invent answers when the conversational backend is unavailable.
3. Model output is never evidence, policy, identity, access control, billing authority or promotion authority.
4. Search visibility is not authorization; undocumented endpoints are not automatically executable.
5. Unknown, blocked, partial, contradicted and stale states remain explicit.
6. The public frontend never directly exposes private Operations credentials or private Worker access.
7. A capability has one canonical owner; adapters may expose it but may not fork it.
8. Every meaningful chat action should have an idempotency/replay boundary and an observable lifecycle state.

## Current product gap

The frontend is already branded and structured as Heroic AI, but Chat mode is still browser-local. The next runtime milestone is the authenticated public-to-private conversational path. Until that path has real end-to-end execution evidence, the product must not claim a fully operational conversational backend.
