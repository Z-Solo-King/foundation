# AI Audit and Verification Standard

Foundation is both an implementation boundary and an evidence boundary. AI-assisted maintenance must not turn partial repository inspection into confident claims about missing code, CI, deployment, or runtime state.

## Evidence levels

- **L0 — hypothesis:** pattern, filename, count, prior statement, or suspicion.
- **L1 — source:** relevant file/module/document opened and read.
- **L2 — repository:** L1 plus search, callers/imports/exports, compatibility paths, and tests.
- **L3 — execution:** L2 plus a current test, lint, workflow, or reproducible execution.
- **L4 — runtime:** L3 plus approved current deployment/runtime evidence.

Claims must never be stronger than their evidence level.

## Negative claims

Claims such as missing, absent, stub, duplicated, broken, unsupported, no retry, no streaming, or never called require the target read, repository search, caller/export inspection, relevant tests, current revision verification, and focused execution when behavioral. If evidence is unavailable, say unverified or partially verified.

A short file is not proof of a stub. A compatibility export is not duplicate authority. A delegated implementation is not absence.

## Positive claims

Do not equate PR existence with completeness, mergeability with acceptance, workflow definitions with executed checks, skipped jobs with success, or source with production state. The acceptance requirement determines the required evidence level.

## CI taxonomy

- **pre-runner:** zero executed steps, no runner identity/metadata, no logs;
- **setup/checkout:** runner executed but repository setup failed;
- **test/check:** a verification step executed and failed;
- **external/tooling:** an external service/action failed after execution began.

A pre-runner failure is not a repository test failure.

## Runtime separation

Keep repository source, GitHub Actions, deployment intent, and live runtime state separate. Private secrets and live infrastructure require the approved runtime evidence path.

## Canonical authority

Before implementing a missing-looking primitive, locate canonical implementations, trace compatibility exports/facades, inspect callers, and determine ownership. Extend existing authority rather than creating a second implementation.

## Revision and merge discipline

Record repository, branch/PR, head SHA, relevant base SHA, and observation time. Never mix revisions. Do not merge because GitHub reports mergeable; required checks must pass on the reviewed head. Do not close an issue because code exists unless its written acceptance condition is satisfied or it is directly superseded/duplicated with evidence.

## Required finding format

### Finding
One precise claim.

### Evidence
Exact files, symbols, PRs, workflow runs, and SHAs.

### Evidence level
L0–L4.

### Counter-check
What was inspected that could have disproved the finding.

### Result
Verified / partially verified / unverified.

### Action
Fix / test / issue / defer / no change.

### Acceptance gate
Exact evidence required before calling the work complete.

## Prohibited shortcuts

Do not infer implementation from filenames, line counts, historical summaries, or AI descriptions. Do not call a compatibility layer a stub without tracing it. Do not describe pre-runner failures as test failures. Do not claim deployment/runtime state from source alone.

## Incomplete evidence rule

> Source evidence confirms X. The remaining assertion is unverified because Y evidence is unavailable.

Never substitute inference for unavailable evidence.
