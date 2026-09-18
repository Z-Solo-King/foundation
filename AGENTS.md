# AI / Maintainer Engineering Guidance

Read these before architecture or cross-repository changes:
1. `docs/MAINTENANCE_CONTRACT.md`
1. `REPOSITORY_MAP.json`
2. `docs/FAMILY_CONTRACT.json`
3. `docs/MAINTENANCE_CONTRACT.md`
4. relevant public contract/test files
5. Operations `docs/AGENT_MAINTENANCE_GUIDE.md` when working across the family

Live `main` and fresh execution evidence outrank dated notes.

## Ownership

Foundation owns public-safe contracts, deterministic observed-data/research primitives, frontend/public API, public CI, and canonical production deployment/backup.

Operations owns protected policy/resource authority, private acquisition/execution, provider/runtime selection, evaluation, promotion/rollback/recovery, memory, and chatbot control.

Foundation never imports Operations private implementation or credentials. Operations consumes Foundation public contracts rather than copied algorithms.

The retired `Z-Solo-King/extractor-mapper` repository is historical; active extractor/mapping lives in private Operations.

## Canonical-owner rule

Before adding behavior:
- search both active repositories and active PRs;
- identify the canonical owner;
- inspect callers/tests/side effects;
- extend that owner instead of creating a duplicate.

Compatibility modules may preserve supported imports, but cannot become a second business-logic authority.

## Public-boundary rules

Keep Foundation free of:
- private credentials/secrets;
- protected policy/provider/resource logic;
- private runtime topology;
- private evaluation holdouts;
- promotion/rollback authority.

Unknown, blocked, stale, partial, contradictory, rejected, and unavailable states must remain explicit. Do not turn transport failure or missing evidence into successful empty data.

## Code structure

Prefer cohesive modules with stable responsibility boundaries.

Split a module when responsibility, trust boundary, caller surface, and import boundary are clear. Do not split solely because of line count.

Group related code where it reduces navigation and duplicate ownership without creating another abstraction layer.

## Evidence

Use:
`L0 hypothesis -> L1 source -> L2 repository -> L3 CI/control-plane -> L4 approved runtime/production`

Source inspection, green tests, merge status, workflow definitions, and deployment intent are not production certification.

## GitHub Actions

Foundation is the sole family GitHub Actions and canonical production-deployment owner.

Operations must not gain `.github/workflows/` or a competing deployment path.

Do not manually dispatch or rerun privileged workflows during maintenance unless explicitly required and authorized.

## Validation

Use the cheapest proving layer first:
`contract -> focused test -> integration -> CI -> approved runtime`

Add focused owner-level and adversarial tests for behavior changes. Never weaken boundary, provenance, security, cost, or fail-closed checks just to make validation green.

## Documentation

Public documentation must remain public-safe. Private operational methodology, protected runtime state, secret material, and exploratory/private future knowledge belong in Operations.

When a rule or contract is consolidated, remove redundant copies rather than preserving parallel authorities. Do not create model-specific guidance, chat-limit handoffs, duplicate architecture maps, or parallel governance/knowledge standards.
