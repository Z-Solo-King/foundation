# Research Intelligence Engine — Knowledge Ledger

Status: September 13, 2026

This file preserves durable project knowledge discovered across prior conversations, uploaded research packages, the AI archive, personal extractor/mapper work, the current Foundation repository, and current GitHub documentation. It is a continuity record, not a new policy authority. Current code and explicit protected policy remain authoritative when this ledger conflicts with implementation.

## 1. Canonical current architecture

Active repositories:

- `Z-Solo-King/foundation`: public-safe research execution surface, evidence semantics, deterministic observed-data core, public Worker, public CI and tests.
- `Z-Solo-King/operations`: private authority for protected policy, orchestration, credentials, private state, provider governance, deployment and protected promotion.
- Historical extractor/mapper material: retained as engineering lineage and compatibility evidence, not a third active security boundary.

This reconciles the earlier three-family design into the current two-repository active architecture. One canonical owner per behavior remains mandatory. Compatibility layers must not become shadow implementations.

## 2. Constitutional rules

Priority order:

1. Security, privacy and source-access rules.
2. Platform/provider policy and authorization requirements.
3. Strict $0 economic policy.
4. Provenance and evidence integrity.
5. Explicit user constraints.
6. Verified primary evidence.
7. Independent corroboration.
8. Learned operational preference.
9. Heuristic convenience.

Hard rules:

- Unknown billing/quota state is a hard deny in strict-$0 mode.
- AI interpretation is never evidence authority by itself.
- Unknown, inaccessible, contradictory, stale, partial, inferred, blocked and error states remain distinct.
- Source count is not source independence.
- Public Worker output is untrusted data until schema, provenance, hashing/replay and evaluation gates accept it.
- Learning is observational, reversible and non-destructive.
- Protected policy cannot be modified by a self-evolution loop.
- Private workers and credentials must not become public.
- Never weaken authentication to make CI green.
- Never claim live provider verification from unit tests or configuration inspection.
- Do not add paid infrastructure merely to improve a benchmark or obtain green CI.
- Uploaded code is never executed merely because it was uploaded; execution requires isolation and explicit resource/network controls.

## 3. Canonical end-to-end method

`User request -> Research/Task Contract -> System Awareness + Policy/Budget Gate -> Planner -> Capability/Source Router -> Acquisition -> Deterministic Observation/Artifact -> Retention + Integrity + Lineage -> Entity/Claim/Evidence Mapping -> Adversarial Verification -> Gap Search/Recovery -> Budget-Aware Stop -> Publication Gate -> Answer + Snapshot/Artifact -> Post-Run Evaluation -> Shadow -> Canary -> Rollback/Promotion -> Verified Memory/Learned State`

The provider layer is replaceable. The evidence model is not.

## 4. Research Contract requirements

A request can carry:

- question
- output type
- claims required
- freshness requirement
- language requirements
- required source families
- primary-source requirement
- community-evidence requirement
- contradiction requirement
- evidence-quality floor
- maximum search actions
- maximum browser actions
- maximum AI actions
- wall-time limit
- strict zero-cost requirement

Planner behavior is bounded. It may adapt method/provider/depth before spending resources, but may not expand beyond the declared envelope.

Recommended query portfolio:

- exact/entity
- synonyms/aliases
- primary-source targeted
- counterclaim/disconfirmation
- multilingual
- recent/freshness
- site-restricted
- citation-following

## 5. Acquisition methodology

Preferred representation order is fact-aware, not crawler-first:

`documented permitted API -> permitted feed/export -> permitted structured/machine-readable surface -> permitted HTML/page -> browser/rendering only when the requested fact cannot be obtained adequately earlier`

Examples:

- Fast facts such as price, stock, availability, explicit SKU/MPN and structured pagination should prefer authorized machine-readable paths.
- Rich specifications should prefer official specification data, structured data and deterministic HTML extraction before browser escalation.
- API/XHR discovery is useful only when the endpoint is actually permitted and discoverable from the source. It must not become a mechanism for bypassing access controls.
- JSON-LD, Microdata, OpenGraph and other embedded structured data should be extracted before model interpretation when it contains the requested fact.
- Browser automation is a fallback, not the universal default.
- CAPTCHA/bot-protection evasion, fingerprint masking, proxy rotation and similar bypass techniques are not architecture requirements.

