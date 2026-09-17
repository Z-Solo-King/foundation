# Family Synchronization Reconciliation — 2026-09-18

**Status:** CURRENT audit record (L2; CI/runtime evidence remains separate).

## Canonical family boundary

The active GitHub family contains two repositories:

- `Z-Solo-King/foundation` — public-safe contracts, deterministic/evidence core, public Worker, CI, deployment and backup workflow.
- `Z-Solo-King/operations` — private control plane/runtime, protected policy/resource authority, provider governance, private orchestration, memory, evaluation, promotion and recovery.

The standalone extractor/mapper repository is historical context and is not part of the active family boundary.

## Current observed branch tips

- Foundation `main`: `d31db88f65dc923e3cdf861fd0087beffbf21045`
- Operations `main`: `10272e8d1c3a2a786143d59f246c19737337e1df`
- Approved Operations production revision: `cf28a28cb40de527aff1cd87f96e103669635f70`
- Nightly Operations revision: `b6a519742e57e7e68db64ab10535d76372bcbdb1`

These SHAs are audit observations, not aliases for future branch tips. Production revision remains separate from Operations `main`.

## Recent GitHub implementation state

### Public admission/security

Foundation PR #484 merged to `main` after both required checks passed. The implementation enforces fail-closed production authentication, explicit development-only bypass, JSON content-type/body admission, bounded JSON structure, finite research/chat request limits, safe history roles and bounded metadata/history fields.

### Source URL security

Foundation PR #482 merged to `main` with required CI green. URL canonicalization, unsafe destination rejection, redirect revalidation and HTTPS-to-HTTP downgrade protection remain in the public source-fetch boundary.

### Execution identity

Foundation PR #488 merged to `main` after being rebuilt from the post-#484 base. The contract defines deterministic identity inputs and explicitly prevents identity from becoming an authorization, resource, evidence or publication authority.

### Stage receipt correctness

Foundation PR #461 remains a separate implementation stream for stage-receipt expiry and cumulative resource-chain validation. It does not create a second ResourceLedger authority.

### Nightly Operations pin

Foundation PR #486 remains open and stale against the latest Foundation `main`; its one-line pin update is still pending protected-check acceptance. Foundation issue #487 tracks the separate requirement to keep the nightly research lane timeout below the six-hour GitHub Actions ceiling.

## Evidence boundary

- `L0` — hypothesis
- `L1` — source inspected
- `L2` — repository inspection including callers/tests/ownership
- `L3` — current GitHub Actions execution
- `L4` — approved runtime/production execution

GitHub source and CI evidence do not establish Cloudflare, B2, private runtime or production truth.

## Rules

1. Current merged source and current GitHub checks outrank dated plans and copied issue summaries.
2. Open PRs are proposed until merged.
3. Do not recreate an existing authority for identity, policy, resources, evidence, evaluation, provider eligibility or publication.
4. Keep Foundation public and Operations private.
5. Keep the strict zero-cost/no-paid-fallback policy fail-closed.
6. Group related requirements into coherent implementation streams rather than multiplying duplicate PRs.
7. Close issues only when their stated acceptance is actually satisfied or they are explicitly superseded/duplicated.
8. Do not infer L4 runtime state from L1/L2/L3 evidence.
