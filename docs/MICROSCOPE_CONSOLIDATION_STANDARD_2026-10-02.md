# Microscope Consolidation Standard — 2026-10-02

## Objective
Reduce duplicated engineering surface without losing unique behavior, provenance, security boundaries, production dependencies, or historical evidence.

Consolidation is hierarchical:
repository -> subsystem -> feature -> method/function -> rule/invariant -> policy -> test/evidence -> branch

Every discovered object receives one disposition:
KEEP | COMBINE | SPLIT | TRIM | RETIRE | ARCHIVE | REVIEW

## Authority
Foundation owns public-safe contracts/core/edge/Actions/deployment orchestration. Operations owns private policy/runtime/provider/resource/extraction/migration/evidence. The former extractor-mapper repository is historical only.

One behavior has one authoritative owner. A compatibility facade may preserve imports but must not contain competing semantics.

## Branch graph
For every branch record name, HEAD SHA, protection, ancestry, PR linkage, tag/release linkage, workflow/production references, disposition and confidence.

Same-tip branches are exact duplicate-reference candidates, not automatic deletions. A branch fully contained in default is a merged-redundancy candidate. Unique or diverged branches require semantic/dependency review.

## Capability graph
For every feature/module/function/method:
entrypoint -> implementation -> callers -> dependencies -> tests -> policy -> docs -> runtime evidence

Duplicate detection combines exact bytes/hash, normalized syntax/AST or language structure, signatures, import/call-graph overlap, changed-file overlap, contract similarity and differential tests. AI semantic review is a secondary adjudicator.

## Combine / split / trim
COMBINE equivalent behavior behind one canonical implementation.
SPLIT mixed responsibilities into shared primitives and domain-specific adapters.
TRIM dead code, repeated prose/inventories and obsolete compatibility scaffolding after consumers are verified.
ARCHIVE historical evidence, migration rationale, regression explanations, replay anchors and provenance.

## CrossFire
Use up to six independent AI/API lanes against the same frozen, sanitized candidate input. Lanes must not see one another's answers during evidence collection.

Recommended lenses:
1. identity/duplication
2. unique-behavior preservation
3. combination design
4. split boundary
5. security/policy authority
6. evidence/retirement gate

CrossFire is evidence, not voting. Deterministic authority makes the final disposition.

## Mutation
Discovery is parallel. Mutation is serialized. Every accepted consolidation must preserve/add regression coverage, reconcile owner/docs, verify workflow/runtime boundaries, merge through normal protection and then re-check retirement candidates.

## Completion
100% branches classified; 100% duplicate candidates adjudicated; every capability has one canonical owner or historical status; every rule/policy has one authority; every production/runtime reference reconciled; every retired item has explicit evidence; zero unclassified objects remain.
