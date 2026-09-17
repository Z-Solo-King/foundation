# Typed Contradiction Contract

**Status:** proposed
**Schema:** `contradiction/v1`
**Related:** #443, #401, #407, #408, #429, #436

## Purpose

Contradiction detection must compare claims according to predicate semantics rather than broad lexical mismatch. Candidate generation must also be bounded so contradiction analysis does not become an unrestricted O(C²) production path.

## Predicate families

Implement deterministic handling for numeric values and tolerances, normalized quantities/units, dates and validity windows, mutually exclusive categories, geography/scope, product/model/version predicates, commercial qualifiers, and explicit negation.

## Candidate bucketing

Candidates are first bucketed by compatible entity, predicate, temporal window and scope. Expensive comparison occurs only within compatible buckets. Bucket keys and normalization versions are recorded for replay.

## Semantics

Missing/unknown values do not contradict. Different product versions, regions or time windows remain distinct unless an explicit compatibility rule applies. `starts_at` must not be treated as an exact-price assertion. Unit conversion is deterministic and provenance-preserving.

AI can adjudicate genuinely ambiguous semantic conflicts, but the accepted contradiction relation remains governed by the canonical verification authority.

## Acceptance

Test numeric tolerance, unit conversion, dates, category exclusion, geography, version, commercial qualifiers, negation, missing values and ambiguous wording. Verify source-order invariance, bounded candidate counts, deterministic outcomes and retained claim/evidence lineage.

No second contradiction engine or evidence authority is introduced.
