## 2026-09-21 LIVE SYNC ANCHOR

- Foundation main: `24e20c19f02a820afb261f4c43915f46c87a6a9c`
- Operations main: `0f1420b2b7dba3270ff8de874ac2eb5e88995976`
- Active Foundation PR: #919 (lifecycle/materialization).
- Active Operations PR: #668 (deep immutability residue).
- Merged current-wave Foundation: #913 Go race gate, #914 multi-blocker nightly diagnosis, #916 runtime capability receipts.
- Merged current-wave Operations: #658 snapshot/provider/stream hardening, #659 Go fanout hardening, #662 shared provider configuration, #664 non-finite robots rejection.
- Current open acceptance queue remains runtime/evidence-heavy; see `docs/ENGINEERING_LEARNING_LOOP_2026-09-21.md` for the synchronized methodology and evidence rules.

# Family Change Methodology

The family has two active repositories: `foundation` and `operations`. The retired `extractor-mapper` repository is historical material only and is never an active implementation owner.

## Required sequence

1. Search both active repositories for the behavior, policy, model, registry, and existing tests.
2. Resolve exactly one canonical owner from `docs/FAMILY_CONTRACT.json` and the repository codemap.
3. Inspect existing consumers, dependencies, side effects, error states, and cost/security constraints before adding a new symbol.
4. Place the code inside the package/layer that already owns that responsibility; split or move a module only when it improves cohesion, dependency direction, security boundary, testing, or maintainability.
5. Extend the canonical owner instead of creating a peer implementation.
6. Expose only the smallest stable, versioned contract required by the consumer.
7. Keep consumer-side guards fail-closed and non-authoritative when the owner already exists elsewhere.
8. Add concise module/function documentation for non-obvious behavior: purpose, inputs/outputs, invariants, side effects, failure semantics, cost/security constraints, and why the code belongs at that layer. Avoid duplicating the algorithm in documentation.
9. Add regression coverage at the owner and at the cross-repository boundary when applicable.
10. Run repository-local validation and the family overlap/ownership audit when structure or ownership changes.
11. Run the deterministic placement/boundary audit for cross-repository structural changes.
12. Remove obsolete compatibility or duplicate implementations after parity evidence.
13. Update the canonical contract and affected codemap whenever ownership, dependency direction, or validation responsibility changes.

## AI/human maintenance standard

Every maintained component should be discoverable through the same chain:

`family contract -> repository codemap -> canonical module -> direct consumers -> owner tests -> boundary tests`

For AI efficiency, prefer indexed metadata, typed contracts, bounded context, deterministic filtering, and targeted reads over repeated repository-wide scans. A chatbot should ask the canonical map for ownership first and inspect source only after it has identified the likely owner.

For human maintainability, prefer cohesive modules with explicit responsibilities, stable names, small public surfaces, deterministic error states, bounded side effects, and comments/docstrings that explain *why* an invariant exists rather than restating the code.

## Definition of done

A cross-repository change is complete only when there is one authoritative implementation of the behavior, one authoritative policy where applicable, a minimal explicit boundary contract, no unexplained duplicate implementation or competing authority, a mechanically valid placement boundary, and enough local explanation/tests for a new human or AI agent to safely modify the component.

## Do not use similarity as the merge rule

Exact equality, structural similarity, or high token similarity identifies candidates for review; it does not prove that two components have the same responsibility. Before merging, compare behavior, side effects, trust boundary, versioning, consumers, and failure semantics.

## Cross-repository order

For a new shared capability, prefer:

`Foundation contract/core -> Foundation validation -> pinned Operations consumption -> Operations private implementation/control -> boundary validation`

Do not copy Foundation implementation into Operations merely to remove an import, and do not move protected Operations policy into Foundation merely to simplify validation.
\n## Cross-paradigm learning scan protocol\n\nUse the four-layer scan in `docs/ENGINEERING_LEARNING_LOOP_2026-09-21.md`: inventory coverage, repository-wide semantic search, targeted owner review, then evidence reconciliation. Record coverage honestly and never treat path inventory coverage as byte-for-byte semantic rereading.\n