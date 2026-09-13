# Research Intelligence Engine — Expanded Planner Knowledge Ledger

Status: September 13, 2026

Purpose: preserve the full planner design discovered across the current architecture, historical extractor/scraper/mapper work, research-engine plans, testing notes, and continuity discussions. This is a design/knowledge ledger, not permission to bypass protected policy and not a claim that every feature below is already implemented.

## 1. Planner mission

The planner is not merely a list of stages. It is the bounded decision system that turns a user Research/Task Contract into an explicit, inspectable, resource-bounded strategy.

The planner must decide, before execution where possible:

- what kind of task this is
- what facts/claims are required
- what evidence quality is required
- what source families and languages are required
- which acquisition representations are appropriate
- which methods should be tried first
- how much parallelism is safe
- which fallbacks are allowed
- what conditions justify escalation
- what conditions justify stopping
- what uncertainty must be preserved
- what must be persisted for replay/evaluation/learning

The planner does not decide final truth. It proposes bounded work; policy, acquisition, evidence, verification and publication gates retain their own authority.

## 2. Non-negotiable planner constitution

Priority order:

1. security/privacy/source access and platform policy
2. strict $0 economic policy and hard quota state
3. provenance/integrity requirements
4. explicit user constraints
5. evidence requirements
6. deterministic efficiency
7. learned operational preference
8. heuristic convenience

Planner invariants:

- unknown quota/billing state cannot become allow under strict-$0 mode
- the plan may not widen its own hard envelope
- AI may propose strategy but cannot create evidence authority
- a failed transport is not an empty result
- inaccessible, blocked, partial, stale, contradictory and error states stay distinct
- source count is not independence
- a successful method does not become permanently preferred without measured evidence
- learned strategy cannot override hard policy
- no unbounded retry/fallback loop
- every escalation needs a bounded reason
- every plan should be serializable, fingerprintable and replayable

## 3. Planner inputs

### Required contract inputs

- question/task
- output type
- claims required or requested
- depth
- freshness/temporal requirement
- languages/locales
- required source families
- forbidden source families when supplied
- primary-source requirement
- community/UGC requirement
- contradiction requirement
- evidence-quality floor
- citation requirement
- exactness/precision requirement
- zero-cost requirement
- maximum search actions
- maximum browser actions
- maximum AI actions
- maximum pages/observations where applicable
- maximum bytes/artifact size where applicable
- maximum wall time
- concurrency ceiling
- user-specific restrictions

### Context inputs

The planner should also consume an explicit system-awareness snapshot:

- available capabilities and capability versions
- provider availability and health
- provider/account free/billing state
- remaining quota by dimension
- current network/source restrictions
- source profiles
- representation health
- recent method outcomes
- cached artifacts and snapshots
- prior run outcomes
- benchmark/replay information
- current deployment/evaluation version

Unknown state remains unknown. The planner may choose a safer reduced plan rather than guessing.

## 4. Task classification before query generation

The planner should classify the request into one or more task modes before selecting sources.

Core modes:

- fact lookup
- specification extraction
- comparison
- recommendation
- price/availability snapshot
- troubleshooting/diagnosis
- historical/temporal research
- change detection
- controversy/contradiction research
- community/experience research
- primary-source verification
- literature/document research
- entity identification/resolution
- structured catalog/product research
- file/document analysis
- code analysis
- dataset analysis
- media analysis
- mixed web + file/code/media research

Task mode changes the expected representation and evidence strategy. One universal scraper strategy is explicitly rejected.

## 5. Fact-type classification

Before choosing acquisition methods, classify each required fact/claim.

Useful fact classes include:

- identity: name, title, model, MPN, SKU, GTIN, version
- availability: stock, availability, access status
- commercial: price, currency, promotion, shipping
- specification: dimensions, ports, panel, refresh rate, memory, power, compatibility
- configuration: variant/options/tiers
- temporal: release date, current status, historical value, change
- qualitative: experience, sentiment, usability
- normative: policy, terms, rules
- relational: compatibility, ownership, dependency, comparison
- derived: calculations or synthesis explicitly derived from accepted inputs

