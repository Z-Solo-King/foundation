# Foundation Documentation Index

**Status:** current as of 2026-09-16. Foundation is the public-safe contract, evidence, deterministic-core and public Worker/CI owner.

## Read first

1. `README.md`
2. `docs/DOCUMENTATION_INDEX.md`
3. `docs/DOCUMENTATION_HYGIENE.md`
4. `docs/FAMILY_CONTRACT.json`
5. `docs/FAMILY_ARCHITECTURE.md`
6. `docs/PUBLIC_DETERMINISTIC_CORE.md`
7. `docs/RUN_RECORD_PUBLIC_BOUNDARY.md`
8. `DEPLOYMENT.md` and `.github/workflows/codeql.yml`

## Ownership

Foundation owns public-safe contracts/schemas, deterministic evidence/observation primitives, the public API/Worker, frontend boundary and public CI/deployment workflow.

Operations owns private acquisition policy, provider credentials/runtime, protected resource/quota authority, chatbot orchestration, private evaluation and promotion/rollback.

Foundation remains independent of Operations source and private authority; Operations consumes pinned Foundation contracts through the defined boundary.

## Deployment evidence

The canonical public deployment workflow is `.github/workflows/codeql.yml`. Source-level tests and historical deployment notes are not production proof; runtime claims require fresh evidence tied to the deployed revision.

Dated continuity/handoff documents are historical unless explicitly marked current. Repository state and current GitHub evidence override them.
