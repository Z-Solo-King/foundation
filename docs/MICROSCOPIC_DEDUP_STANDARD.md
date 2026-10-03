# Microscopic Deduplication Standard

## Objective

Keep one canonical implementation for each shared mechanic and keep variants limited to policy, configuration, or genuinely unique behavior.

## Trunk → group → leaf

```text
unique implementations
        │
        ▼
shared group mechanics
        │
        ▼
cross-project common mechanics
        │
        ▼
configuration / policy / unique hooks
```

### Trunk
Use one canonical implementation for mechanics such as:
- time normalization and freshness
- canonical serialization and hashing
- shared error/receipt shapes
- common retry, I/O, logging, and validation primitives
- workflow orchestration that is identical across consumers

### Group
Use a group module when several consumers share mechanics but differ by domain:
- provider/API adapters
- extraction/parsing
- benchmark/crossfire execution
- runtime/edge adapters
- persistence or resource-gating mechanics

### Leaf
Leaves contain only:
- unique provider/domain behavior
- policy decisions owned by that subsystem
- configuration
- small adapter hooks
- tests for genuinely unique behavior

## Deduplication evidence

A consolidation is safe only after checking:
1. semantic equivalence, not just matching names;
2. input/output and error-contract compatibility;
3. authority, security, privacy, and resource-policy boundaries;
4. current call sites and tests;
5. branch/PR ancestry and whether the candidate contains unique work;
6. live or focused validation after migration.

Never delete historical branches merely because names look repetitive. Prefer ancestry/content/reference evidence.

## Branch hygiene

Branches are classified as:
- canonical/active: retain;
- active unique work: retain until integrated;
- superseded duplicate: eligible for retirement after evidence review;
- historical evidence: retain when it is the provenance record;
- abandoned scratch/retry: eligible for retirement after reference checks.

The default branch and release/provenance branches are never retired by an automated name-only rule.

## Cross-language rule

Share schemas, fixtures, contracts and evidence vectors across languages. Do not copy source code solely for symmetry. A language-specific implementation must justify its own runtime or maintenance boundary.

## Migration sequence

shared primitive → parity tests → migrate one consumer → focused validation → migrate next consumer → remove dead duplicate → refresh maps/docs.

## Current implementation note

The Operations scraper execution fabric now consumes the canonical evidence timestamp parser from `private/shared_evidence_kernel.py` instead of maintaining a second parser, with parity tests preserving legacy UTC normalization behavior.
