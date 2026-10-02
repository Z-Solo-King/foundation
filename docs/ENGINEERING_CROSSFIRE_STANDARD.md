# Engineering CrossFire Standard

## Purpose

Engineering CrossFire is the repository-wide diagnostic pattern for finding defects that a single scanner, model, language lens or workflow can miss.

It is a diagnostic/evidence layer, not a replacement for canonical policy, tests, release gates or production authority.

## Core method

1. Freeze one repository snapshot and scan scope.
2. Run six independent analytical lanes concurrently.
3. Do not pass one lane's findings into another lane during evidence collection.
4. Normalize every lane result into the same finding schema.
5. Compare the lane outputs only after all eligible lanes finish.
6. Classify agreement, disagreement, unavailable lanes and partial coverage.
7. Route each verified finding to its canonical owner.
8. Persist compact evidence: scan revision, scope digest, lane outcomes, finding digest, timing and limitations.
9. Use deterministic repository policy/tests to adjudicate correctness.
10. Serialize mutations, PR creation, merges and production actions after the read-only evidence phase.

## Six project-wide lenses

| Lane | Primary responsibility |
| --- | --- |
| ownership | detect duplicate implementation and unclear ownership boundaries |
| contracts | verify required maps, registries, schemas, entrypoints and canonical navigation surfaces |
| workflows | inspect CI/workflow placement and detect competing automation authority |
| language | inventory source-language/toolchain surface and unexpected runtime candidates |
| documentation | detect stale/dated operational documentation that can become a false source of truth |
| public-surface | detect high-confidence private identifiers, credential-like content and private-runtime paths in the public tree |

The lanes may inspect related surfaces, but they must not consume another lane's conclusions while scanning.

## AI/API CrossFire

Provider/model CrossFire remains available as a separate evidence source. The current target is up to six independent provider lanes with a five-success strong-evidence threshold.

Provider agreement is descriptive evidence only. It cannot authorize deployment, alter policy, promote an implementation or replace deterministic validation.

When raw model output is unnecessary, retain bounded evidence metadata such as provider/model identity, success/failure class, latency, token counts when available, response digest, validator result and limitation.

## Parallelism

Read-only scans should run concurrently with a bounded worker pool. A failure, timeout or unavailable dependency in one lane must not suppress unrelated lanes.

Any stateful operation is a second phase and must be serialized through its canonical owner.

## Evidence states

A run records:

- full_6: all six scan lanes completed;
- strong_5: five lanes completed;
- limited: two to four lanes completed;
- insufficient: zero or one lane completed.

These labels describe diagnostic breadth, not correctness.

## Finding states

A finding is confirmed, candidate, unavailable or suppressed. A finding is never promoted to a production action solely because multiple lanes agree.

## Token efficiency

Prefer scope -> canonical owner -> focused scan -> normalized finding -> digest over repeated full-repository prose.

Receipts should retain hashes, counts, paths, classifications, timings and decisive evidence references. Do not retain large model transcripts unless explicitly required.

## Failure and disagreement

A CrossFire run must expose partial execution.

For each lane record start/completion, duration, status, finding count, error class when unavailable and limitation.

When independent lanes disagree, preserve the disagreement and send the subject to the canonical deterministic authority. Do not average or vote it away.

## Automation placement

Foundation owns the public scheduled/manual engineering CrossFire workflow because Foundation owns hosted GitHub Actions authority.

Operations keeps private runtime/provider/language evidence and executable owner-side tooling, but must not introduce a competing GitHub Actions authority.

## Completion condition

A CrossFire automation change is complete only when the six-lane contract is machine-validated, the scan is deterministic for the same snapshot and scope, partial/unavailable lanes are explicit, evidence is compact and reproducible, findings route to canonical ownership, no mutation occurs during evidence collection, and workflow authority remains singular.
