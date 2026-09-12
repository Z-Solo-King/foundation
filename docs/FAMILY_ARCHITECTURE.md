# Family Architecture Rule

This repository is one member of a two-repository system. The public-safe ownership contract is canonical in `docs/FAMILY_CONTRACT.json`.

- `foundation`: public contracts, evidence structures, research contracts, and reusable deterministic primitives.
- `operations`: private control, acquisition, extraction, mapping, verification, evaluation, promotion, deployment, recovery, and chatbot orchestration.

Dependency direction is one-way:

`foundation -> operations`

The arrow describes public contract/result flow, not unrestricted imports. The public repository must not import private implementation, and Operations must not bypass its protected policy and resource gates.

## Single-owner rule

The same behavior may not have multiple authoritative implementations. A compatibility module may expose an old API over the canonical owner, but it may not contain another copy of the algorithm.

## Repository structure rule

New modules belong under the layer that owns their responsibility. Do not create a convenient top-level module when an existing owning package already exists. Keep public contracts, evidence semantics, execution state, protected policy, and orchestration separated by ownership.

## GitHub change order

Use one coherent feature branch and one PR per owning repository. For a cross-repository change, merge in dependency order: `foundation` contract -> `operations` implementation/control-plane integration. Do not copy implementation between repositories to avoid a dependency.

## Change methodology

1. Locate the existing canonical implementation.
2. Decide which repository owns the behavior using `docs/FAMILY_CONTRACT.json`.
3. Extend that owner rather than duplicating it.
4. Expose the minimum contract needed by consumers.
5. Add a boundary regression test.
6. Run repository-local validation.
7. Run the family overlap audit when ownership or cross-repository structure changes.
8. Remove duplicate implementation after parity evidence.

## Anti-patterns

- Two resource ledgers for the same resource authority.
- Two execution-run models with overlapping state.
- A public repository reimplementing protected policy from Operations.
- A public repository making trust or promotion decisions.
- Legacy snapshots receiving new business logic.
- A compatibility facade that becomes a second implementation.
- Synchronized copy-paste commits across repositories that should instead be a contract plus one owner.

## Historical migration record

The former `extractor-mapper` repository was consolidated into Operations and deleted. Selected historical migration material is retained only under `operations/archive/extractor-mapper/` as non-active reference material. It is not an active dependency, runtime source, CI target, or privacy boundary.
