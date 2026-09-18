# Foundation Documentation Index

**Status:** current repository guidance
**Repository role:** public-safe contract, evidence, deterministic core and public Worker/CI owner

## Read first

1. `README.md` — repository purpose and boundaries.
2. `REPOSITORY_MAP.json` — ownership and canonical modules.
3. `docs/CURRENT_SOURCE_OF_TRUTH.md` — living current-state record.
4. `docs/AI_AGENT_HANDOFF.md` — compact maintenance handoff.
5. `docs/DOCUMENTATION_HYGIENE.md` — documentation maintenance rules.
6. `docs/FAMILY_CONTRACT.json` — family ownership contract.
7. `docs/FAMILY_ARCHITECTURE.md` — repository roles and dependency direction.
8. `docs/FAMILY_SYNC_STANDARD.md` — uniform cross-repository synchronization, status and evidence format.
9. `docs/FAMILY_SYNC_STATE.json` — latest recorded family synchronization snapshot.
10. `docs/PUBLIC_DETERMINISTIC_CORE.md` — public implementation boundary.
11. `docs/RUN_RECORD_PUBLIC_BOUNDARY.md` — public/private run-record boundary.
12. `DEPLOYMENT.md` and `.github/workflows/heroic-ai-production-release.yml` — public deployment path.

## Source of truth

The current `main` tree, current pull requests/workflows and fresh execution evidence outrank dated plans, handoffs and chat notes. `docs/FAMILY_SYNC_STATE.json` records the last audit observation; compare its SHAs with live branch tips before making a fresh current-state claim.

This index is navigation, not a commit or production-status record.

## Responsibilities

Foundation owns public-safe contracts and schemas, deterministic observed-data/evidence primitives, the public API/Worker and frontend boundary, and the canonical public CI/deployment workflow.

Foundation does not own private acquisition policy, provider credentials/runtime, protected resource/quota authority, private chatbot orchestration, private holdouts, promotion/rollback authority or private runtime state.

## Relationship with Operations

```text
Foundation public contract/core
            |
      typed/service boundary
            v
Operations private control plane
```

Operations may consume Foundation contracts and public-safe services. Foundation remains independent of Operations source and private authority.

## Feature-owned test navigation

Coverage tests are maintained in the flat top-level `tests/` tree and organized by owning production boundary/subsystem. Generic coverage aggregators must not be recreated merely to collect edge cases.

## Deployment documentation

`DEPLOYMENT.md` is the detailed deployment guide. It records `.github/workflows/heroic-ai-production-release.yml` and the evidence rules for distinguishing a deployment attempt from current production verification.

## Documentation lifecycle

Living current-state documents are deliberately limited to the current source-of-truth, handoff, family synchronization standard/state, architecture/ownership standards and topic-specific contracts.

Dated audits, handoffs and requirement snapshots are historical context unless they are explicitly retained as unique provenance. When a dated record becomes redundant, incorporate its useful facts into the living documents and delete the duplicate rather than creating another continuation snapshot.

When contracts, ownership, workflows, dependency direction or production gates change, update the affected canonical document in the same change set.
