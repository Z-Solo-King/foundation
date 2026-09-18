# AI / Maintainer Engineering Guidance

Read `REPOSITORY_MAP.json`, `docs/FAMILY_CONTRACT.json`, and `docs/FAMILY_ARCHITECTURE.md` before architecture or cross-repository changes.

## Ownership

Foundation owns public-safe contracts, deterministic research/evidence primitives, planning, the public Worker/API boundary, canonical public CI, and production deployment/backup ownership.

Operations owns protected policy, resource governance, private acquisition/execution, provider/runtime selection, evaluation, promotion, rollback, recovery, private runtime orchestration, and chatbot control.

Dependency direction is:

`foundation public contract/core -> operations consumer/control plane`

Never import Operations source, private credentials, private runtime state, or protected implementation into Foundation.

## Canonical-owner rule

Before writing code, search both active repositories and active PRs for an existing implementation. Identify the canonical owner first.

Extend the canonical owner. Do not create a second implementation of the same behavior, policy, registry, state model, result semantics, resource ledger, evaluator, promotion authority, trust boundary, or deployment authority.

Compatibility facades are allowed only to preserve supported legacy imports; they must not contain competing business logic.

## Issue queue algorithm

Treat GitHub as the live queue.

For each candidate issue:

1. Read the complete body, labels, comments/status, and acceptance criteria.
2. Search open PRs, recent commits, and the current tree.
3. Classify the work as implementation, deterministic validation, runtime/production acceptance, external dependency, duplicate/superseded, research, or roadmap.
4. Do not add code to runtime-only or external-only issues. Record the missing evidence/dependency and move on.
5. Prefer the oldest actionable issue with a clear canonical owner and no competing file surface.
6. Prefer the smallest coherent slice that satisfies concrete acceptance criteria.
7. Update tests plus issue/PR metadata so the next agent can resume without chat history.

A blocked PR is not a queue stop condition.

## Parallelization and collision control

Parallelize read-only discovery aggressively:

- batch issue/PR/tree/file reads;
- keep roughly 3–4 independent candidate lanes available;
- re-check active PRs and exact touched files immediately before a write.

Serialize repository mutations:

- branch creation;
- file writes;
- issue/label/status changes;
- PR creation/closure;
- merges.

Do not race another agent on the same issue, branch, or file surface.

## Implementation

Start new work from the latest `main`.

Contracts should be versioned when externally consumed, deterministic where required, bounded for size/depth/fan-out/retries/resources, explicit about unknown/partial/stale/blocked states, and provenance-preserving.

Security and privacy boundaries must fail closed. Do not silently truncate, silently pass, or turn missing evidence into success.

Add owner-level regression tests plus focused boundary/adversarial tests. Never create a second evaluator, verifier, publication authority, identity authority, or resource ledger just to satisfy a local test.

## PR discipline

Every implementation PR should state:

- exact issue(s);
- in-scope and out-of-scope behavior;
- canonical owner;
- tests/validation;
- remaining runtime/external evidence;
- whether the PR is a complete closure candidate or one implementation slice.

Use `Closes #N` only when the repository-level closure criteria for that issue are genuinely satisfied.

Related issues may be batched only when they share the same owner/file surface. Do not bundle unrelated work to reduce PR count.

## Merge discipline

Merge only after required checks and branch-protection rules are satisfied.

Never bypass required checks, authentication, deployment ownership, or runtime evidence gates.

If checks are pending or failing, work on another safe lane instead of waiting.

After a merge, verify current `main` before starting dependent work.

## Duplicate handling

Search before creating a PR.

When an active PR already owns the same implementation, do not create a competitor. Close the duplicate PR with an explicit canonical-PR reference.

Do not close the underlying issue merely because a PR exists; close it only when its acceptance criteria are actually satisfied.

## Runtime and production evidence

Source inspection and repository tests do not substitute for approved runtime/L4 evidence.

Keep runtime-only issues open until required evidence exists. Never fabricate deployments, secrets, bindings, production responses, or acceptance receipts.

Operations may be private; never expose protected topology, credentials, evaluation holdouts, or private runtime implementation through Foundation.

## Cross-repository order

For family changes:

1. Foundation contract/core.
2. Operations integration/control plane.
3. Runtime/production acceptance in the owning environment.

Do not copy implementation between repositories. Share the minimum stable versioned contract.

## Documentation

When ownership, workflow, policy, or agent methodology changes, update the canonical documentation in the same change set.

Non-trivial modules must make responsibility, non-responsibilities, inputs, outputs, invariants, failure semantics, side effects, canonical authority, and tests discoverable without chat history.

## Completion loop

`parallel triage -> non-overlapping slice -> latest-main branch -> smallest safe change -> focused tests -> PR -> merge when green -> update issue -> rescan queue -> next slice`

Continue until the remaining queue is entirely runtime/external/blocked, duplicate/superseded, or otherwise lacks a repository-actionable fix.
