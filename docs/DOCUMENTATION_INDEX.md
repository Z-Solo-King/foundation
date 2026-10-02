# Foundation documentation index

**Role:** public-safe contracts, evidence, deterministic core, public API/frontend, GitHub Actions and deployment orchestration.

## Read first
1. `README.md`
2. `REPOSITORY_MAP.json`
3. `docs/AI_PROJECT_MAP.json`
4. `docs/AI_PROJECT_MAP.md`
5. `docs/AI_AUDIT_SYSTEM.md`
6. `docs/AI_COMPUTE_INSPIRED_PATTERNS.md`
7. `docs/DOCUMENTATION_INDEX.md`
8. `docs/DOCUMENTATION_HYGIENE.md`
8. `docs/REPOSITORY_HYGIENE_AND_FORMAT_STANDARD.md`
9. `docs/FAMILY_FULL_COVERAGE_STANDARD.md`
10. `docs/FAMILY_CONTRACT.json`
11. `docs/FAMILY_ARCHITECTURE.md`
12. `docs/FAMILY_SYNC_STANDARD.md`
13. `docs/FAMILY_SYNC_STATE.json`
14. `docs/CROSS_REPO_CLOUDFLARE_SYNC.md`
15. `docs/REQUIREMENT_COVERAGE_RECONCILIATION_2026-09-17.md`
16. `docs/PUBLIC_DETERMINISTIC_CORE.md`
17. `docs/RUN_RECORD_PUBLIC_BOUNDARY.md`
19. `DEPLOYMENT.md`

## Authority
The live `main` tree, current PR/workflow state and fresh execution evidence outrank dated plans, handoffs and chat notes. `FAMILY_SYNC_STATE.json` is an audit snapshot, not a live queue or production certificate.

Foundation owns public-safe contracts/schemas, deterministic observed-data/evidence primitives, the public API/Worker/frontend boundary and public CI/deployment workflow. Operations owns private acquisition, provider credentials/runtime, protected resource/quota authority, private chatbot orchestration, evaluation, promotion/rollback, recovery and private runtime state.

## Cross-repository boundary
`Foundation public contract/core -> Operations private control plane`

Operations may consume public contracts. Foundation must not copy private policy/runtime logic or private secrets.

## Tests / deployment
Coverage tests are feature-owned. Generic aggregation filenames must not be recreated merely to collect edge cases.

`DEPLOYMENT.md` is the detailed public deployment guide. A workflow, secret configuration or deployment script is not production evidence by itself; current production claims require evidence tied to the deployed revision.

## Documentation maintenance
When contracts, ownership, workflows, dependencies or production gates change, update the canonical owner in the same PR. Dated continuity material is historical. Unique evidence is retained and indexed; pointer-only stubs and duplicate prose may be retired after dependency checks.

## Current cross-system snapshot
`docs/CROSS_REPO_CLOUDFLARE_SYNC.md` is the 2026-09-28 dated synchronization record. Do not use it to infer mutable issue counts or current runtime status later.

## Canonical feed boundary

Public feed documentation is methodology-only. Live target state and recovery execution belong to Operations. docs/WOOCOMMERCE_GOOGLE_FEED_RECOVERY_1247.md is the public contract/method reference; it is not a live target registry or completion certificate.


20. docs/PUBLIC_RELEASE_GOVERNANCE.md

The public feed recovery boundary and release-publication safety rule are defined by docs/PUBLIC_RELEASE_GOVERNANCE.md and docs/WOOCOMMERCE_GOOGLE_FEED_RECOVERY_1247.md; enforcement is scripts/validate_release_publication_policy.mjs.
