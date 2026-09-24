# AI Analysis Map

Compact routing index for human and AI repository analysis. Read this before opening large source, workflow, or historical documents.

## Read first

1. `README.md`
2. `REPOSITORY_MAP.json`
3. `DEPLOYMENT.md` for deployment questions
4. `docs/CREDENTIAL_AND_BACKUP_AUTHORITY.md` for credential, B2, backup and evidence questions
5. `docs/AI_AUDIT_AND_VERIFICATION_STANDARD.md` for audit questions
6. `docs/FAMILY_CONTRACT.json` for public-contract questions
7. `docs/FAMILY_SYNC_STANDARD.md` for cross-repository synchronization, status, ownership and evidence rules
8. `docs/FAMILY_SYNC_STATE.json` for the latest recorded family synchronization snapshot
9. `docs/REQUIREMENT_COVERAGE_RECONCILIATION_2026-09-17.md` for the latest implementation-vs-plan reconciliation
10. Then open the canonical implementation and focused feature-owned tests.

## Focused test navigation

- Execution/resource/provider/research lifecycle: `tests/test_execution_edge_cases.py`
- Worker-task/result/replay boundaries: `tests/test_worker_boundary_edge_cases.py`
- Evidence/claims/lineage/verification: `tests/test_intelligence_edge_cases.py`
- Public HTTP/Wikipedia transport boundary: `tests/test_source_transport_edge_cases.py`
- Public API/capability validation: `tests/test_api_capability_edge_cases.py`
- Public worker HTTP entrypoint: `tests/test_worker_entrypoint_edge_cases.py`
- Run-record/stage-receipt/token-efficiency contracts: `tests/test_run_record_edge_cases.py`
- Public persistence/product-mapping edges: `tests/test_public_core_edge_cases.py`

The former `test_coverage_*` files were broad aggregators. They were audited by content and removed only after their branch assertions were relocated to feature-owned suites. Do not recreate generic coverage aggregators.

## High-analysis-cost areas

`.github/workflows/nightly-multi-agent-research-v3.yml` contains orchestration, matrix lanes, preflight policy, artifact handling, diagnosis, baseline comparison, attestation, and final gating. For narrow questions inspect the relevant job first, then the invoked benchmark module. Research logic belongs in the benchmark package.

`.github/workflows/heroic-ai-production-release.yml` is the single production deployment owner. `.github/workflows/codeql.yml` is security analysis only. `.github/workflows/autonomous-benchmark.yml` is benchmark orchestration. `.github/workflows/b2-repository-backup.yml` is the repository backup/B2 evidence boundary. These are orchestration/evidence boundaries, not application runtime modules.

## Credential boundary

- `OPERATIONS_APP_ID` and `OPERATIONS_APP_PRIVATE_KEY` belong to the GitHub App used for private Operations source access in deployment/backup workflows.
- `B2_KEY_ID`, `B2_APPLICATION_KEY`, and `B2_BUCKET` belong only to B2.
- Never substitute credentials between authorities.

## Analysis rules

- Prefer canonical source over compatibility exports.
- Prefer focused feature-owned tests over broad suite reading.
- Separate workflow state, source state, and runtime state.
- Do not infer missing behavior from file size or workflow length.
- Structural refactors require regression coverage and required checks.
- Package boundaries and compatibility exports are part of the public contract.
- Current code/docs/PR/workflow evidence outranks dated plans and chat history.
- A `main` SHA recorded in a sync document is an audit observation, not a replacement for the actual current branch tip.
- Never treat source existence as L3/L4 runtime evidence.
