# AI Analysis Map

Compact routing index for human and AI repository analysis. Read this before opening large source, workflow, or historical documents.

## Read first

1. `README.md`
2. `REPOSITORY_MAP.json`
3. `DEPLOYMENT.md` for deployment questions
4. `docs/CREDENTIAL_AND_BACKUP_AUTHORITY.md` for credential, B2, backup and evidence questions
5. `docs/AI_AUDIT_AND_VERIFICATION_STANDARD.md` for audit questions
6. `docs/FAMILY_CONTRACT.json` for public-contract questions
7. Then open the canonical implementation and focused tests.

## High-analysis-cost areas

`.github/workflows/nightly-multi-agent-research.yml` contains orchestration, matrix lanes, preflight policy, artifact handling, diagnosis, baseline comparison, attestation, and final gating. For narrow questions inspect the relevant job first, then the invoked benchmark module. Research logic belongs in the benchmark package.

`.github/workflows/codeql.yml` is the single production deployment owner. `.github/workflows/autonomous-benchmark.yml` is benchmark orchestration. `.github/workflows/b2-repository-backup.yml` is the repository backup/B2 evidence boundary. These are orchestration/evidence boundaries, not application runtime modules.

## Credential boundary

- `OPERATIONS_READ_TOKEN` belongs to production checkout of the private Operations repository.
- `BACKUP_GITHUB_TOKEN` belongs only to repository mirroring for the B2 backup workflow.
- `B2_KEY_ID`, `B2_APPLICATION_KEY`, and `B2_BUCKET` belong only to B2.
- Never substitute credentials between authorities.

## Analysis rules

- Prefer canonical source over compatibility exports.
- Prefer focused tests over broad test-suite reading.
- Separate workflow state, source state, and runtime state.
- Do not infer missing behavior from file size or workflow length.
- Structural refactors require regression coverage and required checks.
- Package boundaries and compatibility exports are part of the public contract.
- Current code/docs/PR/workflow evidence outranks dated plans and chat history.
