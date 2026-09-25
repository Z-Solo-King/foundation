# Decision-Fork Benchmark

Measures decisions made during long-running agent tasks separately from final task success.

## Flow

state -> candidate options -> decision -> execution -> eventual outcome

The decision-maker sees only the pre-fork state and candidate set. The hindsight label is added only after execution. The open-issue audit now tracks the current live issue inventory during its four-lane scan.

## Decision types

- route: select an allowed execution path
- tool: select an already-authorized tool family
- context: select evidence to retain
- recovery: retry, switch, gather evidence, review, or stop
- continue/stop: decide whether the task is complete
- migration: select a measured migration experiment
- candidate: select a proposal for verification

## Metrics

- decision accuracy
- normalized rank distance
- decision latency
- decision-call count
- per-fork observations retained for audit

Use the same state, candidates, tool policy, fixture revision, and evidence rules across providers. Repeat forks at least three times where practical.

## Boundary

Decision-fork data is benchmark evidence only. It does not replace deterministic validation, authorization, release checks, or runtime evidence.


## 2026-09-25 sync
The decision-fork contract is now part of the nightly benchmark research path. Research findings may nominate forks for this benchmark, but hindsight labels remain external to the decision request.

## Live scan synchronization
The decision-fork benchmark is synchronized with the current 11-issue open-issue scan inventory.
