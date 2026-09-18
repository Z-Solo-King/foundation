# Family engineering guidance

Read `REPOSITORY_MAP.json` and `docs/FAMILY_CONTRACT.json` before changing architecture. Read `docs/FAMILY_ARCHITECTURE.md` when a change crosses the repository boundary.

If working from the open issue queue, also read `operations/docs/AI_AGENT_PARALLEL_TRACK_ASSIGNMENT.md` and pick up your assigned `track:*` label — it tells you which issues (in both repositories) are safe to work in parallel without file-surface collisions, which are pure runtime-evidence gates requiring no code, and which infra-blocker issues must be resolved before anything else.

Foundation owns public-safe contracts, deterministic research and evidence primitives, planning, and the public Worker/API boundary. Operations owns protected policy, resource governance, private acquisition/execution, evaluation, promotion, rollback, deployment/recovery, and chatbot control.

Before adding code, search both active repositories for an existing implementation and identify the canonical owner. Extend that owner rather than creating a second implementation. Use a thin compatibility facade only when a supported legacy import requires it.

Cross-repository changes follow dependency direction: Foundation contract/core first, Operations consumer/control-plane integration second. Do not copy implementation between repositories to avoid a dependency.

Keep code readable to another maintainer: explicit types, cohesive modules, narrow functions, clear error semantics, bounded side effects, and tests beside the owner. Avoid creating a module only because its name is convenient.

Never expose private topology, credentials, evaluation holdouts, or protected implementation through this public repository.



## Issue-queue execution strategy

The issue queue is the work plan. Optimize for **verified throughput**, not activity count.

### 1. Parallel read/triage pass

Run independent read-only lanes in parallel:

- **Duplicate lane** — exact, superseded, or repetitive issues; identify one canonical owner.
- **Implementation lane** — inspect canonical code/tests for small missing acceptance slices.
- **Grouping lane** — map related issues into implementation streams and dependency order.
- **PR/CI lane** — inspect open PRs, changed files, mergeability, required checks, and stale bases.

Do not wait for one read lane before starting another.

### 2. Controlled mutations

Parallelize independent branches/files, but never competing writes to the same file or branch. Keep issue updates, file writes, PR creation, and merges controlled to avoid GitHub secondary-rate-limit collisions.

Preferred flow:

parallel discover → independent slices → parallel branch work → controlled writes → parallel CI polling → merge green → refresh main

Never continue a long chain from a stale base after main changes. Rebase/replay the intended patch onto current main.

### 3. Bounded implementation slices

For large issues, extract a concrete independently testable contract slice instead of waiting for the entire issue.

Every slice should have:

1. one canonical owner;
2. explicit acceptance behavior;
3. bounded scope;
4. regression/adversarial tests;
5. no duplicate authority;
6. no unnecessary Cloudflare/Operations dependency.

Leave the parent issue open when only a slice is complete. Record exactly what landed and what remains.

### 4. Merge from evidence

A PR is merge-ready only when:

- based on current main or refreshed after main changed;
- required GitHub checks are successful;
- changed-file surface is understood;
- no competing PR owns the same file surface;
- no second authority is introduced.

Do not claim tests are green when checks are absent, pending, or failed.

### 5. Stale PR handling

When main advances:

- preserve the intended patch;
- replay/rebase it onto current main;
- close obsolete PRs only after verifying the work is preserved or superseded;
- verify main directly rather than assuming a closed PR lost its code.

Avoid repeatedly rebuilding the same stale patch.

### 6. Issue closure rules

Close only when the **full acceptance contract** is satisfied or the issue is provably:

- an exact duplicate;
- superseded by a newer canonical issue with equivalent scope;
- invalid/obsolete by explicit repository evidence.

A contained implementation slice does not automatically close its parent.

For duplicates: comment the canonical mapping, preserve any unique acceptance in the canonical issue, then close the duplicate.

### 7. Evidence levels

Keep these separate:

- **L1:** repository source, schemas, tests, docs.
- **L2:** repository CI/check results.
- **L3:** GitHub administrative evidence.
- **L4:** external/runtime evidence such as Cloudflare, private Operations runtime, production behavior, or external resources.

Never close an L3/L4-gated issue using only L1/L2 evidence.

### 8. Foundation/Operations boundary

Foundation owns public-safe API/schema contracts, deterministic research/evidence primitives, source/artifact integrity and provenance, bounded acquisition/public reads, planning/decision primitives, and the public Worker boundary.

Operations owns protected runtime policy, resource governance, private acquisition/execution, evaluation/promotion/rollback, deployment/recovery, and chatbot control.

This is a Foundation/GitHub scope. Do not use Cloudflare tooling or modify Operations source from a Foundation-only task. Record cross-repository dependencies instead.

### 9. Canonical-owner rule

Before implementing:

search both repos → inspect existing code/tests → identify canonical owner → extend owner → add a compatibility facade only if required

Do not create a second implementation because the existing module is inconvenient.

Prefer one versioned contract source of truth with thin adapters and deterministic serializers.

### 10. Fast-path priority

When the queue is large:

1. exact duplicates/superseded issues;
2. already-complete issues that can be verified and closed;
3. small deterministic contract/test gaps;
4. bounded security/resource controls;
5. medium implementation slices;
6. broad cross-repository features;
7. L3/L4 runtime acceptance gates.

This is a throughput order, not an importance ranking. Actionable security/production blockers jump ahead.

### 11. Four-lane execution template

| Lane | Purpose | Output |
|---|---|---|
| A | Duplicate/closure audit | canonical mappings + safe closures |
| B | Quick implementation | small tested PRs |
| C | Contract/dependency grouping | ordered implementation streams |
| D | PR/CI verification | merge-ready result or exact failure |

After every merge/closure batch, refresh the queue. Never rely on an old issue count.

### 12. Progress discipline

For long autonomous work:

- report meaningful batch progress;
- state changed, blocked, and remaining work;
- do not repeatedly ask for permission when scope is clear;
- do not stop because one PR is waiting on CI;
- continue independent discovery and implementation while CI runs.