Fast/explicit facts should prefer direct structured representations. Rich or ambiguous facts may require HTML/document context or browser escalation.

## 6. Claim decomposition

A complex question should be decomposed into atomic claim requirements before search planning.

For each claim track:

- claim_id
- normalized question
- expected fact type
- target entity/entities
- required precision
- freshness window
- preferred source hierarchy
- required independence level
- contradiction tolerance
- minimum evidence strength
- accepted uncertainty states
- completion condition

Derived recommendations must retain the underlying claims and evidence dependencies rather than being treated as free-form model output.

## 7. Query portfolio generation

The planner should generate multiple bounded query families instead of trusting one query.

Base portfolio:

1. exact/entity query
2. canonical-name/identifier query
3. synonym/alias query
4. primary-source targeted query
5. counterclaim/disconfirmation query
6. recent/freshness query
7. site-restricted query
8. citation-following query
9. multilingual query when relevant
10. community/experience query when explicitly required
11. alternative wording/query expansion when retrieval quality is weak
12. gap-specific query derived from missing claims

Each query should have a purpose, expected information gain, cost estimate, source-family target and stop condition.

The planner should not emit all possible queries blindly. It ranks candidates using expected value under the remaining run envelope.

## 8. Query generation dimensions

Query expansion should consider:

- aliases and spelling variants
- punctuation/hyphen normalization
- regional spelling/terminology
- language translation and transliteration
- entity + attribute combinations
- official domain restrictions
- document-type terms
- model/MPN/part-number variants
- version/year/date qualifiers
- negative/counterclaim phrasing
- forum/community terminology
- citation-chain anchors

Avoid uncontrolled synonym explosion. Expansion is bounded by action budget and marginal utility.

## 9. Source-family portfolio

The planner should plan diversity by source family, not just source count.

Potential families:

- official/first-party
- manufacturer/vendor
- standards/regulatory
- academic/technical
- reputable editorial/review
- community/UGC
- social/video
- regional/Chinese community
- user-provided files
- local artifacts/snapshots

A plan should be able to require specific families while preventing multiple pages from the same origin family from masquerading as independent corroboration.

## 10. Representation ladder

For each target source, plan candidates by representation rather than immediately choosing a transport.

Preferred order when permitted and sufficient:

1. documented public/authorized API
2. permitted feed/export
3. permitted structured/machine-readable endpoint or embedded state
4. JSON-LD/Microdata/OpenGraph/other metadata
5. static HTML/document extraction
6. browser/rendering

The planner may reorder this ladder based on a measured SourceProfile, but may not violate policy or security.

XHR/API discovery is a representation-discovery capability, not permission to bypass access controls.

## 11. Historical extractor/source intelligence lessons that belong in planning

The personal extractor work established planning-relevant patterns that should survive the architecture consolidation.

### Host/source profiles

A source profile may capture:

- platform hint
- supported representations
- endpoint patterns
- authentication mode
- preferred method
- method fallback order
- pagination style
- rate/pacing guidance
- concurrency ceiling
- challenge markers
- parser family
- field completeness behavior
- last-known-good route
- health/failure rates
- freshness characteristics
- profile/version timestamp

### Method fingerprinting

Represent each candidate acquisition method with a stable method fingerprint such as:

- source
- representation
- request shape
- parser/extractor version
- expected schema
- pagination contract
- evidence surface

This makes method performance comparable and replayable.

### Pagination planning

The planner must understand that pagination is not a generic page loop. It should plan based on observed pagination contracts:

- page number
- offset/limit
- cursor
- token/continuation
- link-based next page
- sitemap enumeration
- finite ID enumeration

Track:

- expected total hint when available
- pages/items observed
- repeated-page detection
- cursor repetition
- incomplete-page markers
- early termination reason
- completeness estimate

If a source advertises a total count, do not stop at an arbitrary small page sample when the task needs the full catalog. Completeness thresholds must be explicit.

### Repeated/duplicate page detection

Repeated page content should be treated as a stop/failure signal, not as successful additional observations. Record the reason and avoid wasting further requests.

### Bounded concurrency and pacing

The planner should assign per-source concurrency and pacing envelopes. A global concurrency value is insufficient.

