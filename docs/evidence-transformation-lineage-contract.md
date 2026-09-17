# Evidence Transformation Lineage Contract

**Status:** proposed contract
**Schema:** `evidence-transformation/v1`
**Related:** #440, #397, #400, #402, #403, #385, #386, #429

## Purpose

Research evidence commonly passes through deterministic parsing, HTML cleanup, Unicode normalization, OCR, translation, chunking and other transformations. Provenance must survive those transformations without pretending that a derived representation is the original source.

## Derived representation

A transformed artifact or span records, where applicable:

- parent artifact/document version;
- transformation type and implementation version;
- input and output fingerprints;
- execution identity;
- language/encoding transformation;
- extraction confidence and warnings;
- exact span mapping, mapped range, or explicit `MAPPING_LOST` state;
- source-access and retention classification inherited from the parent.

## Transformation semantics

Deterministic formatting normalization may change presentation without changing claim semantics. Transformations that can change text, ordering, language, units or interpretation must remain identifiable as derived material.

OCR and translation are derived evidence. They can help locate or interpret source material but cannot silently increase source authority. If a transformation is lossy, downstream verification must know that exact source-span equivalence is unavailable.

## Span invariant

When an exact mapping exists, the implementation should be able to reconstruct the relationship:

`derived_span -> source_document_version -> source_span`

When it does not, the contract requires an explicit mapping limitation rather than invented offsets.

## Claim-critical preservation

Transformations must preserve, or explicitly flag changes to:

- negation;
- qualifiers/modality;
- numeric values and units;
- dates and temporal boundaries;
- variant identifiers;
- source identity;
- language and translation direction.

## Acceptance fixtures

Cover whitespace/HTML cleanup, Unicode normalization, structured-data reordering, OCR coordinate mapping, translation, chunking, lossy extraction, encoding conversion and failed transformation. Verify stable fingerprints, parent-child lineage, mapped/unmapped span states and explicit propagation of claim-critical changes.

## Authority boundary

This contract defines provenance for transformations. It does not decide claim truth and does not create a second evidence store, mapper or publication gate. Existing evidence and verification authorities remain canonical.

Repository tests establish contract behavior. Approved runtime evidence remains separately required for L4 claims.