## 6. Source intelligence

The long-term design requires persistent source profiles containing, where known:

- source/domain identifier
- source family/origin
- permitted acquisition methods
- representation candidates (API/feed/XHR/JSON-LD/HTML/browser)
- method health/success rate
- HTTP failure distribution (403/404/429/etc.)
- parser/extractor success rate
- field completeness
- freshness behavior
- pagination behavior
- authentication/access requirements
- policy/retention constraints
- request limits
- quarantine state
- extractor/version identifier
- evidence quality by fact type
- replay/test history
- learned preferred method

Repeated failures must lead to bounded backoff, quarantine or local-required state rather than brute-force retries.

## 7. Observation and provenance model

Observation is the immutable factual unit. It should preserve:

- observation_id
- source_id/source_url
- source family/origin
- document_id/document version
- content
- observed/retrieved time
- publication/updated time when known
- language/title/author when available
- acquisition method
- extraction method
- extractor version
- artifact reference
- content hash
- raw/normalized hashes where useful
- quality/status/policy state
- lineage/replay information

EvidenceSpan identifies exact offsets within an Observation. Evidence certificates bind a claim/evidence reference to the observed content hash and structural span. Future certificate work should add temporal scope, document version, source-family independence, extractor/mapper version, retention state and replay metadata.

## 8. Evidence model

Claims must be traceable to evidence spans and observations.

Evidence ranking should remain inspectable and deterministic first, using signals such as:

- evidence role
- relevance
- credibility/authority
- freshness
- independence/origin family
- contradiction status
- completeness
- source diversity
- source concentration
- temporal consistency

Repeated/republished evidence must not masquerade as independent corroboration.

The system should retain the distinction between evidence score and truth. Ranking identifies useful evidence; it does not prove that the evidence is true.

## 9. Verification methodology

Verification is multi-stage:

1. Structural validation.
2. Source URL/access validation.
3. Observation/hash validation.
4. Exact evidence-span validation.
5. Deterministic lexical/field-level checks.
6. Typed contradiction checks.
7. Temporal checks.
8. Source-origin/independence checks.
9. Claim-strength/evidence adequacy checks.
10. Semantic/AI adjudication only for genuinely ambiguous cases.
11. Publication gate.

The semantic layer must not override hard contradictions, provenance failures or policy failures.

Current lexical entailment is conservative but incomplete. The planned next step is calibrated semantic entailment evaluation with adversarial fixtures and explicit false-positive/false-negative measurement.

## 10. Content integrity and poisoning defense

Research over user-generated/community sources must assume adversarial or low-integrity content is possible.

Track and benchmark:

- source concentration
- source-family concentration
- duplicate/near-duplicate concentration
- origin-family concentration
- temporal anomalies
- abrupt synchronized claims
- disagreement density
- citation-chain depth
- UGC trust tier
- republisher dependence
- evidence completeness
- suspicious retrieval patterns

Community material is useful for discovery, sentiment, experience reports and triangulation, but should not automatically outrank official/primary evidence for factual claims.

Historical reviews identified research-poisoning risk in UGC/deep-research settings. Treat this as a permanent security/evaluation concern rather than a one-off bug.

## 11. Evaluation methodology

Evaluation must be separate from generation and separate from promotion.

Required corpus families:

- retrieval
- extraction
- contradiction
- temporal
- independence/lineage
- citation/evidence
- freshness
- resource efficiency
- security/poisoning
- architecture/boundary
- user-quality/usefulness
- multilingual/community-source cases
- file/code/media cases

The historical plan uses 50-case bootstrap and 150–300-case production targets. Those are roadmap targets, not proof thresholds by themselves.

An evaluation receipt should bind:

- candidate version
- frozen baseline version
- benchmark corpus fingerprint
- oracle/evaluator version
- evaluator code fingerprint
- evidence set/artifact fingerprint
- metrics
- resource usage
- timestamps
- pass/fail decision
- environment/runtime metadata

Evaluation should support replay and independent verification without granting public promotion authority.

## 12. Testing methodology — current and required

Already present/valuable:

