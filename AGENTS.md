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


## Fast queue operating profile

For high-volume maintenance, use a two-stage scheduler: parallel read-only discovery, then a serialized mutation queue. Keep 3-4 non-overlapping candidate lanes available, but never let parallel lanes share an issue, branch, or file surface. Re-check active PRs and exact paths immediately before each write.

Track every candidate as one of: `actionable`, `in_progress`, `blocked_checks`, `runtime_only`, `external_blocked`, `duplicate`, `superseded`, or `complete`. A blocked check lane does not stop other actionable lanes.

Prefer exact-path reads and bounded searches over repeated full-tree scans. After a merge or PR closure, refresh only the affected queue slices first, then perform a broader rescan.

GitHub API operations must respect rate limits: avoid excessive concurrent requests, serialize mutations, space large mutation bursts, and back off on secondary-rate-limit responses. Use stable, narrow queries when polling.

## Queue execution protocol v2

Use this operating contract for high-volume issue reduction.

### Wave scheduler

1. **Discovery wave:** keep 3–4 independent read-only lanes classifying issues, PRs, exact file surfaces, and acceptance evidence.
2. **Mutation wave:** serialize branch creation, file writes, PRs, issue updates, and merges.
3. **Acceptance wave:** while checks run, continue independent discovery and implementation instead of waiting.
4. **Rebase wave:** after a relevant merge changes `main`, refresh dependent branches before merge.
5. **Rescan wave:** after every 3–5 meaningful mutations, refresh the live issue/PR queue and discard stale plans.

Never treat a captured issue list as authoritative after another mutation changes repository state.

### Lane packet

Before mutation, each lane records: issue and exact acceptance target; queue disposition; canonical owner/file surface; competing PR/branch; focused tests; and remaining runtime/external evidence. A lane with overlapping authority or files must yield before writing.

### Fresh-main rule

Start from current `main`. If `main` advances before merge, update the work branch through a normal non-force-push flow and rerun required checks. Never make an old PR mergeable by bypassing protection or altering status metadata.

### Acceptance ladder

Treat evidence as:

`implemented -> tested -> CI_green -> integration_verified -> runtime_verified -> production_certified`

Close an issue only at the highest rung explicitly required by its acceptance criteria. Repository tests do not become runtime or production evidence by wording.

### Failure routing

When a lane fails, narrow the failure to the exact contract, file, test, branch-protection rule, or external dependency. Fix the root cause or record a precise blocker, then switch to another independent lane. Never weaken a gate to manufacture progress.

### Batch discipline

Batch issues only when they share the same canonical authority and touched file surface. The PR body must enumerate every included issue and explicitly mark any issue that remains only partially satisfied.

### Queue truth

Issue count is a metric, not the goal. Do not close an issue merely because code, a PR, or green tests exist. Preserve runtime/admin/external gates until their required evidence exists.

### Maintainer handoff

Every substantive issue update should leave the canonical files, completed acceptance items, remaining items, current PR/commit, and blocker/evidence state discoverable without chat history.
