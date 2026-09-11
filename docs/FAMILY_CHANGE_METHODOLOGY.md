# Family Change Methodology

Use this sequence for cross-repository changes:

1. Search for the existing behavior across all three repositories.
2. Assign exactly one owner.
3. Extend the owner instead of copying logic.
4. Expose a minimal versioned contract to consumers.
5. Keep local safeguards fail-closed and non-authoritative.
6. Add regression tests at both the owner and boundary where appropriate.
7. Remove obsolete or compatibility implementations once equivalence is proven.
8. Do not add new functionality to legacy snapshot engines.

A change is complete only when the family has one canonical implementation of the behavior.
