# AI Analysis Map

Compact routing index for human and AI repository analysis. Read this before opening large source, workflow, or historical documents.

## Read first

1. `README.md`
2. `REPOSITORY_MAP.json`
3. `docs/CURRENT_SOURCE_OF_TRUTH.md` — living current-state, issue-gate and evidence summary
4. `docs/AI_AGENT_HANDOFF.md` — compact continuation handoff
5. `DEPLOYMENT.md` for deployment questions
6. `docs/CREDENTIAL_AND_BACKUP_AUTHORITY.md` for credential, B2, backup and evidence questions
7. `docs/AI_AUDIT_AND_VERIFICATION_STANDARD.md` for audit questions
8. `docs/FAMILY_CONTRACT.json` for public-contract questions
9. `docs/FAMILY_SYNC_STANDARD.md` for cross-repository synchronization, status, ownership and evidence rules
10. `docs/FAMILY_SYNC_STATE.json` for the latest recorded family synchronization snapshot
11. Then open the canonical implementation and focused feature-owned tests.

## Focused test navigation

- Execution/resource/provider/research lifecycle: `tests/test_execution_edge_cases.py`
- Worker-task/result/replay boundaries: `tests/test_worker_boundary_edge_cases.py`
- Evidence/claims/lineage/verification: `tests/test_intelligence_edge_cases.py`
- Public HTTP/Wikipedia transport boundary: `tests/test_source_transport_edge_cases.py`
- Public API/capability validation: `tests/test_api_capability_edge_cases.py`
- Public worker HTTP entrypoint: `tests/test_worker_entrypoint_edge_cases.py`
- Run-record/stage-receipt/token-efficiency contracts: `tests/test_run_record_edge_cases.py`
- Public persistence/product-mapping edges: `tests/test_public_core_edge_cases.py`

Former broad coverage aggregators were removed after their useful assertions were relocated to owner-named suites. Do not recreate generic coverage aggregators.

## High-analysis-cost areas

`.github/workflows/nightly-multi-agent-research.yml` contains orchestration, matrix lanes, preflight policy, artifact handling, diagnosis, baseline comparison, attestation and final gating. For narrow questions inspect the relevant job first, then the invoked benchmark module.

`.github/workflows/heroic-ai-production-release.yml` is the single production deployment owner. `.github/workflows/codeql.yml` is security analysis only. `.github/workflows/autonomous-benchmark.yml` is benchmark orchestration. `.github/workflows/b2-repository-backup.yml` is the repository backup/B2 evidence boundary.

## Credential boundary

- `OPERATIONS_READ_TOKEN` belongs to production checkout of the private Operations repository.
- `BACKUP_GITHUB_TOKEN` belongs only to repository mirroring for the B2 backup workflow.
- `B2_KEY_ID`, `B2_APPLICATION_KEY`, and `B2_BUCKET` belong only to B2.
- Never substitute credentials between authorities.

## Analysis rules

- Prefer canonical source over compatibility exports.
- Prefer focused feature-owned tests over broad suite reading.
- Separate workflow state, source state and runtime state.
- Current code/docs/PR/workflow evidence outranks dated plans and chat history.
- A `main` SHA recorded in a sync document is an audit observation, not a replacement for the actual current branch tip.
- Never treat source existence as L3/L4 runtime evidence.
- Historical material should be opened only when a question requires provenance or historical context.
