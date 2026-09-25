# Foundation Documentation Index

**Status:** current repository guidance
**Repository role:** public-safe contract, evidence, deterministic core and public Worker/CI owner

## Read first

1. `README.md` — repository purpose and boundaries.
2. `REPOSITORY_MAP.json` — ownership and canonical modules.
3. `docs/DOCUMENTATION_INDEX.md` — documentation navigation.
4. `docs/DOCUMENTATION_HYGIENE.md` — documentation maintenance rules.
5. `docs/FAMILY_CONTRACT.json` — family ownership contract.
6. `docs/FAMILY_ARCHITECTURE.md` — repository roles and dependency direction.
7. `docs/FAMILY_SYNC_STANDARD.md` — uniform cross-repository synchronization, status and evidence format.
8. `docs/FAMILY_SYNC_STATE.json` — latest recorded family synchronization snapshot.
9. `docs/FAMILY_INTEGRATION_GRAPH.json` — machine-readable cross-surface topology, material-derived benchmark probes and integration loops.
10. `docs/FAMILY_INTEGRATION_ARCHITECTURE_2026-09-25.md` — narrative integration spine and maintenance questions.
11. `docs/REQUIREMENT_COVERAGE_RECONCILIATION_2026-09-17.md` — current implementation-vs-plan reconciliation.
12. `docs/PUBLIC_DETERMINISTIC_CORE.md` — public implementation boundary.
13. `docs/RUN_RECORD_PUBLIC_BOUNDARY.md` — public/private run-record boundary.
14. `DEPLOYMENT.md` and `.github/workflows/heroic-ai-production-release.yml` — public deployment path.

## Source of truth

The current `main` tree, current pull requests/workflows and fresh execution evidence outrank dated plans, handoffs and chat notes. `docs/FAMILY_SYNC_STATE.json` records the last audit observation; its SHA values must be compared with the live branch tips before making a fresh current-state claim.

This index is navigation, not a commit or production-status record.

## Responsibilities

Foundation owns public-safe contracts and schemas, deterministic observed-data/evidence primitives, the public API/Worker and frontend boundary, and the canonical public CI/deployment workflow.

Foundation does not own private acquisition policy, provider credentials/runtime, protected resource or quota authority, private chatbot orchestration, private holdouts, promotion/rollback authority or private runtime state.

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

Coverage tests are maintained in the flat top-level `tests/` tree and organized by owning production boundary/subsystem rather than physically colocated beside source modules. The audited generic `tests/test_coverage_*` aggregators have been replaced by focused owner-named suites covering execution, worker boundary, intelligence/evidence, source transport, API/capabilities, Worker entrypoint, run-record/token-efficiency contracts, and public-core persistence/product mapping.

The generic filenames must not be recreated merely to collect edge cases. Subsystem-scoped suites such as `test_edge_cases.py`, `test_execution_edge_cases.py`, and `test_intelligence_edge_cases.py` are acceptable when their assertions remain tied to a clearly identified production owner. Test relocation is optional; the required invariant is clear ownership and preserved assertions, not physical directory colocation.

## Deployment documentation

`DEPLOYMENT.md` is the detailed deployment guide. It records `.github/workflows/heroic-ai-production-release.yml` and the evidence rules for distinguishing a deployment attempt from current production verification.

## Documentation updates

When contracts, ownership, workflows, dependency direction or production gates change, update the affected canonical document in the same change set. Mark dated continuity material as historical. When a production workflow filename or ownership boundary changes, update both this navigation entry and `DEPLOYMENT.md` in the same PR.

For family-wide synchronization changes, update `FAMILY_SYNC_STATE.json` and the affected Operations source-of-truth/navigation records in the same coordinated change set.

- `docs/runtime-evidence-ownership.md` — runtime acceptance ownership matrix and AI rules of engagement.