Concurrency decisions should consider:

- recent 403/429/5xx rate
- documented/requested rate limits
- method type
- source health
- worker/runtime budget
- public/free quota

Escalation should often reduce concurrency instead of increasing it.

### Challenge/block classification

Distinguish:

- normal not-found
- authentication required
- policy blocked
- rate limited
- bot challenge/CAPTCHA
- transient server failure
- malformed response
- parser failure
- empty legitimate result

These states must lead to different recovery actions.

### Compression/encoding awareness

Some machine-readable APIs can appear empty or malformed when compression/encoding handling is wrong. Planner diagnostics should permit transport/decoding recovery before classifying a source as empty.

### Source-specific method flags

The historical extractor had useful source-specific learned flags such as:

- omit a problematic parameter on a source
- prefer one structured method over another
- disable known incomplete feed paths
- use a platform-specific parser family
- use an alternate API flow when GraphQL/structured route returns insufficient data

These belong in a versioned SourceProfile or capability record, not scattered hard-coded planner branches.

### Quarantine

Repeatedly failing methods should enter cooldown/quarantine with a reason, timestamp and recovery criteria rather than consuming the entire run budget.

## 12. Acquisition method scoring

Each candidate method should be scored using measured signals such as:

- expected evidence directness
- source authority
- completeness
- historical success rate
- freshness
- latency
- request cost
- byte cost
- browser/AI cost
- failure probability
- policy compatibility
- privacy constraints
- replayability
- parser stability
- expected information gain

A useful conceptual score is:

`utility = evidence_value * expected_success * expected_completeness * freshness_factor * independence_value - resource_cost - risk_penalty`

This is a planning heuristic, not truth scoring and not permission authority.

## 13. Learned routing

Learned routing should be observational first.

For each source/method combination retain:

- attempts
- successes
- partial successes
- blocked outcomes
- parser failures
- completeness
- field-level coverage
- latency distribution
- resource use
- freshness delay
- evidence quality outcomes
- last success/failure
- confidence/sample size
- strategy version

Use recency weighting plus sample-size safeguards. A one-off success must not outweigh a large stable history.

Learned preferences reorder permitted methods; they do not create new permissions.

## 14. Adaptive depth

Planner depth should be adaptive but bounded.

Start with the minimum strategy sufficient for the requested quality floor.

Escalate when:

- required claims are still uncovered
- evidence quality is below floor
- contradictions are unresolved
- freshness is inadequate
- source family diversity is insufficient
- independence is insufficient
- primary-source requirement is unmet
- extraction is partial
- confidence is ambiguous
- a source is stale or blocked

Reduce/stop when:

- required claims are adequately covered
- required evidence floor is met
- contradictions are resolved or explicitly qualified
- additional search has low expected information gain
- remaining budget is better reserved for higher-value unresolved claims

## 15. Gap analysis and recovery planning

After each acquisition batch, compute a claim coverage map:

- satisfied
- partially satisfied
- unsupported
- contradicted
- stale
- inaccessible
- blocked
- ambiguous
- derived-only

Generate recovery actions from the gap, not from generic retry rules.

Examples:

- missing primary evidence -> primary-source query
- weak freshness -> recent query/document version
- contradiction -> independent-source/counterclaim search
- partial product catalog -> alternate pagination/representation
- parser failure -> alternate parser/method
- source blocked -> permitted alternate source
- community claim without primary -> first-party verification

## 16. Contradiction-aware planning

Contradiction is a planning trigger, not only a verification result.

When strong sources disagree, planner actions can include:

- acquire newer document version
- acquire source-of-record
- inspect exact evidence spans
- query counterclaims
- search independent origin family
- separate temporal validity
- identify product/model/variant mismatch
- detect regional/configuration differences

Never resolve a contradiction by majority count alone.

## 17. Independence-aware planning

The planner should estimate whether additional sources add independent information.

Useful checks:

- same publisher
- same source family
- same underlying data/feed
- republished text
- citation ancestry
- same corporate origin
- same document lineage
- synchronized copies

Once additional sources are mostly duplicates, redirect budget to another independent family or stop.

## 18. Freshness and temporal planning

Represent freshness explicitly:

