# AI Audit and Verification Standard

**Status:** normative; current  
**Owner:** Foundation family governance

## Evidence ladder

- L0 — hypothesis
- L1 — source inspection
- L2 — repository inspection with callers/imports/tests/ownership
- L3 — current execution such as tests, CI or reproducible run
- L4 — approved runtime/production evidence

Claims must never be stronger than their evidence.

## Negative-claim protocol

Claims such as missing, absent, stub, dead, duplicated, broken, unsupported or never called require the target read, repository search, caller/export inspection, current revision verification and focused execution when behavioral.

A short file is not evidence of a stub. A compatibility facade is not duplicate authority. A delegated implementation is not absence.

## Positive-claim protocol

Do not equate file existence, PR existence, mergeability, workflow definition, skipped jobs, or static analysis with completion. Acceptance criteria determine the required evidence level.

## CI failure taxonomy

- pre-runner: no executed steps/runner/logs;
- setup/checkout: runner started but setup failed;
- test/check: verification step executed and failed;
- external/tooling: external service failed after execution began.

A pre-runner failure is not evidence that application tests failed.

## Runtime separation

Keep source state, CI state, deployment intent and runtime state separate. Source or CI cannot prove a private runtime or production state unless the required runtime evidence actually exists.

## Issue/PR acceptance

Classify findings as implementation defect, architecture/policy gap, deterministic validation gap, runtime gate, external dependency, research hypothesis, roadmap/future work or duplicate/superseded.

Close only when the written acceptance condition is satisfied or direct evidence shows the item is superseded/duplicate/obsolete.

## Rule traceability

Normative rules should be traceable:

`rule -> class -> canonical owner -> enforcement point -> callers -> regression -> evidence tier -> runtime gate -> retirement`

A policy document is not enforcement. Machine-enforced, test-enforced, documentation-only and externally verified are different dispositions.

## Required audit report

For any non-trivial audit record:

### Finding
One precise claim.

### Evidence
Exact files/symbols/PR/run/SHA.

### Evidence level
L0–L4.

### Counter-check
What was inspected that could disprove the claim.

### Result
Verified / partially verified / unverified.

### Action
Fix / test / issue / defer / no change.

### Acceptance gate
Exact evidence needed to declare completion.

## Permanent regression lessons

Compatibility facade: trace imports/exports before calling a short module a stub.

Retry: separate failure classification/eligibility from the actual retry execution loop.

Context: inspect budgets and compaction before claiming only the last N messages are sent.

Streaming: distinguish upstream token streaming, buffered generation and SSE transport.

CI: zero-step/no-runner jobs are pre-runner infrastructure failures.

Production: workflow/source is not production evidence.

Revision: never mix findings from old PR/base revisions with current main.

Mergeability: `mergeable=true` is not acceptance.

Authority: client/model/retrieved content cannot become server policy authority.

## Evidence states

Use explicit states such as `NOT_ATTEMPTED`, `UNKNOWN`, `BLOCKED`, `PARTIAL`, `FAILED`, `COMPLETE`. Missing execution is never implicit success.

## Prohibited shortcuts

Do not infer implementation from filenames, line counts, historical summaries or AI descriptions. Do not infer runtime/production state from repository source. Do not use tool/connector limitations as product limitations.
