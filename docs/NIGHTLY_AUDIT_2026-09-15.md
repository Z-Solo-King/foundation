# Nightly GitHub research audit — 2026-09-15

## Execution truth

The current Foundation nightly workflow is **not** a 20-way fan-out. It runs two sequential research jobs (`research-a`, then `research-b`), each covering four slots, followed by a project-summary job. Each research job has a 265-minute timeout. Therefore this audit records the requested 19+1 matrix as **coverage intent**, not as executed evidence. The repository's GitHub Actions policy also makes Foundation the public execution owner while private Operations Actions capacity is restricted during September 2026.

## Reproducible gaps found

1. The existing workflow does not execute 19 independent experiment classes.
2. The existing multi-agent runner supports global capacity 20 and paired capacity experiments, but its nightly program catalog remains 24 project programs organized as 8 slots × 3 lanes rather than the requested 19-class matrix.
3. LLM result records historically did not preserve provider usage fields such as input/output/cached/thinking tokens; the data model now has fields for these measurements, but mainline execution is not yet certified to populate them end-to-end.
4. Chat learning is now durable-capable in Operations, but private CI is unavailable/restricted for this period; the merged runtime explicitly keeps chat observations candidate-only.
5. UI lifecycle source tests cover local queue/reconnect semantics, but a visible browser session and live deployed UI cannot be claimed from source inspection alone.
6. B2 repository-backup workflow attempts on the new Foundation branch failed without job records; no remote backup/restore success is claimed from those runs.

## Implemented this audit

- Foundation PR #156: deterministic 19-experiment + aggregator matrix, execution-coverage accounting, and explicit no-production-mutation/no-hidden-CoT invariants.
- Foundation issue #157: tracks normal workflow integration of the 19+1 execution matrix.
- Operations PR #180: durable bounded chat-learning store, fail-closed learning qualification, candidate strategy-signal derivation, and expanded token/tool economics.

## Evidence rules

No model output, chat memory, historical benchmark anecdote, inaccessible source, or static UI inspection is promoted to authoritative evidence. External claims require receipts. Chat-derived learning can influence candidate strategy ordering only within equal evidence-strength tiers. Protected policy, security, identity, billing, access control and resource authority remain outside the chat-learning plane.

## Next validation

The next executable priority is to integrate the 19+1 matrix into the Foundation workflow through normal PR checks, execute it on the public Foundation owner, persist one sanitized artifact per job plus one aggregator report, and compare the resulting metrics with the previous successful nightly baseline. Only after observed execution should individual coverage classes be marked complete.
