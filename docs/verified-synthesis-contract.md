# Verified Synthesis Contract

**Status:** proposed contract for Heroic AI
**Schema:** `verified-synthesis/v1`
**Related:** #435, #385, #386, #392, #398, #409, #412

## Purpose

The synthesizer is a presentation/interpretation stage. It must not become a second evidence authority or silently create facts that were not admitted by the canonical evidence pipeline.

## Input boundary

A synthesis request contains only the fields needed to render the already-resolved result:

- research/execution identity;
- required and optional scope;
- canonical claim identifiers and claim text;
- support state for each claim;
- evidence references and citation metadata already admitted by the evidence pipeline;
- freshness and temporal state;
- contradiction/qualification state;
- explicit gaps and unavailable evidence;
- allowed output language/format;
- schema and policy revisions relevant to interpretation.

Raw credentials, provider internals and unnecessary private payloads are outside this contract.

## Projection rule

Every material factual assertion in the generated answer must be one of:

1. a projection of an admitted claim;
2. an explicitly marked inference derived from admitted claims; or
3. an explicit unknown/limitation statement.

The synthesizer must not manufacture a new evidence reference, source, timestamp, measurement, citation, or verification state.

## State preservation

Synthesis must preserve, rather than strengthen or erase:

- `UNKNOWN`;
- `UNVERIFIED`;
- `QUALIFIED`;
- `CONTRADICTED`;
- stale/expired evidence;
- missing required scope;
- explicit temporal boundaries;
- negation and material qualifiers;
- units and ranges.

`COMPLETED` at synthesis input means the upstream execution contract completed; it does not grant permission to rewrite claim/evidence state.

## Transformation rules

Formatting, summarization, translation and compression may change presentation but may not change epistemic scope. A translation that drops a qualifier, negation, unit or temporal boundary is invalid. A concise answer may omit optional explanatory material, but may not omit a required gap in a way that makes the result appear complete.

## Publication relationship

This contract is upstream of the existing publication gate. The publication gate remains authoritative for public release. A synthesis validator may reject malformed or state-strengthening output, but it does not independently decide whether evidence is true.

## Required negative fixtures

Implementations should test at least:

- unsupported factual sentence added by the model;
- citation invented for an otherwise valid claim;
- claim wording strengthened beyond evidence;
- contradicted claim rendered as settled fact;
- stale evidence rendered as current;
- unknown value filled from model knowledge;
- qualifier, negation, unit or temporal scope lost during translation;
- private provider/runtime detail leaked into the answer;
- required missing scope omitted from the final limitations.

## Acceptance boundary

Repository tests prove the contract and deterministic validation. They do not establish L4 production behavior. Approved runtime evidence is required before claiming that the deployed synthesizer enforces this boundary.

No new claim store, evidence store, publication authority, provider authority or runtime is introduced by this contract.
