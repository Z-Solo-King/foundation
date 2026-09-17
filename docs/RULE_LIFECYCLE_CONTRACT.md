# Normative Rule Lifecycle Contract

**Status:** Canonical family governance contract
**Owner:** Foundation family governance

Every normative rule must be traceable as:

`rule -> class -> canonical owner -> enforcement point -> callers -> regression -> evidence tier -> runtime gate -> exception/retirement`

## Rule classes

- product/runtime invariant
- security/privacy invariant
- economic/resource invariant
- provenance/evidence invariant
- maintainability/process rule
- validation/evidence gate
- operator/tooling guidance

A policy document is not enforcement. Machine-enforced, test-enforced, documentation-only and externally verified are separate dispositions. Duplicate authorities are prohibited unless one is an explicitly delegating compatibility facade.

## State composition

Aggregate state is derived only from checks actually executed. Missing execution is `UNKNOWN` or `NOT_ATTEMPTED`, never implicit success. Retained successful work plus failed work is `PARTIAL` when the operation contract permits partial completion. Structural validity, capability, readiness and resumability are separate dimensions.

Error handling must preserve the original failure and must not manufacture a healthy secondary state. Search/index results are evidence leads, not proof of absence. Historical documentation cannot outrank current repository state.

## Evidence discipline

The family evidence contract is `docs/EVIDENCE_VALIDATION_CONTRACT.md`. Source/test evidence cannot be promoted to runtime/production truth. External/admin-only gates remain explicit.
