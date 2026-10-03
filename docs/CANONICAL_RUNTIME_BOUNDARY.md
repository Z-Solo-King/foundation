# Canonical Runtime Boundary

## Current repository/runtime ownership

Foundation is the public contract and deterministic-core repository. Operations is the private control-plane and execution repository.

The migration target is:

```text
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

## Public-core synchronization tooling — 2026-10-02

The production release boundary now materializes the immutable Foundation public core through the Node-based Operations tool `scripts/sync_public_core.mjs`. The migration changes only build-time synchronization tooling; runtime service-binding and authentication authority remain unchanged.

## Public front door reconciliation — 2026-10-02

The canonical public frontend is the GitHub-backed Cloudflare Pages project `heroic-ai` at `https://heroic-ai.pages.dev`. It serves the existing Foundation frontend and routes `/health`, `/readiness`, and `/api/*` through the `HEROIC_BACKEND` service binding to the production `heroic` Worker.

The retired `ai-cio.pages.dev` Pages project is not the canonical public front door and must not be used by production release or live-probe configuration.

## Production worker staging and privileged automation — 2026-10-03

Production Worker deployment is a controlled release operation, not a general-purpose checkout.

- Python Worker stages are built from an allowlisted runtime tree containing only the selected entrypoint, dependency metadata, required runtime directories and the selected Wrangler configuration.
- Tests, tooling, backups, development virtual environments, migration notes and known provider credential files must not enter a deployment stage.
- Each staged Worker is validated with a Wrangler/Pywrangler dry-run bundle audit before deployment. A generated bundle containing a forbidden path or credential file is a hard failure.
- Privileged workflows use purpose-scoped read-only Operations GitHub App access wherever source inspection is required. AI benchmark and CrossFire results remain advisory evidence and cannot promote or deploy themselves.
- Normal production Cloudflare changes must flow through the canonical Foundation production-release workflow on protected `main`. Direct Cloudflare connector mutation is not a normal deployment path.
- Public receipts contain only sanitized deployment/evidence metadata. Raw private GitHub/Cloudflare responses, credentials, provider payloads and private source identifiers are removed before artifact publication.
- Immutable production pins are lineage controls. Moving Operations `main` ahead of an approved revision is ordinary repository progression; integrity failure requires invalid identity, divergence, or an unauthorized authority transition.

## Production release validation boundary — 2026-10-04

The canonical production release validates the public Foundation surface before touching deployment state. Its pre-deployment validation mirrors the protected Foundation `Public tests` contract: the public product, workflow/security, package-boundary, and deterministic benchmark checks are executed from the Foundation checkout. The Foundation release also records coverage for the executable public product suite as evidence; coverage is not a second, divergent acceptance gate. Private runtime, cross-repository and Operations-owned implementation tests are exercised by the later exact-revision Operations audit after the authenticated private checkout is established. This preserves a single public acceptance contract and a separate private runtime ownership boundary.
