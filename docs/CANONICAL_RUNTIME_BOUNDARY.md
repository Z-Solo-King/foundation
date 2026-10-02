# Canonical Runtime Boundary

## Current repository/runtime ownership

Foundation is the public contract and deterministic-core repository. Operations is the private control-plane and execution repository.

The migration target is:

```
Public client
  -> Cloudflare public edge: heroic
  -> private/control execution boundary
  -> Operations: private policy, provider execution, acquisition, chatbot orchestration,
     resources, evaluation, promotion/rollback and private runtime state
```

Foundation no longer needs to carry a second copy of the private application runtime. During migration, legacy public-runtime paths are removed only after parity and regression evidence.

## Authority

- Foundation owns public-safe contracts, deterministic observed-data primitives, the public edge/request boundary, public CI, and public release workflows.
- Operations owns protected policy/resource governance, acquisition/extraction, private adapters and execution planning, verification/evaluation, private chatbot orchestration, provider runtime, promotion/canary/rollback, deployment/recovery and private telemetry.
- Cloudflare is the live runtime authority for deployed Worker versions, bindings, schedules and current resource state.

## Transport rule

Cross-repository application reuse is contract-based. Foundation public application/runtime code must not import Operations source or private state. Privileged Foundation workflows may execute a purpose-specific Operations utility only through the documented immutable-commit bridge.

## Public boundary

The public Worker boundary remains thin and public-safe. Public readiness must remain independently testable and must not require private control-plane state.

## Release invariant

A release is valid only when the approved immutable Operations revision, current Foundation revision, Cloudflare bindings, protected policy values, D1 schema, deployment provenance and post-deployment runtime checks agree.

Do not infer production state from historical docs, branch names, or GitHub `main` position alone.

## Migration integrity gate — 2026-10-02

- The public Foundation tree is the consumer-facing contract and deterministic-core surface; private execution behavior moved out of Foundation is owned by Operations.
- A compatibility surface must remain thin, contract-based and non-authoritative. It must not recreate private policy, routing, provider, resource or execution algorithms.
- Cross-repository workflows use purpose-scoped immutable Operations revisions. Production pins are separate from Operations main and must not be advanced implicitly.
- Runtime claims require live evidence at the appropriate level; source files and historical synchronization documents are not production certificates.
