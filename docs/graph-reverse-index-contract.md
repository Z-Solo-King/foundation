# Evidence and Claim Graph Reverse-Index Contract

**Status:** proposed
**Schema:** `graph-index/v1`
**Related:** #442, #383, #391, #398

## Purpose

Production evidence traversal must use indexed D1 access paths rather than rebuilding in-memory dictionaries or scanning full tables. D1 remains the canonical production graph store.

## Required access paths

Provide indexed paths for claim/evidence, evidence/document, document/source, source/lineage, observation/run-time, claim validity, and content-hash reuse candidates.

## Invariants

- Index state represents canonical rows exactly; it does not create semantic relationships.
- Authorization, retention and deletion constraints apply to indexed reads as they do to canonical reads.
- Writes that affect an index are committed atomically with the authoritative state where practical.
- Rebuilds are deterministic, resumable and non-destructive.
- Duplicate content hashes may identify reuse candidates but never prove evidence equivalence or truth.
- Pagination uses stable indexed keys rather than large OFFSET scans.

## Recovery

A rebuild may run from canonical D1 state after corruption or schema migration. During rebuild, callers must receive an explicit availability/degraded state rather than reading an incomplete index as authoritative.

## Acceptance

Test forward/reverse traversal, concurrent writes, duplicate hashes, retention/deletion, interrupted rebuild and reconciliation against canonical rows. Verify query plans remain bounded for representative workloads and that rebuilding never changes evidence semantics.

This is an indexing contract only; it introduces no second graph store or evidence authority.
