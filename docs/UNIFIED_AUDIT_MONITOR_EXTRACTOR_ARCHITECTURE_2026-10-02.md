# Unified Audit / Monitor / Extractor Architecture — 2026-10-02

## Purpose

Audit, Monitor and Extractor are capabilities, not three competing copies of one system.

`Audit / Monitor / Extractor -> Family Common Core -> domain adapters / unique behavior`

The common core is deliberately small: deterministic, public-safe primitives whose semantics are identical across consumers. It is not an orchestration layer.

## Ownership

- Foundation owns public-safe deterministic primitives and public contracts.
- Operations owns private audit interpretation, monitoring policy/state, acquisition/extraction strategy, provider/resource/security/promotion policy and runtime orchestration.
- Operations may consume Foundation through the pinned public core and compatibility facades.
- Foundation must not import Operations private implementation.

## Common-core admission test

A helper enters the common core only when semantics, input/output contracts and behavior are equivalent; no domain-specific policy or trust decision is hidden inside it; callers can migrate without behavior change; and focused regression/golden-vector coverage exists.

Name similarity, AI similarity, or repeated code shape is not sufficient.

## Capability layers

### Audit
Discovers, compares, classifies and produces evidence. Interpretation, authority decisions and retirement gates remain domain-specific.

### Monitor
Observes runtime/production state, freshness, health, resource/provider state and drift. Observation primitives may be shared; monitoring policy and alert semantics remain private.

### Extractor
Acquires and transforms external source material. Acquisition policy, parser strategy, transport/site behavior, stopping rules and evidence promotion remain private.

### Shared core
May provide hashing, canonical serialization, stable de-duplication, normalization, identity primitives and typed outcomes when equivalence is proven.

## Prohibited convergence

Do not merge Audit, Monitor and Extractor into one giant service/module merely because they produce evidence. Their inputs, failure modes, security boundaries and lifecycles differ.

Do not duplicate private policy into Foundation for convenience, and do not create a second common layer when an existing Foundation primitive already owns the behavior.

## Branch/history interpretation

The approximately 2.7k historical branches are evidence, not 2.7k active systems. Classify them separately from source-code capabilities:

- exact same-tip -> duplicate-reference candidate;
- tip contained in main -> merged-redundancy candidate;
- active PR/protected/tag/release/live reference -> retain;
- diverged with unique behavior -> semantic review;
- historical evidence only -> archive/retire after reference checks.

Discovery is parallel; mutation/retirement is serialized and fail-closed.

## Completion invariant

Every active behavior has one canonical owner. Every shared primitive has an explicit consumer list. Every compatibility facade points to its owner. Every historical branch has a documented disposition. No consolidation is accepted solely because two names look similar.
