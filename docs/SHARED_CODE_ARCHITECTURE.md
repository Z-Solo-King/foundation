# Shared Code Architecture

## Core rule

Do not copy identical mechanics into Audit, Monitor, Planner, Benchmark, CrossFire, Automation, Runtime, or AI tools. Extract the mechanic once, then keep consumer-specific policy at the edge.

```text
Audit system  ─────┐
Monitor system ────┤
Planner system ────┤──> Shared deterministic kernel
Benchmark ─────────┤
CrossFire ─────────┤
Automation ────────┤
Runtime adapters ──┘
```

## Four levels of reuse

1. Shared primitive code: hashing, canonical serialization, time parsing, freshness, bounded numeric values, filesystem/index helpers, evidence fingerprints.
2. Shared contracts: schemas, error taxonomy, receipt format, capability names, disposition states and test vectors.
3. Shared domain engines: provider runtime, AI task fabric, resource governance, mapper/extractor contracts and evidence reconciliation.
4. Shared orchestration: existing workflows, reusable actions and schedulers consume the engines; they do not duplicate their internals.

## Cross-language rule

Do not force one language implementation to serve every runtime. Share the contract and fixtures. Implement the same contract natively in TypeScript, Python, Rust or Go when a measured runtime reason exists. Differential tests compare normalized outputs against the shared vectors.

## Authority rule

A shared kernel may define mechanics but may not silently become policy authority. Provider eligibility stays in provider runtime; policy stays in protected policy; deployment stays in canonical Actions; Cloudflare production state remains runtime evidence; AI remains advisory.

## Extraction test

A candidate function belongs in a shared kernel when at least two independent consumers need identical semantics and changing the function should imply the same correctness test for both. Do not extract merely because names look similar.

## Consolidation targets

Current first wave:
- Foundation: `tools/evidence_kernel.mjs` shared by verification, observability audit and multi-lens planner.
- Operations: `private/shared_evidence_kernel.py` shared by project observability, limitation refresh and provider runtime.
- Operations provider runtime remains the common provider selection mechanism for chatbot/task-fabric/CrossFire callers.
- AI task fabric remains the common AI execution surface for research, extraction assistance, audit assistance, scan triage, action planning, workflow assistance and Cloudflare diagnostics.

Later waves should migrate workflow boilerplate to reusable actions only where the permissions, secrets and failure semantics are identical.

## Anti-patterns

- same invariant implemented independently in audit and monitor;
- same provider selection reimplemented in benchmark code;
- same freshness calculation in provider and limitation code;
- same canonical JSON/digest procedure in multiple evidence producers;
- wrappers that add no new invariant or boundary;
- multiple schedulers deciding the same maintenance job;
- language rewrites promoted only because a benchmark or score is higher.
