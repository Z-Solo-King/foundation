# Exhaustive Research Intelligence Engine Coverage Matrix

Durable coverage index for the Foundation/Operations system. This matrix is not a completion claim; a row becomes complete only when implementation, negative-path tests, and auditable evidence/receipts exist.

| Domain | Current state | Tracker |
|---|---|---|
| ResearchContract / query classification | Partial; typed category and explicit source requirements exist | #48, #58 |
| Source-family planning | Implemented in PR #49; regression corpus added | #48, #49 |
| Exact identity / variant / anti-contamination | Needs adversarial reconciliation | #59 |
| HTML / JSON-LD / embedded JSON | Protected acquisition remains | Operations #83 |
| API / XHR / robots / sitemap | Protected acquisition remains | Operations #83 |
| Images / lazy images / provenance | Protected acquisition remains | Operations #83 |
| Pagination / completeness certification | Not centralized | #54 |
| Evidence mapping / authority / independence | Needs formal deterministic contract | #60 |
| Contradiction / unresolved-state handling | Needs formal tests | #60 |
| Freshness / TTL semantics | Inconsistent between evidence record and verifier | #51 |
| Price / stock / regional temporal semantics | Needs integrated field policy | #51, #60 |
| Community / multilingual evidence | Planning exists; protected execution remains | Operations #80, #83 |
| 403 / 429 / 5xx / transport metrics | Partial; operational-failure metric hardening in PR #52 | #50, PR #52 |
| ResourceLedger invariants | Protected implementation/testing remains | Operations #84 |
| Replay / recovery / idempotency | Not complete | #55 |
| Prior-night baseline comparison | Not complete | #53, Operations #81 |
| Nightly project-improvement loop | Evidence artifact boundary implemented; acquisition bridge remains | #49, Operations #80, #81 |
| AI claim / source receipt boundary | Fail-closed candidate-evidence rule exists | #49, Operations #80 |
| Evidence qualification receipt | New hardening target | #62 |
| Frontend real lifecycle / streaming / reconnect | Contract exists; production integration remains | #56 |
| Secure browser session bridge | Not complete | #40 |
| Private CI observability | Not trustworthy yet | Operations #82 |
| GitHub governance / protected main | Issue-gated | #57, #63 |
| Merge queue / merge_group CI | Not encoded | #64 |
| Artifact provenance / attestations | Not encoded | #65 |
| Self-improvement / staged promotion / rollback | Protected integration remains | Operations #81 |

## Completion rule

Do not close the master coverage tracker until every applicable row has either a merged/final PR with validated tests or an explicitly scoped blocked/deferred issue with acceptance criteria and preserved evidence context.
