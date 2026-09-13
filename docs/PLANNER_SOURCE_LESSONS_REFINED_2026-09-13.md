# Planner Source Lessons — Refined Findings from Historical Audits

Status: September 13, 2026

This file records additional planner-relevant findings surfaced by older extractor/scraper/mapper audits and research-plan reviews. It supplements `PLANNER_KNOWLEDGE_LEDGER_2026-09-13.md` and exists to prevent loss between chats.

## 1. Evidence-resolution core

The reusable system core is not simply search or an LLM. The planner should optimize the path through:

`observation -> provenance -> source lineage -> evidence span -> claim -> corroboration -> contradiction -> temporal validity -> publication`

Research is the first application. The planner therefore should be reusable for due diligence, technical investigation, product comparison, monitoring, fact checking, literature review and similar evidence-resolution tasks.

## 2. Freshness is source-dependent

Freshness must not be modeled only as a user query requirement. Source types have different expected validity half-lives.

Planner concept:

- `freshness_required`
- `source_freshness_profile`
- `observed_at`
- `published_at`
- `updated_at`
- `expected_validity_window`
- `temporal_validity`

For example, pricing/news/current-status sources usually require tighter freshness than stable standards or historical documentation. The exact values must be empirically calibrated rather than hard-coded as universal constants.

## 3. Evidence processing order

Avoid sending every problem directly to a model. The preferred escalation order is:

`deterministic -> structured -> lexical -> statistical -> semantic -> generative`

The planner should encode this as a strategy preference, while allowing measured exceptions where a later method demonstrably provides better evidence coverage/accuracy at acceptable cost.

Do not turn reliability into one universal 0–100 confidence scalar. Reliability is multi-dimensional: authority, independence, freshness, completeness, entailment, contradiction state and other properties should remain inspectable.

## 4. Source diversity is harder than source count

A source-count target is easy to game because many pages can originate from the same data or publisher.

Planner checks should prefer:

- origin family diversity
- publisher independence
- data-feed independence
- citation ancestry
- temporal independence where relevant
- republisher detection

When marginal sources are duplicates, planner budget should move to an independent source family or stop.

## 5. Historical extractor architecture principles that directly affect planner design

Historical V111/V168/V158/V75-era work repeatedly enforced these patterns:

- `context -> policy -> discovery -> plan -> transport -> adapter -> normalize -> identity/merge -> quality/domain rules -> output -> learn`
- one public function per responsibility
- common abstraction first, protocol adapter second, source facts in profiles/config, unique exceptions last
- data/config before adding code branches
- no patch-stack architecture
- no split-brain runtime state
- learning may tune ranking/pacing/concurrency/endpoint preference/recovery choice but must not rewrite hard rules
- historical code should become behavioral facts, regression tests, profiles or contracts rather than copied layers

Planner implication: method selection, source quirks, cooldown/concurrency state and strategy preference need one canonical owner and one explicit representation. Do not create a second “smart planner” inside acquisition or mapper code.

## 6. Canonical owner map for runtime-changing state

The historical audits identify these ownership boundaries:

- rate/cooldown/concurrency -> recovery/source health state
- endpoint health -> endpoint health state
- method preference -> unified planner/learning state
- product identity -> canonical identity engine
- cache freshness -> shared transport/cache state
- browser session -> browser/session owner

Planner may consume these states and choose actions but should not duplicate them.

## 7. Catalog completeness planning

Historical extractor behavior introduced several useful planning signals:

- declared total count vs observed count
- bounded legacy result windows
- source-specific completeness markers
- optional detail enrichment for variable/option-bearing entities
- batch splitting after explicit URI-length failure
- explicit unknown stock semantics where source stock flags are unreliable

Planner should therefore treat “retrieved some records” and “catalog coverage is complete enough” as separate states.

For large structured collections, the plan should specify a completeness objective and preserve the declared-vs-observed reconciliation evidence.

## 8. Candidate matching efficiency is a planner concern

Historical mapper audits found that rebuilding an index per query can turn a bounded candidate algorithm into an accidental O(Q*N) pattern.

Planner/benchmark design must distinguish:

- reusable-index path
- accidental rebuild-per-query path
- candidate-block size
- truncation rate
- candidate reduction ratio
- candidate recall against truth
- full pipeline throughput

Small candidate counts are not automatically efficient if recall falls.

## 9. Identity-first planning

For structured/entity resolution tasks, planner should seek strong deterministic identifiers before expensive fuzzy or AI matching.

Historical identity hierarchy included signals such as:

- GTIN
- brand + MPN
- brand + manufacturer ID
- brand + model
- source-specific product ID
- URL
- seller SKU

Strong identifiers can be automatic evidence candidates; conflicting strong identifiers should trigger review/alternate evidence.

Variants remain distinct. Price and stock are offer/state fields, not identity.

## 10. Security findings relevant to planner design

Historical audits found that even URL normalization can become a security boundary. Planner-generated targets therefore require purpose-specific URL handling and validation.

Do not assume a syntactically plausible URL is safe.

Planner outputs must be validated again by the acquisition/security owner; plan generation is never the final security gate.

## 11. Recovery as a first-class planner feature

The historical extractor uses explicit recovery budgets and a recovery-decision owner. Planner should therefore represent recovery as a bounded subgraph instead of a generic retry counter.

Recovery should distinguish:

- transient retry
- pacing reduction
- alternate representation
- alternate parser
- alternate source family
- batch split
- browser escalation
- cooldown/quarantine
- terminal stop

Each path requires a bounded budget and a reason.

## 12. Feature-flag/profile rule

When a behavior varies by host/source because of endpoint, page size, delay, field path, feature flag or known exception, prefer data/profile configuration over a new algorithm branch.

The planner should consume versioned capability/profile data rather than accumulating source names and if/else rules.

## 13. Knowledge preservation rule

Every useful historical behavior should be captured in one of four forms before implementation:

1. invariant
2. profile/config field
3. regression fixture/benchmark case
4. explicit rejection with reason

This is the preferred way to preserve the extractor/scraper/mapper corpus without recreating its old architecture.

## 14. Planner feature ordering implication

The planner should be completed as a feature inventory and contract design before broad implementation.

The current stage-list implementation is intentionally inadequate as the final design. The next design pass should complete the plan schema, decision graph, resource model, adaptive recovery model, source/method strategy model, observability/replay fields and evaluation contract before deeper code is written.