- required freshness window
- observed timestamp
- publication timestamp
- last-updated timestamp
- temporal validity interval
- snapshot/document version

When currentness matters, a high-authority old page may be less useful than a newer authoritative source. When historical state matters, the planner must seek date-bounded evidence rather than current-page substitutes.

## 19. Citation-following planning

Citations from a strong source can become graph edges for targeted follow-up.

Planner should track:

- citation target
- whether target was retrieved
- target authority
- target independence
- citation depth
- target relevance
- whether it materially resolves a claim

Avoid unbounded citation-chain traversal. Set maximum depth and expected-gain thresholds.

## 20. Community and multilingual planning

When user requirements include Reddit/X/YouTube/Zhihu/Tieba/Douban/Bilibili/PTT or similar sources, plan them as explicit source families.

Separate:

- discovery value
- experience evidence
- sentiment
- factual evidence

Use authorized/appropriate access methods. Thin indexed samples are not evidence of consensus.

Multilingual planning should consider:

- original-language source retrieval
- translated query variants
- transliteration
- regional terminology
- machine translation as interpretation support rather than evidence substitution
- preservation of original source text/URL for verification

## 21. File/code/data/media planning

The same planner should be capable of planning non-web tasks.

File planning:

- identify format/schema
- inspect metadata
- determine extraction method
- estimate size/complexity
- preserve hashes and provenance
- choose deterministic parser before AI

Code planning:

- detect language/build system
- inspect structure/dependencies
- static analysis first
- sandbox execution only when explicitly allowed
- bounded network/resources
- tests/lint/type checks before acceptance

Data planning:

- infer schema without inventing meaning
- profile missingness/types/cardinality
- validate calculations
- preserve source rows/columns and transformations

Media planning:

- detect media type/codec/container
- choose deterministic metadata/transcript/frame/audio extraction first
- apply modality-specific model tools only where needed

The planner should produce a common TaskPlan while retaining modality-specific action types.

## 22. Resource planner

The plan should reserve resources by category, not only one total count.

Suggested dimensions:

- search actions
- HTTP requests
- browser sessions/actions
- AI calls
- tokens
- bytes downloaded
- artifact bytes stored
- CPU/time budget
- concurrency
- retries
- source-family slots
- verification budget

Reserve a recovery reserve where appropriate rather than spending 100% on first-pass acquisition.

## 23. Cost-aware provider planning

Before any provider/model/browser action, evaluate:

- current provider state
- billing/free state
- quota dimension remaining
- account ceiling
- gateway ceiling if used
- action cost estimate
- fallback provider availability

Most conservative gate wins.

Provider/model selection should use measured task fit and accuracy, not raw speed alone. Historical discussions explicitly warn that a fast/cheap model can be less accurate and therefore worse for evidence-sensitive research.

## 24. AI usage policy in the planner

Use deterministic methods first when they are sufficient.

Potential AI planner roles:

- classify ambiguous tasks
- generate bounded query candidates
- interpret schema/fields when deterministic extraction is insufficient
- adjudicate ambiguous semantic entailment
- summarize accepted evidence

AI may not:

- authorize restricted acquisition
- declare unsupported facts true
- bypass quota/cost gates
- replace provenance
- mutate protected policy

AI actions should carry model/provider version and evaluation context.

## 25. Browser escalation policy

Browser work is expensive and stateful. Planner should treat it as a constrained escalation.

Escalate only when:

- needed information is absent from permitted machine-readable surfaces
- rendering/interaction materially changes available evidence
- static extraction is demonstrably insufficient

Before escalation, record why cheaper representations were insufficient.

Browser plans should specify:

- target URL/path
- navigation/action ceiling
- expected evidence surface
- authentication state requirements
- allowed storage/cookie scope
- timeout
- failure classification
- fallback/stop rule

## 26. Execution graph

The planner should generate a DAG/step graph rather than only a flat stage list.

Nodes can represent:

- query
- source discovery
- representation probe
- acquisition
- pagination step
- artifact capture
- extraction
- claim mapping
- verification
- contradiction check
- independence check
- recovery action
- stop decision

Edges encode dependencies and conditional transitions.

