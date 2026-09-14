# Foundation

Public contract core for the Z-Solo-King GitHub family.

_Last verified: Cloudflare Git deploy test — 2026-09-14 (retry after credential fix)._

This repository contains public-safe contracts, schemas, reusable deterministic primitives, the public Worker boundary, and the public CI evidence path. Protected execution, governance, evaluation holdouts, credentials, and promotion authority live outside this public repository.

## Documentation first

For architecture continuity, the authoritative project-level documents are maintained in private Operations because they include protected planning/status context. The current order is:

1. `AI_CODEMAP.json`
2. `docs/FAMILY_CONTRACT.json`
3. `docs/FAMILY_ARCHITECTURE.md`
4. `docs/PUBLIC_DETERMINISTIC_CORE.md`
5. the relevant subsystem/workflow documentation
6. `operations/docs/PROJECT_MASTER_PLAN_2026-09-13.md` when private repository access is available
7. `operations/docs/PROJECT_STATUS_DONE_VS_LEFT_2026-09-13.md` when private repository access is available

Historical chat archives are provenance, not a replacement for current repository source-of-truth documents.

## Public deterministic core

`foundation_core/` is the canonical public implementation for deterministic observed-data routing, normalization, plausibility checks, and product mapping. See `docs/PUBLIC_DETERMINISTIC_CORE.md` for the exact boundary and maintenance rules.

The private Operations repository consumes this package at a pinned public revision. Private compatibility imports may remain temporarily, but public code is the source of truth and must not be forked privately.

## Public Worker boundary

The public Worker is intentionally standalone with respect to readiness and public diagnostics:

- `/health` is public runtime health;
- `/readiness` verifies public runtime plus public D1 health and does not require the private control plane;
- the public chatbot diagnostic exposes only the bounded public infrastructure verification operation;
- no public route may dispatch arbitrary private control-plane operations;
- private Operations may still call Foundation through its protected Service Binding when an authorized private verification path requires it.

## Current storage boundary

Foundation uses D1 for compact operational state and Backblaze B2 for bounded artifacts/object storage. The former R2 design is not the current artifact-store decision and must not be restored without a fresh cross-repository architecture/cost decision.

## AI / human navigation

`AI_CODEMAP.json` is the compact machine-readable map of ownership, canonical modules, boundaries, and change methodology. Read it before scanning the repository broadly.

## Family documentation

`docs/FAMILY_CONTRACT.json` and `docs/FAMILY_ARCHITECTURE.md` define repository ownership and dependency direction.

`docs/RUN_RECORD_PUBLIC_BOUNDARY.md` defines which run/execution/evidence metadata may cross into the public-safe contract layer. Foundation does not own private chatbot run history.

## CI principle

Foundation owns the public, deterministic test surface and enforces complete branch coverage for its product code. Operations does not depend on GitHub-hosted private CI for routine validation; protected checks are executed through non-GitHub-hosted paths when required.
