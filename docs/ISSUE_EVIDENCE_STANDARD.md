# Evidence-Based Audit and Issue Standard

Repository audits must not turn filenames, counts, or partial context into confident claims.

## Rules

1. No duplication, dead-code, sprawl, missing-feature, or broken-feature claim without reading the relevant content.
2. Before filing, closing, merging, or relabeling an issue, inspect both sides of the claim and confirm the overlap/defect in content.
3. State exactly what was checked; directory listings are leads, not conclusions.
4. Report uncertainty as uncertainty.
5. Corrections to prior findings must be recorded explicitly.
6. For code duplication use increasing-confidence checks such as hash, AST, fingerprint, and structural comparison; the same evidence discipline applies to docs/tests.
7. Record the relevant repository revision when evidence can change.

## Checklist

- [ ] Actual files opened and read.
- [ ] Duplication compared by content, not title alone.
- [ ] Dead/unused claims checked against references/imports/callers.
- [ ] Evidence and revision are recorded.
- [ ] Acceptance condition is explicit.
