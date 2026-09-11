# Family Architecture Rule

This repository is one member of a three-repository system:

- `foundation`: public contracts and reusable primitives.
- `extractor-mapper`: private bounded execution and deterministic replay.
- `operations`: protected policy, resource governance, verification, and promotion authority.

Dependency direction is one-way:

`foundation -> extractor-mapper -> operations`

The arrows describe contract/result flow, not unrestricted imports. The public repository must not import private implementation, and execution code must not bypass protected Operations gates.

## Single-owner rule

The same behavior may not have multiple authoritative implementations. A compatibility module may expose an old API over the canonical owner, but it may not contain another copy of the algorithm.

## Repository structure rule

New modules belong under the layer that owns their responsibility. Do not create a convenient top-level module when an existing owning package already exists. Keep adapters, compatibility views, policy declarations, execution state, evidence semantics, and orchestration separated by ownership.

## Change methodology

Before adding code:

1. Locate the existing canonical implementation.
2. Decide which repository owns the behavior.
3. Extend that owner rather than duplicating it.
4. Expose the minimum contract needed by consumers.
5. Add a boundary regression test.
6. Mark temporary compatibility code with a removal condition.

## Anti-patterns

- Two resource ledgers for the same resource authority.
- Two execution-run models with overlapping state.
- A private repository reimplementing protected policy from Operations.
- A public repository making trust or promotion decisions.
- Legacy snapshots receiving new business logic.
- A compatibility facade that becomes a second implementation.
