# Family Architecture Rule

This repository is one member of a two-repository system. The public-safe ownership contract is canonical in `docs/FAMILY_CONTRACT.json`.

- `foundation`: public contracts, evidence structures, research contracts, and reusable deterministic primitives.
- `operations`: private control, acquisition, extraction, mapping, verification, evaluation, promotion, private runtime orchestration, and recovery.

Dependency direction is one-way:

`foundation public contract/core -> operations consumer`

Operations may consume the pinned public `foundation_core` package or the public Foundation service contract. Foundation must not import Operations source, private credentials, private runtime state, or protected implementation.

## Single-owner rule

The same behavior may not have multiple authoritative implementations. A compatibility module may expose an old API over the canonical owner, but it may not contain another copy of the algorithm.

This applies to code, policy logic, process methodology, DTOs, registries, state models, routing rules, result-state semantics, resource accounting, provider eligibility, evaluation gates, promotion/rollback, trust/identity checks and deployment ownership.

## Repository structure rule

New modules belong under the layer that owns their responsibility. Do not create a convenient top-level module when an existing owning package already exists. Keep public contracts, evidence semantics, execution state, protected policy and orchestration separated by ownership.

## Maintainability rule

The family maintainability contract is `docs/FAMILY_MAINTAINABILITY_STANDARD.md`. Non-trivial modules should make responsibility, non-responsibilities, inputs, outputs, invariants, failure behavior, side effects, canonical authority and tests discoverable without depending on chat history.

## GitHub change order

Use one coherent feature branch and one PR per owning repository. For a cross-repository change, merge in dependency order: `foundation` contract -> `operations` implementation/control-plane integration. Do not copy implementation between repositories to avoid a dependency.

## Change methodology

1. Locate the existing canonical implementation across both repositories.
2. Decide which repository owns the behavior using `docs/FAMILY_CONTRACT.json` and the repository maps.
3. Inspect imports, runtime entrypoints, state and consumers before modifying or moving code.
4. Extend that owner rather than duplicating it.
5. Expose the minimum stable typed/versioned contract needed by consumers.
6. Add owner-level tests plus boundary/golden-vector tests where repositories interact.
7. Run repository-local validation and the family overlap audit for structural changes.
8. Update the canonical documentation in the same change set when ownership, contract, policy or methodology changes.
9. Remove duplicate, obsolete or completed compatibility code after parity evidence.

## Splitting and moving code

Split when responsibilities, ownership, lifecycle or change frequency are materially independent; do not split merely to reduce line count.

Move between repositories only when ownership requires it. Preserve contracts and compatibility during migration, then delete the old implementation after consumers migrate and parity evidence exists.

## Anti-patterns

- Two resource ledgers for the same authority.
- Two execution-run models with overlapping state.
- A public repository reimplementing protected policy from Operations.
- A public repository making trust or promotion decisions.
- Legacy snapshots receiving new business logic.
- Compatibility facades containing competing business logic.
- Synchronized copy-paste commits across repositories that should instead be a contract plus one owner.
- Large modules with mixed ownership that cannot be reasoned about or tested independently.
- AI token reduction that silently removes constraints, failure states or evidence requirements.

## Historical migration record

The former `extractor-mapper` repository was consolidated into Operations and deleted. Its migration facts are retained in current documentation only. The retired repository and any former `operations/archive/extractor-mapper/` snapshot are not active runtime, CI, package, import or ownership boundaries and must not be recreated.
