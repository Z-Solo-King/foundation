# Foundation Documentation Index

**Status:** Current as of 2026-09-16  
**Repository role:** public-safe contract, evidence, deterministic-core and public Worker/CI owner

## Read-first order

1. `README.md` — public purpose and boundaries.
2. `AI_CODEMAP.json` — machine-readable ownership and canonical modules.
3. `docs/DOCUMENTATION_INDEX.md` — this navigation contract.
4. `docs/DOCUMENTATION_HYGIENE.md` — documentation maintenance rules.
5. `docs/FAMILY_CONTRACT.json` — machine-readable family boundary.
6. `docs/FAMILY_ARCHITECTURE.md` — ownership and dependency direction.
7. `docs/PUBLIC_DETERMINISTIC_CORE.md` — public-safe implementation boundary.
8. `docs/RUN_RECORD_PUBLIC_BOUNDARY.md` — public/private run-record boundary.
9. `DEPLOYMENT.md` and `.github/workflows/codeql.yml` — canonical public deployment path.

## Current audited head

Foundation `main`: `73dac355789671d27d5d84697fc937293d9d665c`.

This index is navigation, not production evidence. Runtime claims require fresh execution evidence tied to the deployed revision.

## Canonical responsibilities

Foundation owns public-safe contracts and schemas, deterministic observed-data/evidence primitives, the public API/Worker and frontend boundary, and the canonical public CI/deployment workflow.

Foundation does not own private acquisition policy, provider credentials/runtime, protected resource/quota authority, private chatbot orchestration, private holdouts, promotion/rollback authority, or private runtime deployment control.

## Relationship with Operations

```text
Foundation (public-safe contracts + deterministic core + public Worker/CI)
                              |
                         typed/service boundary
                              v
Operations (private policy + orchestration + acquisition + protected execution)
```

Operations may consume Foundation contracts and public-safe service surfaces. Foundation must remain independent of Operations source and private authority.

## Current deployment-documentation rule

The canonical public deployment workflow is `.github/workflows/codeql.yml`. The latest audited Foundation production attempt is not treated as successful end-to-end production proof because the private Operations checkout was rejected by the GitHub Actions credential. Older successful smoke claims must not be copied forward as current proof.

## Documentation update rule

Changes to public contracts, schemas, deterministic algorithms, public/private boundaries, deployment ownership, workflow behavior, or dependency direction must update the affected canonical document in the same change set.

Dated continuity/handoff documents are historical unless explicitly marked current. Repository state, current `main` heads, current PRs/workflows, and fresh runtime evidence override historical notes.