- unit tests
- branch coverage gate
- fail-closed edge tests
- contract tests
- worker boundary tests
- persistence/diagnostic tests
- public/private family boundary tests
- live HTTP smoke checks
- production infrastructure verification
- CodeQL
- deterministic public boundary scans

Required expansion:

- golden corpus regression suites
- property-based tests for contracts and parsers
- metamorphic tests for normalization/extraction/routing invariants
- fuzz tests for hostile/malformed inputs
- differential tests comparing two extractors/methods against the same evidence set
- replay tests from immutable observation/artifact bundles
- pagination/retry/429/403/CAPTCHA/partial-response fixtures
- temporal regression fixtures
- UGC poisoning/adversarial fixtures
- cross-source independence fixtures
- cross-strategy A/B evaluation on frozen evidence
- performance/resource-budget benchmarks
- live canary tests after deployment
- deployment drift detection tied to commit/version
- explicit recovery/idempotency tests for side effects and pending writes

Do not use 100% branch coverage as the only quality measure. Branch coverage proves exercised code paths, not factual correctness, retrieval quality or operational resilience.

## 13. Controlled self-evolution

The intended learning loop is:

`observe -> propose candidate -> sandbox -> regression -> shadow -> canary -> accept/rollback`

Every proposed improvement needs:

- frozen baseline
- candidate version/fingerprint
- explicit hypothesis
- pre-registered metrics
- bounded test corpus
- resource/cost ceiling
- failure criteria
- rollback mechanism
- retained evaluation receipt

Examples of learnable behavior:

- preferred permitted source representation for a site/fact type
- source/provider health
- query pattern quality
- extraction method performance
- evidence-selection utility
- token/resource efficiency
- failure/blocked-state patterns

The learning loop must never directly mutate hard policy, credentials, security boundaries or billing policy.

## 14. Operational system awareness

The chatbot should maintain an explicit machine-readable capability/state model, not a vague “self-aware” concept.

It should know:

- which providers/tools exist
- which are currently usable
- source/API restrictions
- quotas and quota dimensions
- billing/free eligibility state
- provider/source health
- acquisition methods that worked/failed
- research gaps
- evidence quality
- current run budget
- prior run outcomes
- capability/version history
- artifact/file/media support

Operational loop:

`know state -> plan -> check limits -> act -> measure -> adapt -> finish -> review -> learn -> test -> improve`

Unknown state must never silently become an allow decision under strict $0 policy.

## 15. Cost and quota methodology

Economic controls are independent of any one gateway.

The authorization decision must consider:

- provider/account billing state
- provider-specific quota
- account-level hard ceiling
- gateway budget/estimate
- remaining run budget
- historical burn rate

The most conservative gate wins.

AI Gateway telemetry or estimated spend is not sufficient as the sole $0 authority.

Provider quota must be modeled by dimension where relevant: requests, tokens, pages, bytes, executions, daily/monthly credits, concurrency and service-specific units.

Provider capabilities should include `verified_at`, `free_state`, `availability_state`, and beta/billing-transition information where applicable.

## 16. AI Gateway and privacy

AI Gateway can expose request/response/logging metadata. Therefore every AI call must have a data-classification policy.

Recommended policy fields:

- data_classification
- provider_allowed
- gateway_allowed
- gateway_logging
- prompt_logging
- response_logging
- prompt_retention
- response_retention
- redaction_policy
- training_use_policy
- regional_constraint
- deletion_deadline

Private data should default to minimal or disabled prompt/response logging unless explicitly permitted.

## 17. Files, code, data and media are first-class research inputs

The universal-learning plan deliberately expands beyond web pages. A file/code/data/media object can be:

- research source
- evidence bundle
- constraint
- dataset
- comparison target
- transformation input
- output target

The same Task, Observation, Evidence, Artifact and Evaluation contracts should apply across web and files.

Artifact metadata should include:

- artifact_id
- media type/format
- schema/format version
- provenance/source references
- creation timestamp
- tool/model versions
- validation status
- retention classification
- hashes

Generated code should be syntax/lint/test checked when tooling is available. Generated spreadsheets should preserve meaningful formulas/structure/formatting where appropriate.

Private files must not flow into public GitHub workers unless explicitly authorized by security policy.

