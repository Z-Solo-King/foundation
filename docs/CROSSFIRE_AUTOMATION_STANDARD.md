# CrossFire Automation Standard

**Status:** Active project-wide quality pattern

CrossFire means using multiple independent lenses against the same target, then
normalizing evidence, checking contradictions, and preserving the existing
specialized acceptance authorities.

## Where it applies

Use the pattern for repository audits, migration, extractor/mapper work, chatbot
verification, provider comparison, workflow/security review, regression replay and
external-source acquisition.

## Default topology

**normalize -> select lenses -> fan-out -> execute -> normalize receipts -> dedupe ->
contradiction check -> acceptance -> persist**

The existing CI/workflow system remains the executor. CrossFire does not create a
second scheduler.

## Coverage rule

Important surfaces should have at least two materially different verification paths.
High-risk audits may use six or eight lanes. A second lane should differ by evidence
family, runtime, method, provider, browser or trust boundary; rereading the same file
is not independent verification.

## Quality patterns

Use cross-lens triangulation, cross-runtime replay, cross-provider differential,
cross-browser differential, cross-method extraction ladders, historical regression
replay, boundary audits, negative-space audits, metamorphic checks and bounded mutation
tests where the target warrants them.

## Authority rule

CrossFire results are evidence for existing owners. They must not:

- replace a canonical acceptance gate;
- turn diagnostic output into production proof;
- bypass credentials, rate limits or access controls;
- retry indefinitely;
- mutate production during an audit;
- hide skipped lanes or contradictory evidence.

## Learning rule

Verified receipts may improve future lane prioritization, cost estimation and
failure prediction. They may not weaken required security, provenance, policy,
resource or release gates.
