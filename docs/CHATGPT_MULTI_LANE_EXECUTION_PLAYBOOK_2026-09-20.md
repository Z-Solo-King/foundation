# ChatGPT Multi-Lane Execution Playbook — 2026-09-20

This document defines how a ChatGPT session should operate this repository when migration and maintenance work are both active.

## Goal

Optimize for trustworthy progress, not raw parallel task count.

The desired execution properties are:

**adaptive, flexible, hybrid, efficient, effective, logically correct, stable, uniform, diverse, explainable and structurally reproducible.**

## Four-lane model

Use up to four independent reasoning lanes.

Default under heavy migration load:

1. Migration implementation.
2. Migration differential/security/performance evidence.
3. Migration integration/toolchain/benchmark automation.
4. Runtime/control-plane/production acceptance.

This is a scheduler default, not a permanent assignment.

## Adaptive reallocation

Increase migration capacity when:

- migration backlog is large;
- candidate work is unblocked;
- acceptance queues are thin;
- collisions are low.

Increase acceptance capacity when:

- production/control-plane is failing;
- a release gate is red;
- secrets/bindings/dispatch/authentication are the actual blocker;
- runtime evidence is available and ready to collect.

Reduce parallel mutation capacity when:

- two lanes approach the same file surface;
- duplicate PRs appear;
- stale branches accumulate;
- repeated merge conflicts occur.

Never leave a lane idle simply because another lane is waiting on CI.

## Uniformity layer

Every lane reports:

- issue/PR;
- canonical owner;
- exact revision;
- file surface;
- acceptance rung;
- evidence mode;
- result;
- blocker;
- next safe action.

Every candidate uses the same core promotion ladder:

`implemented -> tested -> CI_green -> integration_verified -> runtime_verified -> production_certified`

## Diversity layer

When three or four lanes are active, intentionally diversify:

- Rust + TypeScript + Go + Python reference;
- unit + differential + adversarial + performance/security;
- low-risk leaf + integration boundary + acceptance gate.

Do not make diversity cosmetic. Each lane should answer a materially different question.

## Language-security layer

### Python
Protect policy, governance, provenance, replay/idempotency, resource accounting and semantic authority.

### TypeScript
Apply Worker/browser Web-API constraints, XSS/output escaping, origin validation, AbortSignal/cancellation and no Node-only Worker assumptions.

### Rust
Keep deterministic kernels pure, bounded and side-effect-free by default. `unsafe` requires explicit review and threat-model evidence.

### Go
Bound goroutines, retries, queues, connections and response bodies. Use context cancellation/deadlines. Do not embed policy in global concurrency code.

### Other runtimes
Use explicit ecosystem/service/FFI/security rules from the Operations language-governance policy before introducing them.

## Mutation discipline

Read-only work may be parallel.

Branch creation, writes, issue state changes, PR creation, merges and deployment mutations are serialized.

Before mutation:

- refresh the relevant main ref;
- search active PRs for overlap;
- verify exact file ownership;
- choose the smallest reversible slice.

## Failure discipline

Classify every failure as:

- candidate code defect;
- test defect;
- evidence harness defect;
- dependency/toolchain defect;
- control-plane defect;
- runtime defect;
- external dependency;
- stale/duplicate work.

Fix shared root causes once. Do not patch 20 identical jobs individually.

## Session continuity

A new ChatGPT session must be able to resume from GitHub alone.

Therefore, after meaningful work, leave:

- exact commit/PR;
- acceptance rung;
- tests;
- remaining evidence;
- external blocker;
- canonical owner;
- next recommended lane action

in repository metadata.

## Completion criterion

Do not stop because the migration branch is large.

Continue until the actionable queue is exhausted or the remaining work is genuinely runtime/external/blocked, duplicate/superseded, or otherwise requires evidence unavailable to the repository tooling.
