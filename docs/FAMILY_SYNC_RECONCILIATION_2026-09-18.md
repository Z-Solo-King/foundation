# Family Synchronization Reconciliation — 2026-09-18

**Status:** CURRENT audit record (L2; CI/runtime evidence remains separate).

## Canonical family boundary

The active GitHub family contains two repositories:

- `Z-Solo-King/foundation` — public-safe contracts, deterministic/evidence core, public Worker, CI, deployment and backup workflow.
- `Z-Solo-King/operations` — private control plane/runtime, protected policy/resource authority, provider governance, private orchestration, memory, evaluation, promotion and recovery.

The standalone extractor/mapper repository is historical context and is not part of the active family boundary.

## Current observed branch tips

- Foundation `main`: `88e16810febede7e0d7fa663638794e10d213712`
- Operations `main`: `532b90ecfe7a876b4477ab8cb2097b18bcf62b70`
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

### Nightly Operations pin repair

Foundation PR #491 merged to `main`. The canonical pin-repair workflow now targets the current audited Operations main revision. This does not itself prove that the private nightly runtime has executed that revision.

### Zero-cost provider gate

Operations PRs #392, #393 and #394 merged the hard $0/no-paid-fallback admission path into the canonical provider selector, dynamic quota policy, public chat runtime state adapter and private research runtime state adapter. Operations issue #353 is completed.

### Provider-output admission

Operations PR #395 merged one canonical bounded provider-output normalizer used by both chatbot and private research execution. It rejects oversized, malformed, partial/truncated, identity-mismatched, structured/tool-call and invalid-usage output before downstream interpretation.

### Provider-derived fan-out limits

Operations PR #396 merged the structural-amplification layer for private research output: bounded JSON depth/collection width, bounded findings/follow-up counts and deterministic duplicate coalescing. Tool-dispatch, streaming and broader parent-budget integration remain separate governed contracts.

### Durable recovery accounting

Operations PR #398 merged an idempotency correction for durable reservation recovery. Consume/release now report whether the current transition actually won, and expired-reservation reconciliation counts actual releases only.

### Deadline, immutable identity and lease-recovery bundle

Operations PR #402 merged as `532b90ecfe7a876b4477ab8cb2097b18bcf62b70`. It is the consolidated repository implementation for Operations issues #377, #383 and #384: one monotonic parent deadline now propagates through multi-agent scheduling/phases/agents, governed research providers, model-call governance, HTTP timeout and retry backoff; immutable decision snapshots remain enforced at protected execution; durable reservations carry execution identity through the existing idempotency-key authority; lease duration is capped by parent remaining time; late consumption is rejected; identity-bound heartbeat and recovery are implemented; and adversarial regression coverage was added.

The three issues remain open pending explicit acceptance/CI evidence. The merge does not claim Cloudflare/private-runtime/L4 production certification.

### Stage receipt correctness

Foundation PR #461 remains a separate implementation stream for stage-receipt expiry and cumulative resource-chain validation. It does not create a second ResourceLedger authority.

### Nightly timeout gate

Foundation issue #487 remains open. The nightly research lane still uses the six-hour ceiling and requires a lower timeout while preserving its existing authentication, live preflight, lane coverage, artifact, attestation, diagnosis and final-gate semantics.

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
