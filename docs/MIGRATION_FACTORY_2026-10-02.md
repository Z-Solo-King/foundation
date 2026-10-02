# Migration Factory — CrossFire Execution Contract (2026-10-02)

The migration factory turns repository evidence into a repeatable inventory and disposition process. It does not transfer production authority.

## Six parallel lanes

1. runtime-frontier
2. dependency-frontier
3. tooling-ci
4. tests-benchmarks
5. target-language
6. retirement-readiness

Each lane scans the full tracked Python surface of both Foundation and the exact immutable Operations revision. The six lane outputs are independent evidence; aggregation checks completeness and coverage only.

## Trust boundary

The workflow is privileged because it reads the private Operations repository through a read-only GitHub App token. It is intentionally manual-dispatch only. No pull-request or untrusted trigger may execute private Operations checkout logic.

Foundation remains the sole GitHub Actions and deployment authority.

## Core rule

Every Python file receives exactly one disposition:

- MIGRATE
- RETAIN
- DELETE
- FOLLOW (tests/benchmarks)
- ARCHIVE
- REVIEW REQUIRED

No unclassified Python is allowed.

## Migration completion

A candidate must pass parity, runtime, security/policy/provenance, shadow, canary and rollback gates before authority transfer. Production consumer redirection and explicit authority-transfer evidence are required before leaving Python authority.

## AI CrossFire

AI can be attached as advisory evidence when credentials are available. AI output cannot promote code, override policy/security/provenance gates, or change authority. Disagreements become review findings and deterministic repository evidence remains canonical.

## Exit criteria

Migration is complete only when all production responsibilities have an explicit disposition, promoted consumers no longer route through Python, the bounded rollback-only period has expired, obsolete Python files/imports/packages/workflows are removed, verification follows the new production owner, and a fresh cross-repository scan reports zero unclassified Python.
