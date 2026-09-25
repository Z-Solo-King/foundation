# AI / Agent Benchmark Standard — 2026-09-25

## Purpose

Provide one reproducible evaluation contract for the coding models and agent roles used by the Heroic AI engineering workflow. The benchmark measures observable engineering behavior; it never grants security, policy, resource, provenance, runtime, or deployment authority.

## Audit-derived six lanes

| Lane | Focus | Example lenses |
|---|---|---|
| L1 | semantic state, concurrency, retry, recovery | Python, JavaScript, Java, Kotlin |
| L2 | edge transport and contracts | TypeScript, JavaScript, C#, PHP |
| L3 | native concurrency and unsafe surfaces | Rust, Go, C/C++, Zig |
| L4 | governance, evidence, provenance, document synchronization | Python, YAML, JSON, Markdown |
| L5 | cross-model, agent, and tool portability | model-neutral/tool-neutral |
| L6 | benchmark reproducibility and artifact integrity | Python, JSON, YAML |

These lanes reuse the existing audit methodology: vary language, component, evidence mode, and risk class rather than repeating the same test under different names.

## Agent tree

The benchmark can run the same task through `main`, `explorer`, `worker`, `researcher`, and `advisor` roles. Role selection changes the observable workflow, not the acceptance contract.

## Model comparison

Every model/provider must receive the same task ID, requirements, tool policy, fixture version, repository revision, and acceptance rules. Record observations rather than hidden reasoning. Use at least three repeated runs per task/model before treating a behavioral difference as stable.

Measure correctness, evidence quality, completeness, precision, token efficiency, tool efficiency, context efficiency, and self-correction. Keep component metrics visible rather than reducing decisions to a single number.

## Audit methods reused

Apply differential testing against the reference behavior, metamorphic checks, schedule exploration, fault injection before/after side effects, late-output testing, bounded resource fuzzing, schema/version drift checks, artifact parity, negative security corpora, stale-pin detection, and contradiction scans.

## Promotion and learning

A benchmark observation is not a production finding. Reproduce important findings independently against repository/runtime evidence before changing code, issue state, architecture, or deployment configuration. Convert verified improvements into regression tasks and keep the task corpus versioned.

## Artifact contract

A run should retain run ID, provider/model, agent role, lane, language lens, task/fixture version, repository revision, tool-policy version, evidence tier, observable outcome metrics, and artifact digest/provenance. Missing measurements are explicit gaps, never inferred as zero.
