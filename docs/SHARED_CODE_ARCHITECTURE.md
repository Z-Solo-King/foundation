# Shared Code Architecture

## Family model

Audit, Monitor, and Extractor are one **mechanics family**, not one authority.

```text
Audit system ─────┐
Monitor system ───┤
Extractor system ─┤
                  └──> shared deterministic mechanics / contracts
                    \_> system-specific policy, authority and execution
```

The objective is to combine code when the semantics are genuinely identical, while trimming duplicate implementations and leaving unique behavior at the consumer boundary.

## Core rule

Do not copy identical mechanics into Audit, Monitor, Extractor, Planner, Benchmark, CrossFire, Automation, Runtime, or AI tools. Extract the mechanic once, then keep consumer-specific policy at the edge.

```text
Audit ────────────┐
Monitor ──────────┤
Extractor ────────┤
Planner ──────────┤──> Shared deterministic kernel / contracts
Benchmark ────────┤
CrossFire ────────┤
Automation ───────┤
Runtime adapters ─┘
```

## Four levels of reuse

1. Shared primitive code: hashing, canonical serialization, time parsing, freshness, bounded numeric values, filesystem/index helpers, evidence fingerprints.
2. Shared contracts: schemas, error taxonomy, receipt format, capability names, disposition states and test vectors.
3. Shared domain engines: provider runtime, AI task fabric, resource governance, mapper/extractor contracts and evidence reconciliation.
4. Shared orchestration: existing workflows, reusable actions and schedulers consume the engines; they do not duplicate their internals.

## Cross-language family rule

Source code does not need to be identical across TypeScript, Python, Rust or Go. The family boundary is established by:

- one semantic contract;
- one set of deterministic test vectors;
- equivalent normalized outputs;
- no duplicated authority.

A language-specific implementation is valid when there is a measured runtime or deployment reason. It must remain contract-equivalent and must not introduce a competing policy owner.

## Authority rule

A shared kernel may define mechanics but may not silently become policy authority. Provider eligibility stays in provider runtime; extraction policy stays in extractor contracts/strategies; audit authority stays in audit controls; monitoring remains read-only telemetry quality; deployment stays in canonical Actions; Cloudflare production state remains runtime evidence; AI remains advisory.

## Extraction decision table

| Situation | Action |
|---|---|
| Same algorithm, same inputs/outputs, same invariant | Extract shared mechanic |
| Same data shape, different meaning | Share schema/fixture only |
| Same mechanic, different policy/authority | Shared core + thin adapter |
| Different lifecycle/security boundary | Keep separate |
| One implementation only | Do not extract prematurely |
| Wrapper adds no invariant/boundary | Trim it |

## Family handoff

The preferred flow is:

`Extractor observation -> shared evidence mechanics -> Monitor/Audit consumers`

The shared layer should carry deterministic identity, timestamps, canonical serialization, digests and provenance metadata. It must not decide whether a finding is accepted, whether a site method is selected, or whether production state is healthy.

## Existing implementation

Foundation:
- `tools/evidence_kernel.mjs` provides shared deterministic primitives.
- Verification and observability audit consume the kernel.
- Multi-lens planning consumes bounded numeric primitives from the kernel.

Operations:
- `private/shared_evidence_kernel.py` provides the same mechanics for the Python runtime.
- Project observability, limitation refresh, provider runtime and extractor/mapper evidence consumers reuse it.
- Extractor observation, checkpoint state, resource envelopes and image observations now reuse canonical digest mechanics.

Cross-repo contract:
- share schemas and fixtures rather than importing private implementation across repositories;
- differential tests are the parity gate;
- policy and production authority stay with their canonical owners.

## Duplication cleanup rule

Before deleting or replacing a duplicate:

1. Identify every consumer.
2. Prove identical semantics, not merely identical names.
3. Compare edge cases and error behavior.
4. Add or reuse a common regression vector.
5. Switch consumers.
6. Re-scan for the old implementation.
7. Only then remove the duplicate.

This makes trimming monotonic: no consumer loses its invariant while the number of implementations decreases.

## Verification

Acceptance for consolidation requires deterministic focused tests, stable digest behavior, acyclic imports, explicit authority boundaries, and a clean duplicate scan for the targeted surface.

CrossFire / AI can review candidate equivalence and surface edge cases, but AI output is advisory. Deterministic tests and existing authority gates remain the acceptance criteria.

## Anti-patterns

- same invariant implemented independently in audit, monitor and extractor;
- same provider selection reimplemented in benchmark code;
- same freshness calculation in provider and limitation code;
- same canonical JSON/digest procedure in multiple evidence producers;
- wrappers that add no new invariant or boundary;
- multiple schedulers deciding the same maintenance job;
- cross-language rewrites promoted only because a benchmark or model preference is higher;
- deleting a duplicate before its consumers and parity vectors are identified.
