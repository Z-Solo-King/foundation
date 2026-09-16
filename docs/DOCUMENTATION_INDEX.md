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
8. `docs/PUBLIC_DETERMINISTIC_CORE.md` — public implementation boundary.
9. `docs/RUN_RECORD_PUBLIC_BOUNDARY.md` — public/private run-record boundary.
10. `DEPLOYMENT.md` and `.github/workflows/codeql.yml` — public deployment path.

## Source of truth

The current `main` tree, current pull requests/workflows and fresh execution evidence outrank dated plans, handoffs and chat notes. This index is navigation, not a commit or production-status record.

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

## Deployment documentation

`DEPLOYMENT.md` is the detailed deployment guide. It records the approved workflow and the evidence rules for distinguishing a deployment attempt from current production verification.

## Documentation updates

When contracts, ownership, workflows, dependency direction or production gates change, update the affected canonical document in the same change set. Mark dated continuity material as historical.
