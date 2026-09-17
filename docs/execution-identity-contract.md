# Canonical Execution Identity Contract

Status: proposed contract for Heroic AI execution identity
Version: `execution-identity/v1`
Related: #391

## Purpose

Heroic AI has several legitimate consumers of execution identity: research idempotency, replay/checkpoint validation, cache/coalescing, evaluation grouping, provenance and diagnostics. They must agree on what constitutes the same execution without creating a second identity, policy, resource, or evidence authority.

The contract below defines the **identity inputs**. It does not authorize a request, allocate resources, select a provider, or publish evidence.

## Identity-bearing fields

An implementation may serialize these fields into a canonical object when they materially affect execution correctness:

```json
{
  "contract": "execution-identity/v1",
  "request": "<normalized request semantics>",
  "capability": "<canonical capability id>",
  "execution_mode": "<canonical execution mode>",
  "policy_version": "<policy revision>",
  "schema_version": "<input/output schema revision>",
  "freshness_class": "<required freshness semantics>",
  "tool_inputs": "<canonicalized correctness-relevant tool parameters>",
  "source_inputs": "<canonicalized correctness-relevant source parameters>",
  "provider_config": "<provider/model config identity when output-relevant>",
  "research_plan": "<research-plan identity when applicable>"
}
```

Fields that are not relevant to correctness should remain diagnostic metadata rather than identity inputs. Timestamps, request IDs, trace IDs, log sampling decisions and presentation-only formatting must not make equivalent executions appear different.

## Canonicalization rules

1. Normalize field names and schema representation before hashing.
2. Serialize object keys deterministically.
3. Preserve semantically meaningful ordering only where ordering changes execution.
4. Normalize equivalent scalar representations according to the owning contract; do not invent semantic equivalence globally.
5. Omit absent optional fields consistently rather than mixing `null`, empty strings and missing keys without a contract rule.
6. Never hash secrets, credentials, authorization tokens or unnecessary raw private content.
7. Use a cryptographic digest of the canonical representation; the digest is an identifier, not proof of authorization or truth.

## Reuse rules

### Idempotency

An idempotency implementation may use the execution identity to detect an equivalent request, but it must still apply the existing authenticated request and lifecycle rules. A matching identity does not grant access.

### Cache and request coalescing

Reuse is valid only when authorization scope, freshness requirements, policy revision and all correctness-bearing inputs are compatible. A cache hit or coalesced execution must not bypass current authorization or resource admission.

### Replay/checkpoint

A checkpoint is reusable only when its identity and all owner-defined resume conditions match. A matching fingerprint must not reset deadlines, resource budgets, freshness requirements or security state.

### Evaluation

Evaluation may group equivalent executions using the identity, but benchmark/corpus/oracle binding remains the responsibility of the existing evaluation authority. Identity alone never makes an execution a passing evaluation result.

### Provenance

Artifact manifests may record the execution identity alongside source/evidence/provider/version metadata. The identity provides reproducible correlation; it does not replace provenance details.

## Explicit non-goals

This contract must not become:

- an authorization mechanism;
- a policy authority;
- a resource/quota ledger;
- a memory authority;
- an evidence-quality authority;
- a provider-selection authority;
- a publication gate;
- a replacement for existing idempotency, replay, cache, evaluation or provenance implementations.

## Invalidation boundaries

A reuse path must be invalidated or bypassed when a correctness-bearing input changes, including as applicable:

- policy revision;
- schema revision;
- capability contract;
- required freshness semantics;
- tool/source parameters;
- provider/model configuration that changes output behavior;
- research-plan semantics;
- authorization context where the owner requires isolation.

Resource budget consumption itself should not normally define semantic execution identity. A retry/resume must continue to account against the original parent budget even when it retains the same identity.

## Privacy boundary

The canonical input should prefer stable identifiers and digests over raw content. If a request contains sensitive content that is necessary to distinguish executions, use an approved privacy-preserving digest mechanism owned by the appropriate runtime boundary. Do not place raw user content in logs merely to explain identity decisions.

## Determinism requirements

For a fixed contract version and identical identity-bearing normalized inputs, canonical serialization and digest generation must be stable across processes and supported runtimes. Equivalent presentation-only differences must not change the identity.

The implementation must include explicit negative fixtures proving that materially different freshness, policy, capability, source, tool or provider inputs do change the identity.

## Relationship to existing architecture

Foundation owns the public-safe contract and deterministic normalization rules. Operations remains authoritative for protected policy, resource accounting, private runtime authorization and provider eligibility. The execution identity is a shared correlation primitive, not a new cross-repository authority.

## Acceptance checklist

- [ ] Canonical serialization is deterministic.
- [ ] Identity-bearing versus diagnostic-only fields are documented.
- [ ] Secrets and unnecessary raw private content are excluded.
- [ ] Policy/schema/capability/freshness changes invalidate incompatible reuse.
- [ ] Idempotency, cache/coalescing, replay, evaluation and provenance consumers use the same contract without duplicating authority.
- [ ] Collision/near-collision and semantic-difference fixtures exist.
- [ ] Equivalent executions remain comparable across process boundaries.
- [ ] Documentation explicitly distinguishes identity from authorization, resource accounting and evidence truth.
