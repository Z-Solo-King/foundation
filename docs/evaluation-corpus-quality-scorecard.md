# Real-source evaluation corpus and vector quality scorecard

Version: `research-evaluation/v1`

Related issues: #407, #408, #388, #386, #387, #369.

## Evaluation corpus

Maintain a versioned corpus covering deterministic facts, multi-source research, contradictions, stale/current temporal cases, multilingual evidence, citation precision, source-family duplication, adversarial retrieved content, incomplete execution, provider/source failure and long-running/large-evidence workloads.

Each case declares the population, expected invariants, oracle/provenance source, replay/snapshot constraints and corpus version. Real-source/oracle evidence is distinct from repository-only testing.

## Vector scorecard

Measure independently:
- correctness;
- completeness;
- evidence coverage;
- citation precision;
- source independence/diversity;
- freshness compliance;
- contradiction state;
- reliability/terminal success;
- latency;
- resource/token efficiency;
- safety/policy compliance.

No aggregate score hides a critical dimension. Missing measurements remain explicit. Critical dimensions may independently block publication or promotion through the existing evaluation authority.

## Provenance and promotion

Corpus identity and scorecard version bind to the existing EvaluationReceipt/provenance system. Evaluation remains the authority for pass/fail and promotion; this document defines measurement inputs and reporting, not a second evaluator.

## Leakage and stability controls

Cases should be checked for duplicate/near-duplicate leakage, oracle contamination and population drift. Equivalent runs should produce comparable semantic measurements even when presentation text differs.

## Required negative cases

Include citation-present-but-irrelevant, one-source-many-claims, duplicated syndicated sources, stale evidence, contradictory observations, provider failure, incomplete results, latency improvement with quality regression and resource improvement caused by harmful truncation.
