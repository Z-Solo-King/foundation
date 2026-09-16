# AI Analysis Map

Compact routing index for human and AI repository analysis. Read this before opening large source, workflow, or historical documents.

## Read first

1. `README.md`
2. `REPOSITORY_MAP.json`
3. `DEPLOYMENT.md` for deployment questions
4. `docs/AI_AUDIT_AND_VERIFICATION_STANDARD.md` for audit questions
5. `docs/FAMILY_CONTRACT.json` for public-contract questions
6. Then open the canonical implementation and focused tests.

## High-analysis-cost areas

`.github/workflows/nightly-multi-agent-research.yml` contains orchestration, matrix lanes, preflight policy, artifact handling, diagnosis, baseline comparison, attestation, and final gating. For narrow questions inspect the relevant job first, then the invoked benchmark module. Research logic belongs in the benchmark package.

`.github/workflows/codeql.yml`, `.github/workflows/autonomous-benchmark.yml`, and `.github/workflows/b2-repository-backup.yml` are similarly orchestration/evidence boundaries, not application runtime modules.

## Analysis rules

- Prefer canonical source over compatibility exports.
- Prefer focused tests over broad test-suite reading.
- Separate workflow state, source state, and runtime state.
- Do not infer missing behavior from file size or workflow length.
- Structural refactors require regression coverage and required checks.
- Package boundaries and compatibility exports are part of the public contract.
