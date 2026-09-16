# AI Analysis Map

## Purpose

Compact routing index for human and AI repository analysis. Read this before opening large source, workflow, or historical documents.

## Repository evidence

- Repository: `Z-Solo-King/foundation`
- Current main revision at scan: `672d22d9bd205401596b923098f0405bb9fb600a`
- Full tracked-tree scan: recursive Git tree, `truncated=false`.

## Read-first order

1. `README.md`
2. `REPOSITORY_MAP.json`
3. `DEPLOYMENT.md` for deployment-contract questions
4. `docs/AI_AUDIT_AND_VERIFICATION_STANDARD.md` for audit questions
5. `docs/FAMILY_CONTRACT.json` for public contract questions
6. Then open the canonical implementation and focused tests.

## Production-code analysis

The public Foundation backend is intentionally split into small contract-oriented modules. Do not merge modules merely to reduce file count; package boundaries are part of the public contract.

Compatibility example: `backend/planner.py` is an explicit compatibility export for the canonical planner and is not a second implementation.

## High-analysis-cost workflow

`.github/workflows/nightly-multi-agent-research.yml` is a large orchestration file containing matrix lanes, preflight policy, artifact handling, validation, diagnosis, baseline comparison, attestation, and final gating.

Analysis rule: do not read this workflow wholesale for a narrow research question. Start with the specific job (`research`, `project-summary`, or `final-gate`) and then follow the invoked `benchmark.multi_agent.*` module. The workflow is orchestration authority; research logic belongs in the benchmark package.

A future split is justified only when job boundaries can be separated without changing artifact/dependency semantics. Do not split solely to reduce YAML size.

## Other workflow hotspots

- `.github/workflows/codeql.yml` — security-analysis orchestration; read only for CI/security questions.
- `.github/workflows/autonomous-benchmark.yml` — benchmark orchestration; follow the invoked benchmark module first.
- `.github/workflows/b2-repository-backup.yml` — backup/deployment evidence; do not treat it as application runtime code.

## Historical/documentation routing

Historical audit, decision, handoff, benchmark, and deployment records are evidence records, not implementation authority. For narrow questions, use the current source-of-truth document and canonical source first.

## Analysis rules

- Prefer canonical source over compatibility exports.
- Prefer focused tests over broad test-suite reading.
- Separate workflow state, source state, and runtime state.
- Do not infer missing behavior from file size or workflow length.
- Do not delete package markers or compatibility exports solely because they are small.
- Structural refactors require regression coverage and required checks.