## 18. Archives and personal engineering assets

The personal V175 extractor and V18/product-mapper family contain useful engineering patterns, including:

- host/source profiles
- bounded pagination
- limited concurrency
- explicit delays
- source-specific extraction methods
- deterministic identity signals
- conflict detection
- human confirmation
- calibrated thresholds
- explainable match signals
- versioned learned match models
- replay/backfill orientation
- quarantine instead of brute-force retry

These should be generalized into contracts, not copied wholesale as a second architecture.

## 19. Multilingual and community-source strategy

Reddit, X/Twitter, YouTube, Zhihu, Douban, Tieba, Bilibili, PTT and similar sources can be useful, but access and evidence quality differ by platform.

Rules:

- Use official/authorized access where required.
- Keep source-specific health/access state.
- Treat community content as evidence with an explicit trust tier.
- Do not claim a community consensus when the available sample is thin.
- Chinese/community recommendations from reviews are idea sources; they are not automatically architecture facts.
- Platform-specific legal/policy requirements override convenience.

## 20. Infrastructure sequencing

Current strict-$0 core:

- Cloudflare Workers
- D1 for compact state/index/projections
- Backblaze B2 for large evidence/artifacts
- GitHub public Actions for public CI/testing

Conditional/later:

- Queues for bounded fan-out
- Workflows for long-running durable research
- AI Gateway for multi-provider transport/routing/observability
- Vectorize only after retrieval benchmarks justify it
- Durable Objects only when measured coordination/state needs justify them
- KV is not another durable source of truth

Do not add infrastructure merely because it is available.

## 21. GitHub operating model

Current public-repository rule:

- Foundation is the heavy public CI/test surface.
- Do not restore dependence on private GitHub-hosted Actions for bulk work.
- Public CI proves public-code behavior; it does not certify private runtime behavior.

GitHub hardening target:

- `main` ruleset
- pull request required
- public-tests required
- no force push / deletion
- stable CodeQL required check after observing exact check name
- merge queue only after merge_group checks are proven
- secret scanning + push protection enabled in settings
- Dependabot for Actions and Python dependencies
- dependency review added only when dependency churn warrants another required check
- OIDC deployment only after Cloudflare trust is verified end-to-end
- artifact attestations when a real release/package artifact exists

All third-party Actions should stay pinned to full commit SHAs.

## 22. Deployment truth model

Deployment state is evidence, not assumption.

Minimum live sign-off:

1. CI green.
2. /health green.
3. /readiness green.
4. Deployed commit/version matches source under test.
5. Authenticated diagnostic route exists in the deployed Worker.
6. D1 live path passes.
7. B2 round-trip passes with artifact/hash/size evidence.
8. Residual risks recorded.

A stale Worker returning 404 for a newly implemented route is deployment drift, not proof that the source implementation is broken.

## 23. Known historical deployment blocker to preserve

Earlier live tests demonstrated that /health and /readiness could remain green while the deployed Worker was stale relative to the source. The authenticated infrastructure verifier then returned 404.

This established an important test principle: **health/readiness are necessary but insufficient**. The smoke suite must exercise an application capability tied to the current code path.

Cloudflare credential/account configuration previously prevented safe redeployment. Secrets must never be placed in source or logs.

## 24. Knowledge quality rules

When future research or AI reviews produce a claim:

1. Preserve the claim and its source.
2. Classify it as fact, design recommendation, hypothesis, observation, or rejected claim.
3. Prefer primary documentation/reproducible code for platform facts.
4. Record disagreements instead of silently averaging them.
5. Do not promote a community anecdote into a platform fact.
6. Do not retain unsupported numerical claims merely because they sound useful.
7. When a plan changes, retain why the old approach was rejected.
8. Every major architectural change should record what evidence caused it.

Historical examples of claims that were explicitly rejected/qualified include unsupported DORA-stopping claims, unsupported Graphiti latency percentages, unsupported LineageRAG retrieval numbers, simplistic assumptions that AI Gateway spend estimates are authoritative billing, and blanket assumptions that a specific platform/API is always available or free.

## 25. Current Foundation implementation matrix

### Implemented or substantially present

