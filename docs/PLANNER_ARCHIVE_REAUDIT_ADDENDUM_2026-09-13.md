# Planner Archive Re-audit Addendum — September 13, 2026

This addendum records planner capabilities that became clearer after re-reading the newly supplied `ai starter 1..6` files, the universal-learning final plan, later execution/handoff records, and the historical extractor/mapper lessons. It supplements `PLANNER_KNOWLEDGE_LEDGER_2026-09-13.md` and `PLANNER_FEATURE_BACKLOG_2026-09-13.md`.

## Newly made explicit planner requirements

### 1. Requested-field planning
The planner must map requested facts/fields to the representations most likely to expose those fields. A specification task and a simple identity/price task should not receive the same acquisition plan.

A plan may carry `requested_fields`, `field_families`, `preferred_representations`, `required_evidence_modes`, and `field_completion_state`.

This directly preserves the later field-routing work: acquisition/extractor receives representation hints but does not become the planner owner.

### 2. Evidence-mode planning
A requested fact may require different evidence modes:

- structured value
- textual span
- table/cell
- image text/OCR
- image/visual attribute
- PDF page/render
- video transcript
- video frame
- user-provided artifact

The planner must preserve these as separate evidence surfaces so one modality cannot silently overwrite another.

### 3. Cross-modal conflict planning
When structured text, image text, manufacturer data, retailer data, or secondary databases disagree, the planner should create a verification task rather than choose a winner silently.

Examples include image/spec conflicts, retailer/manufacturer disagreements, and variant/image reuse. Rarity or suspicious price/spec combinations can raise verification priority but must never be treated as automatic falsity.

### 4. Canonical context-budget planning
The planner must consume the canonical context allocator rather than implementing local token logic. Evidence, instructions, question, output and reserve space should remain distinct. Repeated/equivalent context should be cacheable using a deterministic cache identity.

The planner should reserve recovery/context headroom rather than spending the complete model budget on the first pass.

### 5. Accuracy-aware strategy routing
Cheap/fast is not sufficient. Strategy selection must consider measured task accuracy/correctness alongside latency, resource consumption and failure rate. A fast strategy that produces systematically weaker evidence must lose to a slower strategy when the task quality floor requires accuracy.

### 6. Planner invalidation and re-planning
A plan is valid only against the state under which it was created. Material changes in provider quota, billing, source health, source policy, capability versions, time/freshness or retention constraints must invalidate or revalidate the relevant actions.

This prevents a planner from executing stale assumptions merely because the serialized plan remains syntactically valid.

### 7. Explicit action prerequisites
Every action in a future execution DAG should declare:

- required capability
- source/policy eligibility
- resource reservation
- input artifacts/claims
- expected observation type
- possible failure states
- retry/fallback rules
- side effects
- checkpoint/idempotency key
- completion condition

The planner creates the action contract; canonical owners execute it.

### 8. Negative-result semantics
The planner must distinguish:

- source genuinely contains no matching record
- source was not searched deeply enough
- pagination incomplete
- extraction failed
- source blocked/inaccessible
- entity mismatch
- fact absent from the representation

A negative observation is not automatically proof that the fact is false or nonexistent.

### 9. Completeness-aware stopping
Historical extractor testing showed that a low number of returned items can look successful while being materially incomplete. Planner stopping therefore requires an explicit completeness target when the task requires catalog/list coverage.

Use total-count hints, pagination progress, repeated-page detection, cursor state, page/item counts and termination reason together. A target such as "enough evidence for the requested claim" is different from "full catalog coverage".

### 10. Recovery is an evidence problem, not a retry problem
Planner recovery should be selected from the observed failure/gap:

- transport/encoding issue -> transport recovery
- parser failure -> alternate parser/representation
- 429 -> cooldown/reduced concurrency
- 403/CAPTCHA -> permitted alternate surface/source
- partial catalog -> pagination/completeness recovery
- contradiction -> independent-source/date/variant investigation
- missing primary evidence -> primary-source query
- stale evidence -> newer document/version search

Unbounded retry is never the generic recovery algorithm.

### 11. Learning memory must be replayable
Any learned method preference must record enough state to reproduce why the preference changed:

`source + representation + method fingerprint + observation/result + extractor/parser version + resource usage + evidence quality + timestamp + strategy version`

One-off success is insufficient. Sample size, recency and stability matter.

### 12. Strategy components are composable, not a swarm
Query strategy, retrieval method, parser, extractor, mapper, verifier, ranking rule and browser strategy can be represented as bounded strategy components and evaluated in combinations. Candidate cross-products must be capped.

The planner can propose a better combination; the canonical owner applies it after evaluation. This is controlled cross-learning, not autonomous agent proliferation.

### 13. Research regret belongs in the stopping model
Stopping should consider not only whether the current evidence floor is met but whether important evidence is likely still discoverable. The planner can continue when the expected value of unresolved evidence is high, but must stop when marginal information gain is low relative to remaining resources and recovery reserve.

### 14. Refresh planning is incremental
A previous research snapshot should be reusable. The planner should identify stale/changed claims, sources, documents or contradictions and refresh only affected components instead of repeating the complete research run.

### 15. Human feedback is learning evidence, not policy authority
User corrections, operator review and labeled outcomes can improve strategy quality. They must be captured as observations/evaluation labels and pass the same regression/evaluation lifecycle. They cannot directly mutate source-access, security, billing, privacy or evidence-authority policy.

### 16. Capability absence is a first-class planning gap
When the system cannot perform a required task, the planner should emit a structured capability gap containing required capability, missing prerequisite, possible alternative methods and research/discovery actions. It should not invent a capability or silently fall back to an unverified method.

### 17. Plan explainability
A planner should be able to answer, for each action:

- why this method was selected
- which alternatives were rejected
- what evidence/failure history affected the choice
- expected cost
- required quality/completeness target
- stop/escalation condition

This creates a durable audit trail for later strategy learning and debugging.

## Deliberately rejected planner patterns

- Universal one-scraper strategy.
- Browser-first acquisition.
- LLM-first extraction for deterministic facts.
- Source-count voting.
- Single scalar confidence score as truth.
- One global concurrency setting for all sources.
- Infinite fallback chains.
- Treating transport failure as empty data.
- Treating rarity as proof of bad data.
- Treating image-derived data as automatically more or less authoritative than structured data.
- Planner-owned network code.
- Planner-owned protected policy.
- Autonomous direct production mutation.

## Design freeze target

Planner design is ready for implementation only when the following can be represented without inventing a new ad-hoc field or hidden branch:

`Task -> Claims -> Fact/Field requirements -> Evidence requirements -> Source-family targets -> Representation candidates -> Method candidates -> Resource reservations -> Conditional DAG -> Stop/escalation rules -> Expected observations -> Gap/recovery rules -> Replay fingerprint -> Evaluation criteria`

The planner remains proposal/coordination logic. Acquisition, evidence truth, mapper semantics, verification authority, resource authority and protected policy remain owned by their canonical components.
