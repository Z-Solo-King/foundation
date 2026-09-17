# Family Synchronization Reconciliation — 2026-09-17

**Status:** CURRENT audit record (L2; CI/runtime evidence remains separate).

## Purpose

This record reconciles the current GitHub repository state with older project plans and handoff documents from the AI ChatBot / Heroic AI / Research Intelligence Engine work.

## Canonical family boundary

The current GitHub family boundary is **two active repositories**:

- `Z-Solo-King/foundation` — public-safe contracts, deterministic/evidence core, public Worker, CI, deployment and backup workflow.
- `Z-Solo-King/operations` — private Heroic AI control plane/runtime, protected policy/resource authority, provider governance, private orchestration, memory, evaluation, promotion and recovery.

The previously referenced standalone `extractor-mapper` repository is historical context and is not part of the current active two-repository synchronization boundary.

## Current observed branch tips

- Foundation `main`: `9cba8b4c911cc1e6a2dbb3388435fddf6bc9521c`
- Operations `main`: `9058acdc304c867332b21f945b7922d43888a759`
- Approved production Operations revision remains separately identified as `cf28a28cb40de527aff1cd87f96e103669635f70` until a newer approved production revision is established through the production owner.

These SHAs are audit observations, not aliases for future branch tips.

## Synchronization findings

1. Older Final Plan / Status Handoff documents remain useful for architectural intent, but their dated repository SHAs and three-repository wording must not override current source.
2. Foundation `docs/FAMILY_SYNC_STANDARD.md` remains the normative synchronization format and evidence hierarchy.
3. Foundation `docs/FAMILY_SYNC_STATE.json` remains the machine-readable family snapshot and must be updated through the protected PR/check path.
4. Current GitHub issue/PR state is authoritative over copied counts in older handoffs.
5. Open PRs are proposed until merged. A merged implementation is `CURRENT`; CI execution is L3; approved private/production runtime is L4.
6. No GitHub repository document may claim Cloudflare/B2/private-runtime production truth from source inspection or repository CI alone.

## Current implementation coordination

### Public admission/security

Foundation PR `#484` is the current implementation stream for the concrete public-boundary hardening: auth fail-closed behavior, client `system` history rejection, finite request ceilings, JSON representation admission and public exception-boundary controls. Earlier PRs `#460` and `#483` were closed after the implementation was rebuilt directly on current `main` to avoid stale branch lineage.

### Source URL security

Foundation PR `#482` merged to `main` after its required workflows passed. The implementation canonicalizes security-neutral URL variants, rejects unsafe URL forms, revalidates redirect destinations and prevents HTTPS-to-HTTP downgrade redirects.

### Stage receipt correctness

Foundation PR `#461` remains a separate implementation stream for stage-receipt expiry and cumulative resource-chain validation. It does not create a second ResourceLedger authority.

### Provider-output admission

The Operations provider-response admission implementation is merged. Remaining structural fan-out, streaming, deadline, retry, concurrency and runtime-evidence requirements remain under their existing Operations contracts.

## Runtime/evidence gates

Repository implementation work remains separate from external runtime gates for chat, streaming, replay/idempotency, resource accounting, memory/feedback persistence, scheduler activation, cross-repository bridge execution, production deployment, B2 recovery and GitHub administration-only controls.

## Uniform vocabulary

Use only these lifecycle/evidence states where applicable:

- `CURRENT`
- `PROPOSED`
- `VERIFIED`
- `BLOCKED`
- `DEFERRED`
- `HISTORICAL`
- `SUPERSEDED`
- `REMOVED`

Evidence levels:

- `L0` hypothesis
- `L1` source inspected
- `L2` repository inspection including callers/tests/ownership
- `L3` current GitHub Actions execution
- `L4` approved runtime/production execution

## Rules for future AI sessions

1. Read `docs/FAMILY_SYNC_STANDARD.md`, `docs/FAMILY_SYNC_STATE.json`, current source-of-truth documents and repository READMEs first.
2. Read current `main` before relying on any dated plan, handoff or chat transcript.
3. Never recreate a capability, policy, resource ledger, evaluation authority, memory authority, provider authority or deployment owner that already exists.
4. Group closely related issues into substantive implementation PRs; do not create documentation-only duplicates when an existing contract already covers the scope.
5. Never create empty/mechanical PRs or branches merely to represent planning.
6. Do not close issues solely to reduce the visible queue. Close only on acceptance, supersession, duplication or an explicit durable disposition.
7. Keep Foundation public and Operations private. Do not move secrets, private policy, private evaluation data or private runtime ownership into Foundation.
8. Keep the strict $0/no-paid-fallback policy as a hard gate. Unknown billing/quota state must not be treated as permission to spend.
9. Preserve the distinction between repository correctness and L3/L4 execution evidence.
10. When a current-state fact changes, update the canonical source-of-truth and family sync record through the normal protected PR/check path.

## Known lessons from this workstream

- A passing local test is not a GitHub CI acceptance result.
- A configured coverage gate is not a 100% execution claim until CI runs and passes it.
- Source existence is not runtime/production evidence.
- Search returning zero results is a lead, not proof that code or a reference does not exist.
- Provider lists and quotas must not be hardcoded as current truth when live eligibility is required.
- Compatibility facades must delegate; they must not become parallel business implementations.
- Public request fields, provider output, retrieved content, tool output, memory and feedback are untrusted or candidate data unless an explicit canonical authority says otherwise.
- CI failures are regression boundaries; do not weaken tests or restore dead compatibility code simply to make a diff green.
- When a requirement is already represented by a coherent implementation PR, add missing implementation/tests to that stream instead of spawning another duplicate PR.