Parallel branches are permitted only when resource reservations and source policies allow them.

## 27. Checkpointing and resumability

Long plans should emit checkpoints containing:

- plan fingerprint
- completed action IDs
- observations/artifacts captured
- budget consumed/remaining
- source health changes
- pending actions
- failure states
- strategy version

Resume must be idempotent. A repeated action must not duplicate evidence or exceed its budget because of a crash/retry.

## 28. Idempotency and side-effect planning

Any action with external side effects must have:

- stable operation ID
- idempotency key
- receipt
- retry semantics
- commit/ack state
- recovery policy

Research acquisition should remain as close to read-only as possible. Writes such as artifact persistence should be separately accounted and replayable.

## 29. Stop policies

A plan needs explicit stop reasons.

Suggested stop states:

- COMPLETE
- QUALITY_FLOOR_MET
- BUDGET_EXHAUSTED
- WALL_TIME_EXHAUSTED
- PRIMARY_SOURCE_UNAVAILABLE
- SOURCE_BLOCKED
- CONTRADICTION_UNRESOLVED
- INSUFFICIENT_INDEPENDENCE
- INSUFFICIENT_FRESHNESS
- PARTIAL_RESULT
- POLICY_DENIED
- ZERO_COST_DENIED
- NO_EXPECTED_GAIN
- SAFETY_DENIED
- ERROR

Never collapse all stop cases into success/failure.

## 30. Plan explainability

Every material plan decision should be explainable with compact machine-readable reason codes.

Examples:

- `FACT_TYPE_FAST_FACT`
- `PREFERRED_STRUCTURED_REPRESENTATION`
- `PRIMARY_SOURCE_REQUIRED`
- `COUNTERCLAIM_REQUIRED`
- `FRESHNESS_GAP`
- `PARTIAL_PAGINATION`
- `SOURCE_QUARANTINED`
- `INDEPENDENCE_GAP`
- `BROWSER_ESCALATION`
- `COST_GATE_DENIED`
- `LOW_EXPECTED_GAIN_STOP`

Store reason codes and evidence for learned routing decisions.

## 31. Plan fingerprinting and determinism

A ResearchPlan should be canonicalizable and hashed from:

- contract fingerprint
- planner version
- capability snapshot/version
- policy snapshot identifier
- source-profile snapshot identifiers
- chosen actions and ordering
- budgets
- fallback rules
- learned strategy versions

The same input state should generate the same plan unless an explicitly versioned nondeterministic component is used.

## 32. Planner evaluation

Planner quality must be evaluated independently from final answer quality.

Metrics:

- required-claim coverage
- evidence-floor attainment
- primary-source compliance
- contradiction discovery rate
- contradiction resolution rate
- independent-source coverage
- freshness attainment
- retrieval recall
- unnecessary-action rate
- average cost/resource burn
- browser escalation rate
- failed-action recovery rate
- source-method selection precision
- plan determinism
- replay equivalence
- time-to-sufficient-evidence
- overplanning/underplanning rate

Evaluate frozen plans against frozen scenarios before promoting planner changes.

## 33. Planner benchmark corpus

Build a planner-specific golden corpus covering:

- easy direct facts
- rich specification tasks
- conflicting sources
- stale/current conflicts
- community-only clues requiring primary verification
- catalog pagination/completeness
- blocked/429/403 scenarios
- duplicate/republished sources
- multilingual requests
- Chinese/community source cases
- citation chains
- structured-data vs browser tradeoffs
- file/code/media tasks
- strict-$0 provider/quota uncertainty
- partial retrieval and resume
- malformed payload/transport ambiguity

Initial bootstrap can be small, but production planner validation should expand toward 150–300 adversarial/representative cases as previously planned.

## 34. Cross-strategy testing

Planner alternatives should compete on frozen evidence/scenarios.

Examples:

- query portfolio A vs B
- structured-first vs browser-first
- provider/model routing A vs B
- source-family diversification strategy A vs B
- aggressive vs conservative escalation
- pagination strategy A vs B

Compare accuracy/evidence coverage/resource cost, not just latency.

Shadow execution should observe candidate strategies without affecting protected production behavior.

