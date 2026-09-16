# AI Audit and Verification Standard

Foundation is both an implementation boundary and an evidence boundary. AI-assisted maintenance must not turn partial repository inspection into confident claims about missing code, CI, deployment, or runtime state.

## 1. Evidence levels

- **L0 — hypothesis:** filename, pattern, count, prior chat statement, or suspicion. Never enough to file a defect as fact.
- **L1 — source:** relevant file/module/document opened and read.
- **L2 — repository:** L1 plus repository search/callers/imports/exports/tests checked.
- **L3 — execution:** L2 plus a current test, lint, workflow, or reproducible execution.
- **L4 — runtime:** L3 plus approved current deployment/runtime evidence.

A claim must never be stated more strongly than its evidence level.

## 2. Negative claims require counter-checks

Claims such as **missing, absent, stub, dead, duplicated, unsupported, broken, no retry, no streaming, never called, not implemented** require:

1. reading the target implementation;
2. repository search for the relevant symbol/module/interface;
3. inspection of callers/importers/exports and compatibility facades;
4. inspection of relevant tests;
5. current branch/head/base verification;
6. focused execution when the claim is behavioral.

If a check is unavailable, the correct wording is **unverified** or **partially verified**.

A short file is not proof of a stub. A compatibility export is not duplicate authority. A feature delegated to another module is not absent.

## 3. Positive claims also require acceptance evidence

Do not equate:

- PR existence with implementation completeness;
- mergeability with safe-to-merge;
- a workflow definition with an executed check;
- a successful static search with behavioral success;
- a skipped deployment job with deployment success;
- source code with production state.

The acceptance requirement determines the evidence level needed.

## 4. CI failure taxonomy

Classify failures from job evidence:

- **pre-runner:** zero executed steps, no runner identity/metadata, and no job logs;
- **setup/checkout:** runner executed but repository setup failed;
- **test/check:** a verification step executed and failed;
- **external/tooling:** an external service/action failed after execution began.

A pre-runner failure is not a repository test failure.

## 5. Runtime and production separation

Keep these separate in every report:

1. repository source state;
2. GitHub Actions state;
3. deployment workflow intent;
4. live runtime state.

This repository does not gain knowledge of private runtime secrets, live database state, or live Worker state merely because source code references them. Those claims require the approved runtime evidence path.

## 6. Canonical authority check

Before implementing a missing-looking primitive:

1. locate existing canonical implementations;
2. trace compatibility exports/facades;
3. search for the behavior in other modules;
4. determine the declared authority boundary;
5. add wiring/tests rather than a second implementation when authority already exists.

This is especially important for deterministic core logic and public contracts.

## 7. Revision discipline

Every audit records repository, branch/PR, head SHA, relevant base SHA, and observation time. Never combine different revisions and call them the current state.

Re-check a stale PR against current `main` before merge/close decisions.

## 8. Merge/close gates

Do not merge because a PR is marked mergeable. Required status checks must actually pass and the reviewed head SHA must match the merge head.

Do not close an issue because code exists. Close only when the written acceptance condition is satisfied or the issue is explicitly superseded/duplicate with direct content evidence.

## 9. Required AI audit format

For every substantive finding:

### Finding
One precise claim.

### Evidence
Exact files, symbols, PRs, workflow runs, and SHAs inspected.

### Evidence level
L0–L4.

### Counter-check
What was inspected that could have disproved the claim.

### Result
Verified / partially verified / unverified.

### Action
Fix / test / issue / defer / no change.

### Acceptance gate
Exact evidence required before calling the work complete.

## 10. Prohibited shortcuts

Do not infer implementation from filename, line count, old chat summaries, or AI-generated descriptions. Do not call a compatibility layer a stub without tracing it. Do not call a feature absent without checking delegated/canonical implementations. Do not describe pre-runner CI failures as test failures. Do not claim deployment or runtime state from source alone.

## 11. Incomplete evidence rule

When evidence is incomplete, preserve the uncertainty:

> Source evidence confirms X. The remaining assertion is unverified because Y evidence is unavailable.

Never substitute inference for unavailable evidence.
