# Exhaustive Research Intelligence Engine Coverage Matrix

Durable coverage index for the Foundation/Operations system. This matrix is not a completion claim; a row becomes complete only when implementation, negative-path tests, and auditable evidence/receipts exist.

| Domain | Current state | Tracker |
|---|---|---|
| ResearchContract / query classification | Partial; typed category and explicit source requirements exist | #58 |
| Source-family planning | Implemented and merged in PR #49; 17-query regression corpus covered | PR #49 |
| Exact identity / variant / anti-contamination | Needs adversarial reconciliation | #59 |
| HTML / JSON-LD / embedded JSON | Protected acquisition remains | Operations #83 |
| API / XHR / robots / sitemap | Protected acquisition remains | Operations #83 |
| Images / lazy images / provenance | Protected acquisition remains | Operations #83 |
| Pagination / completeness certification | Not centralized | #54 |
| Evidence mapping / authority / independence | Needs formal deterministic contract | #60 |
| Contradiction / unresolved-state handling | Needs formal tests | #60 |
| Freshness / TTL semantics | Implemented and merged in PR #66; issue #51 completed | PR #66, #51 |
| Price / stock / regional temporal semantics | Needs integrated field policy | #60 |
| Community / multilingual evidence | Planning exists; protected execution remains | Operations #80, #83 |
| 403 / 429 / 5xx / transport metrics | Operational-failure metrics implemented and merged in PR #52; issue #50 completed | PR #52, #50 |
| ResourceLedger invariants | Canonical implementation exists; adversarial/recovery proof remains | Operations #84, #85, PR #90 |
| Replay / recovery / idempotency | Not complete end-to-end | #55 |
| Prior-night baseline comparison | Not complete | #53, Operations #81 |
| Nightly project-improvement loop | Evidence artifact boundary implemented and merged in PR #49; protected acquisition bridge remains | PR #49, Operations #80, #81 |
| AI claim / source receipt boundary | Fail-closed candidate-evidence rule exists; protected receipt path remains | PR #49, Operations #80 |
| Evidence qualification receipt | New hardening target | #62 |
| Frontend real lifecycle / streaming / reconnect | Contract exists; production integration remains | #56 |
| Secure browser session bridge | Not complete | #40 |
| Private CI observability | Not trustworthy yet | Operations #82 |
| GitHub governance / protected main | CI ownership safeguards partly implemented; main protection still admin-gated | #57 |
| Merge queue / merge_group CI | Workflow support implemented and merged in PR #67; merge queue/ruleset still admin-gated | PR #67, #63 |
| Artifact provenance / attestations | Not implemented | #64 |
| Self-improvement / staged promotion / rollback | Protected integration remains | Operations #81 |

## Completed in current pass

- PR #49 merged: nightly project-improvement evidence + deterministic source-family planning.
- PR #52 merged: operational-failure benchmark metrics + pinned artifact uploads.
- PR #66 merged: evidence freshness TTL semantics unified.
- PR #67 merged: required CI workflow now runs on `merge_group`.
- PR #65 merged: durable coverage matrix added.
- Issues #48, #50, #51 and #63 completed.

## Completion rule

Do not close the master coverage tracker until every applicable row has either a merged/final PR with validated tests or an explicitly scoped blocked/deferred issue with acceptance criteria and preserved evidence context.
