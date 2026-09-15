# Exhaustive Research Intelligence Engine Coverage Matrix

This document is the durable coverage index for the Foundation repository. It is intentionally a matrix rather than a claim of completion.

| Domain | Contracted outcome | Current state | Durable tracker |
|---|---|---|---|
| Research contract / classification | Typed query category, explicit source requirements | Implemented planning fields; broader classification hardening remains | #48, #58 |
| Source-family planning | Required families are deterministic and regression-tested | PR #49 | #48, #49 |
| Exact product identity / variants | Evidence bound to exact entity/variant | Needs adversarial corpus and deterministic reconciliation hardening | #59 |
| Anti-contamination | Seller/accessory/renewed/used/cross-variant separation | Needs broader adversarial coverage | #59 |
| HTML / JSON-LD / embedded JSON | Normalized acquisition evidence + receipts | Protected acquisition work remains | Operations #83 |
| API / XHR | Only legitimately reachable/authorized surfaces | Protected acquisition work remains | Operations #83 |
| robots.txt / sitemap | Discovery and provenance | Protected acquisition work remains | Operations #83 |
| Images / lazy images | Image identity + provenance | Protected acquisition work remains | Operations #83 |
| Pagination / completeness | Certified complete vs partial/unknown | Not yet centralized | #54 |
| Evidence mapping / reconciliation | Extractor observation -> canonical evidence | Needs authority/identity hardening | #59, #60 |
| Field authority | One deterministic authority contract | Needs formalization | #60 |
| Independence | Copied sources not counted as independent | Needs formalization/tests | #60 |
| Contradictions | Explicit unresolved contradiction state | Needs formalization/tests | #60 |
| Freshness | One canonical TTL policy | Inconsistent today | #51 |
| Price / stock / temporal | Volatile field semantics and regional time context | Needs completeness/authority integration | #51, #60 |
| Community / multilingual | Source-family-specific acquisition + provenance | Planning exists; protected execution remains | Operations #80/#83 |
| 403 / 429 / 5xx / transport | Distinct failure classes and actionable metrics | Partial; operational failure metric hardened in PR #52 | #50, PR #52 |
| ResourceLedger | reserve -> execute -> consume -> reconcile -> release | Protected implementation/testing remains | Operations #84 |
| Replay / recovery | Durable checkpoints + idempotent replay | Not yet complete | #55 |
| Benchmark baseline | Compare current run with prior compatible baseline | Reporting exists; baseline loop remains | #53, Operations #81 |
| Nightly project research | Observe project -> research externally -> adjudicate improvements | PR #49 establishes evidence artifact boundary; execution bridge remains | #49, Operations #80/#81 |
| AI claims / source receipts | Model claims cannot become evidence without receipt | Fail-closed policy exists in nightly project research | #49, Operations #80 |
| Evidence qualification receipt | Claim bound to evidence digests/freshness/contradiction/evaluation | New architecture hardening candidate | #61 |
| Frontend lifecycle | Real backend stream/poll/reconnect/queue semantics | UI contract exists; production integration remains | #56 |
| Secure browser session bridge | Least-privilege short-lived authorized browser session | Not complete | #40 |
| CI observability | Every protected job produces trustworthy normalized receipt | Private side incomplete | Operations #82 |
| GitHub governance | Protected main, required checks, deployment ownership | Issue-gated | #57 |
| Merge queue | Required checks also run for merge_group | Not yet encoded | #62 |
| Artifact provenance | Build/research artifacts have verifiable provenance | Not yet encoded | #63 |
| Self-improvement | evidence -> candidate -> benchmark -> regression -> staged promotion | Protected promotion remains | Operations #81 |

## Completion rule

A row is complete only when its implementation exists, its negative/error boundaries are tested, and its evidence or execution receipt can be audited to a repository revision. Protected/private work must remain issue-gated until the appropriate protected executor proves it.
