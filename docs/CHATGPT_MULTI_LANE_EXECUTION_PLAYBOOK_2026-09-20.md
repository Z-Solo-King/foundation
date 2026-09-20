# ChatGPT Multi-Lane Execution Playbook — 2026-09-20

## Goal

Optimize for trustworthy progress rather than raw parallel task count.

Desired properties:

**adaptive, flexible, hybrid, efficient, effective, logically correct, stable, uniform, diverse, explainable and structurally reproducible.**

## Four-lane model

Use up to four independent reasoning lanes.

Default under heavy migration load:

1. Migration implementation/build.
2. Migration differential/security/performance evidence.
3. Migration integration/toolchain/benchmark automation.
4. Runtime/control-plane/production acceptance.

This is a scheduler default, not a permanent assignment.

## Adaptive reallocation

Increase migration capacity when migration backlog is high, candidate work is unblocked, acceptance queues are thin, and collisions are low.

Increase acceptance capacity when production/control-plane is failing, a release gate is red, or runtime evidence is ready.

Reduce mutation parallelism when two lanes approach the same file surface, duplicate PRs appear, stale branches accumulate, or merge conflicts repeat.

Never leave a lane idle solely because another lane is waiting on CI.

## Uniformity

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

Every candidate uses:

`implemented -> tested -> CI_green -> integration_verified -> runtime_verified -> production_certified`

## Diversity

With three or four active lanes, intentionally vary:

- language;
- component surface;
- evidence mode;
- risk class.

Prefer materially different questions, such as:

- Rust deterministic kernel;
- TypeScript edge/browser contract;
- Go concurrency benchmark;
- Python reference/security/provenance check.

Do not count copies of the same benchmark as diversity.

## Language-security layer

Python protects policy, governance, provenance, replay/idempotency, resource accounting and semantic authority.

TypeScript must follow Worker/browser Web-API constraints, XSS/output escaping, origin validation, AbortSignal/cancellation and no Node-only Worker assumptions.

Rust deterministic kernels are pure and bounded by default; `unsafe` requires explicit review and threat-model evidence.

Go bounds goroutines, retries, queues, connections and response bodies and requires context cancellation/deadlines.

Other runtimes use the explicit ecosystem/service/FFI rules in the Operations language-governance policy before introduction.

## Mutation discipline

Parallelize reads and independent evidence.

Serialize:

- branch creation;
- file writes;
- issue state changes;
- PR creation;
- merges;
- deployments.

Before mutation:

- refresh main;
- search active PR overlap;
- verify canonical owner;
- verify exact file surface;
- choose the smallest reversible slice.

## Failure routing

Classify failures as candidate code, test, evidence harness, dependency/toolchain, control-plane, runtime, external dependency, or stale/duplicate work.

Fix shared root causes once. Never patch identical matrix jobs individually.

## Session continuity

A new ChatGPT session must be able to resume from GitHub alone.

Leave exact:

- commit/PR;
- acceptance rung;
- tests;
- remaining evidence;
- external blocker;
- canonical owner;
- next lane action.

## Completion

Continue until actionable repository work is exhausted. Leave genuine runtime/external blockers open with precise evidence recipes rather than inventing completion.
