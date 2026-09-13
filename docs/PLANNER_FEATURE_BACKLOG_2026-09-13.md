# Planner Feature-First Backlog — September 13, 2026

This backlog deliberately separates **planner design completeness** from **implementation**. The current priority is to capture the complete feature surface before coding the planner deeply.

## Priority P0 — planner design completeness

- [ ] ResearchContract expanded schema: output type, claims, freshness, languages, source families, evidence floor, contradiction/independence requirements, strict-$0 mode, action budgets, wall time, bytes/pages/tokens/concurrency ceilings.
- [ ] Task-mode taxonomy: fact, spec, comparison, recommendation, temporal, contradiction, community, primary-source verification, entity resolution, file/code/data/media.
- [ ] Fact-type taxonomy and directness rules.
- [ ] Claim decomposition and claim coverage model.
- [ ] Query portfolio generator: exact, identifier, synonym, primary, counterclaim, recent, site-restricted, citation-following, multilingual, community, gap-recovery.
- [ ] Query candidate utility/expected-information-gain model.
- [ ] Source-family portfolio and independence targets.
- [ ] Representation ladder and method candidate model.
- [ ] SourceProfile/representation profile references.
- [ ] Method fingerprints and strategy fingerprints.
- [ ] Pagination strategy taxonomy and completeness planning.
- [ ] Repeated-page/cursor detection planning state.
- [ ] Per-source concurrency/pacing planning.
- [ ] Failure taxonomy: empty, 403, 404, 429, 5xx, CAPTCHA/challenge, auth, parser failure, malformed payload, partial response.
- [ ] Quarantine/cooldown/recovery rules.
- [ ] Adaptive depth rules and escalation triggers.
- [ ] Gap analysis and targeted recovery planning.
- [ ] Contradiction-aware planning.
- [ ] Independence-aware planning.
- [ ] Freshness/temporal planning.
- [ ] Citation-following planning with bounded depth.
- [ ] Multilingual/community-source strategy.
- [ ] File/code/data/media planning.
- [ ] Resource reservation by dimension.
- [ ] Provider/model selection with strict-$0 gate.
- [ ] Browser escalation contract.
- [ ] Execution DAG with conditional edges.
- [ ] Checkpoints/resume/idempotency design.
- [ ] Explicit stop-state taxonomy.
- [ ] Explainable reason codes.
- [ ] Canonical plan serialization/fingerprinting.
- [ ] Planner evaluation metrics and golden corpus.
- [ ] Cross-strategy A/B/shadow/canary design.
- [ ] Controlled planner-learning state.

## Priority P1 — first implementation wave after design freeze

1. Immutable contract and plan dataclasses with strict validation.
2. Canonical plan fingerprint and deterministic serialization.
3. Task/fact/claim classification interfaces.
4. Query portfolio object model and bounded deterministic generator.
5. Source-family and representation requirement objects.
6. Budget/resource reservation model.
7. Deterministic strategy scoring primitives.
8. Gap/coverage state and adaptive recovery planner.
9. Explicit contradiction/independence/freshness requirement objects.
10. Plan DAG/conditional action schema.
11. Stop reasons and structured plan diagnostics.
12. Planner-only tests and benchmark fixtures.

## Priority P1 — integration contracts

- Acquisition consumes planned method candidates without inheriting planner policy.
- Extractor consumes fact/field and completeness requirements without moving into planner ownership.
- Mapper consumes the resulting observations and remains network-free.
- Evidence/verification consumes the claim/evidence requirements without accepting planner output as truth.
- Operations remains authority for protected policy, global provider governance, promotion and rollback.

## Priority P2 — adaptive intelligence

- Persist SourceProfile outcomes.
- Learn method preference with sample-size and recency safeguards.
- Detect source deterioration/change.
- Compare strategies on frozen evidence.
- Shadow candidate planner strategies.
- Canary approved planner strategies.
- Roll back on regression.
- Promote verified strategy memory.

## Historical extractor/mapper features explicitly preserved for later implementation

The following came from prior extractor/scraper/mapper work and are intentionally included in planner requirements rather than lost:

- platform/host profiles
- source-specific permitted method ordering
- API/feed/structured/HTML/browser representation discovery
- source-specific parameter quirks represented as versioned profile data
- bounded pagination and total-count hints
- completeness thresholds
- repeated-page detection
- cursor repetition detection
- per-host delay/concurrency
- 403/429/challenge classification
- retry cooldown/quarantine
- gzip/encoding diagnostics before classifying a machine-readable response as empty
- deterministic identifier-first matching
- variant separation
- price/stock volatility separate from identity
- candidate blocking before expensive matching
- oversized-block telemetry and recall measurement
- conflict detection and abstention
- calibrated matching thresholds
- replay/backfill orientation
- reusable indexes instead of rebuilding indexes per query
- full-pipeline benchmarking rather than helper-only benchmarks

## Explicit non-goals

- No network code inside the planner.
- No scraping/browser implementation inside the planner.
- No provider secret handling inside the planner.
- No protected policy mutation by planner learning.
- No duplicate policy engine.
- No uncontrolled autonomous strategy expansion.
- No paid infrastructure requirement.
