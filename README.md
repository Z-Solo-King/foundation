# Foundation

Public contract core for the Z-Solo-King GitHub family.

Foundation contains public-safe contracts, schemas, deterministic primitives, the public Worker/frontend boundary and public CI/deployment evidence path. Protected execution, governance, credentials, private evaluation and promotion authority live in Operations.

## Read first

1. `docs/DOCUMENTATION_INDEX.md`
2. `REPOSITORY_MAP.json`
3. `docs/FAMILY_CONTRACT.json`
4. `docs/FAMILY_ARCHITECTURE.md`
5. `docs/PUBLIC_DETERMINISTIC_CORE.md`

Live repository state and fresh GitHub evidence override dated continuity notes.

## GitHub Actions

Foundation owns the public GitHub-hosted execution surface. Private Operations is deliberately not a GitHub-hosted runtime dependency.

## Deterministic core

`foundation_core/` is the canonical public implementation for deterministic observed-data routing, normalization, plausibility checks and product mapping. Operations consumes it at a pinned public revision.

## Public Worker

The Worker remains standalone for `/health` and `/readiness`. Public routes cannot dispatch arbitrary private control-plane operations. Authorized private verification may use the protected service boundary.

## Storage

D1 is used for compact operational state. Backblaze B2 is the artifact/object-storage path. The former R2 design is retired.
