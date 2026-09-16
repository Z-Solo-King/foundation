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
7. `docs/FAMILY_MAINTAINABILITY_STANDARD.md` — single-owner/change/removal rules.
8. `docs/CREDENTIAL_AND_BACKUP_AUTHORITY.md` — credential purpose, B2/backup boundary and evidence rules.
9. `docs/AI_AUDIT_AND_VERIFICATION_STANDARD.md` — evidence-level and audit discipline.
10. `docs/PUBLIC_DETERMINISTIC_CORE.md` — public implementation boundary.
11. `docs/RUN_RECORD_PUBLIC_BOUNDARY.md` — public/private run-record boundary.
12. `DEPLOYMENT.md` and `.github/workflows/codeql.yml` — canonical production deployment path.
13. `backup/README.md` and `.github/workflows/b2-repository-backup.yml` — repository backup/B2 execution and restore evidence.

## Source of truth

The current `main` tree, current pull requests/workflows and fresh execution evidence outrank dated plans, handoffs and chat notes. This index is navigation, not a commit or production-status record.

## Responsibilities

Foundation owns public-safe contracts and schemas, deterministic observed-data/evidence primitives, the public API/Worker and frontend boundary, the canonical public CI/deployment workflow, and the repository-backup/B2 workflow boundary.

Foundation does not own private acquisition policy, provider credentials/runtime, protected resource or quota authority, private chatbot orchestration, private holdouts, promotion/rollback authority or private runtime state.

## Credential boundary

The family uses purpose-specific credentials. `OPERATIONS_READ_TOKEN` is the dedicated GitHub read credential for the canonical production checkout of private Operations. `BACKUP_GITHUB_TOKEN` is a separate GitHub read credential used only by the B2 repository-backup workflow. `B2_KEY_ID`, `B2_APPLICATION_KEY` and `B2_BUCKET` authenticate/configure B2 only. Never substitute credentials between authorities.

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

When contracts, ownership, workflows, dependency direction, credential authority, backup behavior or production gates change, update the affected canonical document in the same change set. Mark dated continuity material as historical. A material change is not complete until the source, owning documentation, focused tests and current issue/PR record agree.
