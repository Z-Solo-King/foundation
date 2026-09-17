# Uncertainty and Abstention Contract

**Status:** proposed contract
**Schema:** `uncertainty/v1`
**Related:** #438, #385, #386, #392, #407, #408, #435

## Purpose

Heroic AI should distinguish evidence insufficiency from uncertainty, contradiction, staleness and unavailable sources. A scalar confidence value is optional and subordinate to deterministic evidence and publication gates.

## Structured state

For each material claim, preserve the applicable:

- support state;
- evidence sufficiency;
- contradiction state;
- freshness state;
- source-independence state;
- scope/qualification state;
- abstention reason;
- evaluation/calibration identity when a numeric estimate exists.

## Abstention

The system may abstain from asserting a material claim when required evidence is missing, inaccessible, contradictory, stale for the requested task, outside the declared population, or otherwise below the applicable evidence contract. Abstention is an explicit result, not a failed attempt to manufacture confidence.

## Numeric estimates

If a task requires a probability/confidence estimate, its calibration evidence must identify the task, population, corpus version, model/version, evaluation method and time window. Calibration does not grant publication authority and cannot override a hard evidence, provenance, freshness, security or policy gate.

## Invariants

- `UNKNOWN` is not silently converted to low-confidence support.
- `CONTRADICTED` is not averaged into an apparently settled result.
- Missing calibration data is explicit, not treated as a perfect or zero score.
- Source ordering does not change the underlying uncertainty state.
- User feedback and model output cannot directly modify protected thresholds.

## Relationship to evaluation/publication

EvaluationReceipt remains the evaluation authority. The publication gate remains the publication authority. This contract supplies structured uncertainty information to those existing authorities; it does not create another evaluator or evidence store.

## Required fixtures

Test supported, unknown, contradicted, stale, insufficient-sample, out-of-distribution, conflicting-source and source-order permutation cases. Where numeric estimates are used, include reliability/calibration fixtures and verify that hard publication gates still dominate.

Repository evidence establishes contract behavior only. Runtime and production claims remain separately evidence-gated.
