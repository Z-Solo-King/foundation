# Microscopic Deduplication Standard

## Objective

Keep one canonical implementation for each shared mechanic and keep variants limited to policy, configuration, or genuinely unique behavior.

## Trunk -> Group -> Leaf

```text
unique implementations
        |
        v
shared group mechanics
        |
        v
cross-project common mechanics
        |
        v
configuration / policy / unique hooks
```

### Trunk

Use one canonical implementation for mechanics such as:

- time normalization and freshness
- canonical serialization and hashing
- shared error and receipt shapes
- common retry, I/O, logging, and validation primitives
- workflow orchestration that is identical across consumers

### Group

Use a group module when several consumers share mechanics but differ by domain:

- provider and API adapters
- extraction and parsing
- benchmark and CrossFire execution
- runtime and edge adapters
- persistence or resource-gating mechanics

### Leaf

Leaves contain only:

- unique provider or domain behavior
- policy decisions owned by that subsystem
- configuration
- small adapter hooks
- tests for genuinely unique behavior

## Deduplication Evidence

A consolidation is safe only after checking:

1. semantic equivalence, not just matching names
2. input/output and error-contract compatibility
3. authority, security, privacy, and resource-policy boundaries
4. current call sites and tests
5. branch and pull-request ancestry and whether the candidate contains unique work
6. live or focused validation after migration

Never delete historical branches merely because names look repetitive. Prefer ancestry, content, reference, and dependency evidence.

## Branch Hygiene

Branches are classified as:

- canonical or active: retain
- active unique work: retain until integrated
- superseded duplicate: eligible for retirement after evidence review
- historical evidence: retain when it is the provenance record
- abandoned scratch or retry: eligible for retirement after reference checks

The default branch and release or provenance branches are never retired by an automated name-only rule.

## Cross-Language Rule

Share schemas, fixtures, contracts, and evidence vectors across languages. Do not copy source code solely for symmetry. A language-specific implementation must justify its own runtime or maintenance boundary.

## Migration Sequence

`shared primitive -> parity tests -> migrate one consumer -> focused validation -> migrate next consumer -> remove dead duplicate -> refresh maps/docs`

## Current Implementation Note

The Operations scraper execution fabric now consumes the canonical evidence timestamp parser from `private/shared_evidence_kernel.py` instead of maintaining a second parser, with parity tests preserving legacy UTC normalization behavior.

## Branch retirement authorization — 2026-10-03

Live inventory before this cleanup pass: Foundation 1,383 branches and Operations 1,050 branches. Exact same-tip duplication is currently zero in both repositories.

The retirement executor is authorized only through the existing fail-closed workflow. Eligible refs must be merged into the default branch or be exact same-tip duplicates, satisfy the 24-hour age floor, have no active pull request, protection, release/tag, or live-tree reference, and pass expected-SHA revalidation immediately before deletion.

## Retirement evidence expansion — 2026-10-03

The canonical retirement engine also recognizes branches whose resulting Git tree is identical to the default branch, even when their commit histories diverge. Those refs remain subject to the 24-hour age floor, active pull-request, protection, release/tag, live-reference, and immediate SHA-revalidation checks.

Operations consumes the engine from a pinned Foundation revision instead of maintaining a second implementation.
