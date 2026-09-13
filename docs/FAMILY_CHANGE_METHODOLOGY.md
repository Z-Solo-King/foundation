# Family Change Methodology

The family has two active repositories: `foundation` and `operations`. The retired `extractor-mapper` repository is historical material only and is never an active implementation owner.

## Required sequence

1. Search both active repositories for the behavior, policy, model, registry, and existing tests.
2. Resolve exactly one canonical owner from `docs/FAMILY_CONTRACT.json` and the repository codemap.
3. Inspect existing consumers and side effects before adding a new symbol.
4. Extend the canonical owner instead of creating a peer implementation.
5. Expose only the smallest stable, versioned contract required by the consumer.
6. Keep consumer-side guards fail-closed and non-authoritative when the owner already exists elsewhere.
7. Add regression coverage at the owner and at the cross-repository boundary when applicable.
8. Run repository-local validation and the family overlap/ownership audit when structure or ownership changes.
9. Remove obsolete compatibility or duplicate implementations after parity evidence.
10. Update the canonical contract and affected codemap whenever ownership, dependency direction, or validation responsibility changes.

## Definition of done

A cross-repository change is complete only when there is one authoritative implementation of the behavior, one authoritative policy where applicable, a minimal explicit boundary contract, and no unexplained duplicate implementation or competing authority.

## Do not use similarity as the merge rule

Exact equality, structural similarity, or high token similarity identifies candidates for review; it does not prove that two components have the same responsibility. Before merging, compare behavior, side effects, trust boundary, versioning, consumers, and failure semantics.

## Cross-repository order

For a new shared capability, prefer:

`Foundation contract/core -> Foundation validation -> pinned Operations consumption -> Operations private implementation/control -> boundary validation`

Do not copy Foundation implementation into Operations merely to remove an import, and do not move protected Operations policy into Foundation merely to simplify validation.