- research contracts and API scaffolding
- deterministic planner foundations
- source/acquisition abstractions
- evidence observations/spans
- content hashing/integrity
- source lineage/independence
- claims/relationships/contradictions
- evidence certificates
- evidence selection and context budgeting
- evaluation harness and bootstrap corpus
- deterministic entailment with explicit ambiguous state
- adaptive/provider/resource router foundations
- research-run lifecycle
- public Worker boundary and fail-closed task/result validation
- public persistence and diagnostics
- stage receipts
- token-efficiency metrics/gates
- chatbot run records
- public CI with branch coverage gate
- CodeQL
- public boundary scans
- SHA-pinned Actions
- Dependabot Actions monitoring
- public deployment/smoke path
- EvaluationReceipt in the September 2026 hardening branch
- enriched Observation provenance in the September 2026 hardening branch

### Partial / needs completion

- semantic entailment/calibration
- rich evidence certificates
- source profiles and persisted source behavior learning
- representation discovery (API/XHR/feed/structured/browser) as a first-class learned capability
- temporal document/version model
- artifact retention/replay metadata
- adversarial content-integrity metrics
- multilingual/community adapter family
- cross-strategy evaluation
- golden benchmark corpus beyond bootstrap size
- file/code/media intelligence contracts
- durable pending-write recovery
- production evaluation receipt persistence and replay verification
- deployment drift detection beyond smoke checks

### Not yet implemented / later controlled stages

- shadow strategy evaluation engine
- canary learning with rollback
- protected promotion integration
- long-term source deterioration/change detection
- verified research memory promotion
- benchmarked vector/semantic retrieval upgrade
- broad media/3D capability layer
- full universal artifact/file/code execution sandbox

## 26. Explicit implementation backlog

P0:

- keep PR #21 test-clean
- validate current public CI on the final hardening commit
- complete live deployment verification after Cloudflare setup
- keep current source/deployed-version evidence aligned

P1 evidence/evaluation:

- enrich EvidenceCertificate
- build EvaluationReceipt persistence/replay verifier
- expand benchmark corpus toward 150–300 cases
- add adversarial poisoning/UGC/temporal/lineage fixtures
- calibrate semantic entailment

P1 acquisition/source intelligence:

- SourceProfile contract + health history
- representation discovery record
- method success/failure ledger
- bounded method fallback and quarantine
- external-limit verification record

P1 execution/reliability:

- pending-write recovery
- idempotent side-effect receipts
- replay bundles from immutable observations/artifacts
- differential/malformed-input/fuzz fixtures

P1 universal inputs:

- FileFormatCapability registry
- artifact contract
- isolated code execution contract
- generated-artifact validation

P2 controlled learning:

- cross-strategy evaluator
- shadow router
- canary/rollback controller
- verified memory promotion boundary

P2 retrieval:

- benchmark deterministic retrieval against semantic/search indexes
- add Vectorize/AI Search only if measured gain justifies it and free-state is independently verified

## 27. Do not regress these architectural decisions

- Do not recreate the retired third repository as a new source of truth.
- Do not copy the old extractor/mapper wholesale into Foundation as a second implementation.
- Do not use AI as an evidence authority.
- Do not count URLs as independent sources.
- Do not weaken authorization for deployment/tests.
- Do not let public CI require private CI quota.
- Do not assume free-tier or beta pricing without current verification.
- Do not use a gateway spend estimate as the sole $0 control.
- Do not add browser automation before simpler permitted representations are tested.
- Do not let a new source method bypass policy/access checks.
- Do not enable autonomous production mutation.

## 28. Source hierarchy for future sessions

Highest trust for platform facts:

1. Current official provider/GitHub documentation.
2. Current reproducible repository/code.
3. Current live tests with recorded evidence.
4. Maintained external engineering documentation.
5. Community reports/reviews used as hypotheses or operational signals.
6. Unverified AI summaries only as ideas to investigate.

Historical project documents preserve intent and reasoning but do not override current provider documentation or current repository reality.

## 29. Continuity requirement

When a new session begins, first compare:

- this knowledge ledger
- current GitHub tree/CI
- latest final plan
- open implementation issues/PRs
- live verification status
- current provider documentation

Then update the ledger when a material decision changes. The project should accumulate knowledge rather than repeatedly rebuild it from chat history.