## 35. Controlled self-improvement

Planner learning loop:

`observe outcome -> record strategy result -> propose candidate strategy -> replay/frozen eval -> shadow -> canary -> promotion/rollback`

Candidate strategy state must include:

- hypothesis
- scope
- strategy fingerprint
- evidence basis
- benchmark results
- resource results
- regression results
- approval state
- rollback target

Never let planner learning directly rewrite hard security/economic/source policies.

## 36. Extractor/mapper boundary

Historical extractor and mapper features are a source of planner knowledge, not a reason to collapse boundaries.

The planner may request an extraction capability and provide:

- fact/field requirements
- completeness target
- pagination expectation
- preferred method families
- resource envelope
- evidence/provenance requirements

The acquisition/extraction owner remains responsible for performing network and parser operations.

The mapper remains responsible for semantic identity/entity resolution after observation.

Mapper-specific lessons that can influence planning:

- strong identifiers should be sought before weak names
- variants must remain distinct
- price must not become product identity
- hard conflicts should trigger review or alternate evidence
- oversized candidate blocks should be treated as incomplete evidence unless independently resolved
- deterministic blocking should reduce search space before expensive matching
- candidate recall matters in addition to candidate count

## 37. Product/catalog-style planning lessons

When the requested research resembles structured catalogs:

- plan completeness explicitly
- detect source-provided total counts when reliable
- use platform-native bulk/structured paths where permitted
- treat each variant as a potentially distinct observation
- preserve offer/price/stock volatility separately from identity
- avoid expensive fuzzy matching before deterministic identifiers
- measure candidate recall after blocking
- use reusable indexes instead of rebuilding indexes for every query
- benchmark normalization/index/candidate/batch/full-pipeline separately

These are transferable planning principles even when the final system is not a product crawler.

## 38. Security and abuse resistance in the planner

The planner itself can be attacked by prompt injection or hostile source content.

Therefore:

- source text is data, never planner policy
- embedded instructions in web pages/files cannot change budgets or policy
- tool output cannot silently add capabilities
- retrieved content cannot authorize itself
- planner state must be schema validated
- action parameters require policy validation after planning
- suspicious source behavior should reduce trust/quarantine rather than unlock more power

## 39. Planner output contract — target design

A future expanded ResearchPlan should contain at least:

- plan_id
- plan_version
- contract_id/fingerprint
- question/task summary
- task modes
- claim requirements
- source-family requirements
- source candidates
- query portfolio
- representation/method candidates
- ordered action graph
- dependency edges
- budget reservations
- concurrency/pacing rules
- fallback rules
- escalation conditions
- stop conditions
- contradiction strategy
- independence strategy
- freshness strategy
- checkpoint policy
- idempotency policy
- expected evidence outputs
- required artifacts
- reason codes
- planner/capability/policy fingerprints
- learned-strategy references
- evaluation hooks

## 40. Implementation sequencing after design freeze

The planner is being designed before broad implementation by intent.

Recommended order after the feature/design inventory is accepted:

1. expand immutable contract types
2. implement plan schema + validation + fingerprint
3. implement task/fact/claim classification hooks
4. implement bounded query portfolio generation
5. implement source-family and representation strategy objects
6. implement deterministic method scoring
7. implement budgets/concurrency/pacing policy objects
8. implement adaptive gap/recovery planner
9. implement contradiction/independence/freshness planning
10. implement execution DAG/checkpoints/idempotency contracts
11. implement planner evaluation harness/golden corpus
12. add source-profile/learned-strategy integration
13. integrate acquisition/extractor/mapping owners through stable contracts
14. add shadow/canary strategy evaluation

Do not prematurely copy historical extractor branches into planner.py. The planner should describe work; acquisition/extraction remains the execution owner.

## 41. Continuity rule

When later chats add planner discoveries, update this file or a versioned successor in GitHub before considering the knowledge settled.

Do not rely on conversation memory as the sole project memory.

When a planner feature is rejected, record:

- proposal
- source/evidence
- rejection reason
- replacement strategy
- date/version

This ledger exists specifically to prevent the loss of extractor/scraper/mapper lessons and prior planning decisions between chat sessions.
