# Research Evidence and Execution Contracts

**Status:** canonical Foundation research/evidence contract family
**Scope:** public-safe research correctness, evidence, transformation, publication and evaluation inputs

## Request and publication
A normalized research request carries objective/subquestions, required scope, freshness/temporal requirements, evidence/citation requirements, allowed source/tool classes, deadline, resource envelope and publication/privacy constraints.

Result states remain explicit: `QUEUED`, `RUNNING`, `COMPLETED`, `PARTIAL`, `DEGRADED`, `BLOCKED`, `FAILED`, `CANCELLED`, `UNSUPPORTED`.

Public publication requires requested scope, claim support, source/evidence integrity, freshness, contradiction state, provenance completeness and disclosure eligibility. Provider success alone is not publication success.

## Evidence integrity
Acquired sources retain canonical URL/host identity, content fingerprint, source family, retrieval time, freshness and evidence eligibility. Discovery is not evidence until acquisition/integrity validation succeeds. Mirrors/syndication remain linked to their source family.

Unknown dates remain unknown. Historical evidence cannot silently satisfy a current-freshness requirement.

## Bounded research stopping
Continue/stop decisions consider coverage, independent corroboration, contradictions, novelty/marginal gain, freshness, remaining budget, deadline and acquisition failure state. Required dimensions cannot be skipped solely because expected marginal value is low. Redundant evidence must not consume unlimited resources.

## Evidence transformation lineage
For parsing, normalization, OCR, translation, chunking and other transformations preserve parent artifact/document version, transformation type/version, input/output fingerprints, execution identity, language/encoding, warnings/confidence, exact span mapping or explicit `MAPPING_LOST`, and inherited access/retention classification.

Derived evidence never silently gains authority. Numeric values, units, negation, qualifiers, dates, variant identifiers and source identity must be preserved or explicitly flagged as changed.

## Execution identity
`execution-identity/v1` is a correlation primitive for idempotency, replay, caching/coalescing, evaluation and provenance. Correctness-bearing inputs may include normalized request semantics, capability, execution mode, policy/schema versions, freshness class, tool/source inputs, provider/model configuration and research-plan identity.

Canonicalization is deterministic. Secrets and unnecessary private content are excluded.

Execution identity never grants authorization, resources, evidence truth or publication authority. Reuse paths still enforce current authorization, freshness, policy and budget.

## Evidence graph indexing
D1 remains the canonical graph store. Reverse indexes accelerate claim/evidence, evidence/document, document/source, source/lineage and observation/run traversals.

Indexes mirror canonical rows; they do not create semantic relationships. Rebuilds are deterministic, resumable and non-destructive, and incomplete rebuilds remain explicitly degraded/unavailable.

## Source access and multilingual acquisition
Source access, retention and disclosure are separate from evidence truth. Acquisition may use deterministic/static fetch, structured data, search discovery or authorized browser execution. Every lane declares capability, authorization, cost and permitted fallback.

Search output is discovery data, not evidence. SSRF/redirect/source-safety controls apply to every resolved destination.

Multilingual records retain source language, original spans and transformation identity. Translation/normalization remains derived evidence and must preserve dates, quantities, units, negation and qualifiers.

## Typed contradictions
Contradictions are compared semantically, not by broad lexical mismatch. Candidate generation is bucketed by compatible entity/predicate/temporal window/scope before expensive comparison.

Missing/unknown values do not contradict. Version, region and time-window differences remain distinct unless an explicit compatibility rule applies. Unit conversion is deterministic and provenance-preserving.

## Uncertainty and abstention
Preserve support, evidence sufficiency, contradiction, freshness, source independence, qualification and abstention reason.

`UNKNOWN` is not low-confidence support. `CONTRADICTED` is not averaged into a settled result. Missing calibration remains explicit. Numeric confidence/calibration never overrides hard evidence/security/policy gates.

## Verified synthesis
The synthesizer receives only admitted claim/evidence references and state needed to present the resolved result. Every material factual assertion must be a projection of an admitted claim, an explicitly marked inference from admitted claims, or an explicit unknown/limitation statement.

It must not invent sources, evidence references, timestamps, measurements or verification state. Translation, summarization and compression cannot strengthen or erase material qualifiers, negation, units, temporal scope, contradiction or gaps.

## Evaluation and artifact boundaries
Evaluation corpora should cover deterministic facts, multi-source research, contradictions, temporal cases, multilingual evidence, citation precision, source-family duplication, adversarial content, incomplete execution, provider/source failure and long-running/resource-heavy cases.

Measure correctness, completeness, evidence coverage, citation precision, source independence, freshness, contradiction state, reliability, latency, resource/token efficiency and safety independently. Critical dimensions may independently block publication/promotion.

Uploaded/generated artifacts carry type, size/safety classification, schema/content fingerprint, parser/generator version, provenance, validation status, retention policy and publication eligibility. Image-derived facts remain derived evidence with provenance/version metadata. Repository/code analysis treats repository content as data unless separately authorized for execution.

## Authority rule
This document composes existing evidence, resource, verification and publication authorities. It does not create a second evidence store, evaluator, resource ledger, provider selector or publication engine.

Repository tests establish these contracts; runtime/production claims remain separately evidence-gated.
