# Planner / research-intelligence implementation status — September 13, 2026

This record ties the September 2026 feature-first ledger to code and deployment boundaries. It deliberately distinguishes implemented deterministic primitives from still-unintegrated protected runtime work.

## Platform already implemented

- Cloudflare Workers public execution boundary is implemented.
- Cloudflare D1 persistence is implemented and covered by repository tests.
- Cloudflare R2 artifact persistence is implemented and covered by repository tests.
- Public health/readiness/infrastructure diagnostics exist; live deployment evidence must still be rechecked after any redeploy.
- Cloudflare implementation is not being duplicated in the planner branch.

## Implemented in planner PR #23

### Contract and core models
- Expanded ResearchContract with output, claim, freshness, language, source-family, evidence, contradiction, search/browser/AI and wall-time controls.
- Typed task modes and fact types.
- Typed claim and field requirements.
- Coverage, failure, pagination and stop-state taxonomies.
- Method candidates, source plans, actions and resource envelopes.
- `recovery_reserve_ratio` is enforced by runtime reservation rather than remaining declarative only.

### Deterministic planning
- Task classification with specification-task precedence.
- Claim decomposition.
- Bounded query portfolio generation with language/source-family variants.
- Query purpose/source-family/claim targeting.
- Deterministic acquisition method utility scoring.
- Source-profile-aware method ranking hook.
- Field-preference-aware method ranking without bypassing normal utility scoring.
- Gap-specific recovery actions.
- Field-aware representation route scoring contracts.
- Bounded pagination planning with expected-total limits.
- Repeated-page and repeated-cursor detection.

### Route memory and recovery
- Deterministic route key/state model covering source + method + representation.
- Exponential cooldown for retryable empirical failures.
- Immediate quarantine for policy/auth/captcha-style empirical failures.
- Threshold quarantine for repeated failures.
- Explicit recovery transition and success reset.
- Planner method selection filters empirically quarantined/cooldown routes while retaining unseen and recovered routes.
- Route memory remains empirical state only; it does not replace protected source policy or billing authority.

### Resource, replay and external-limit controls
- Explicit action dependency DAG.
- Cycle and missing-dependency validation.
- Deterministic topological order.
- Deterministic canonical plan serialization/fingerprint.
- Explain-plan diagnostics.
- Basic hard/soft stop logic.
- Protected recovery reserve accounting for ordinary resource reservation, with explicit recovery override.
- Immutable replay bundle with contract/plan/context fingerprints including quota/freshness context.
- Context-drift compatibility checks.
- External-service limit observations with explicit VERIFIED/STALE/UNKNOWN/CONTRADICTORY states.
- Route activation guards require a fresh verified limit observation with sufficient observed capacity.
- Unknown quota is never converted into an assumed free allowance.

### Token/context efficiency
- Strategy cards combining evidence quality, completeness, latency, resources, risk, token multiplier, cacheability and retry economics.
- Exact/prefix cache-aware token decisions.
- Explicit verification/final-answer token reserves.
- Deterministic context packets with evidence-token budgets, duplicate suppression, dropped-evidence accounting and stable content/prefix cache identities.

### Evidence, evaluation and integrity
- Immutable evaluation input snapshots with contract/plan/candidate/baseline/capability/policy/source-profile/corpus/oracle identities.
- Evaluation artifacts bind receipts to immutable input snapshots and result fingerprints; they do not grant promotion authority.
- Deterministic-first entailment remains the default; calibrated semantic scoring can adjudicate only already-ambiguous cases.
- Semantic calibration profiles are versioned and bounds-validated.
- Deterministic 150-case production corpus covering retrieval, extraction, contradiction, temporal, independence, citation, freshness, resource, security and architecture classes with adversarial/stale/poison/replay/lineage/recovery variants.
- Integrity metrics for retrieval concentration, source-family concentration, temporal anomalies, disagreement and UGC ratio.
- Integrity metrics are observational; they do not directly promote/reject sources.

### Evidence certificates and research memory
- EvidenceCertificate now preserves optional document version, temporal scope, source-family, extractor version, mapper version, retention state and replay fingerprint.
- Certificate verification fail-closes on content, identity and provenance drift.
- DocumentVersion is now first-class with parent version, extractor/mapper versions, retention state and deterministic fingerprint.
- ClaimSnapshot preserves document-version/evidence lineage, revision number and parent snapshot while retaining legacy constructors.

### Universal artifacts and code safety
- ArtifactManifest supports file/code/data/document/media kinds with schema version, size, media type, producer, retention and metadata.
- Artifact content hash and byte-size verification are deterministic.
- Sandboxed CodeExecutionRequest/Result contracts explicitly require sandbox identity; uploaded code never implies execution.
- Code execution policy requires bounded runtime/output/memory and rejects undeclared network access.
- No code execution occurs in this public module.

### Adaptive learning / strategy lifecycle
- Replan triggers for gaps, contradictions, source degradation, capability/quota/policy/freshness changes and method failures.
- Recovery action selection and failed-method filtering.
- Replayable source/method profile observations.
- Sample-size-aware method success/completeness updates.
- Bounded multi-metric strategy comparison.
- Per-metric quality non-regression guard so efficiency cannot hide a quality regression.
- Shadow → canary → promotable → promoted lifecycle records with explicit rollback, while public evaluation remains non-authoritative for protected production promotion.

### Compatibility and boundary hardening
- Existing `create_plan()` compatibility facade preserved.
- Canonical `create_task_plan()` lives in `planner_engine`; compatibility module delegates to it.
- Field requirements flow from ResearchContract into TaskPlan/action field IDs.
- Legacy Observation positional constructors preserved while provenance/hash validation remains fail-closed.
- Public workers remain untrusted until trusted evaluation accepts their results.

## Still required before the broader roadmap is complete

1. Integrate pagination plans into actual Operations acquisition execution and completeness certificates.
2. Bind replay bundles to canonical protected capability/source/policy version records and durable replay artifacts.
3. Connect planner reservations to the protected Operations runtime resource authority. Operations PR #53 contains the adapter but is not merged because its GitHub Actions jobs currently suffer a repeatable `steps=null` / `BlobNotFound` log-artifact failure; that is not treated as a code-green result.
4. Add 150–300 real-source golden cases in addition to the deterministic public 150-case corpus, plus property/metamorphic/differential/fuzz/replay suites.
5. End-to-end integrate integrity metrics into publication/evaluation and research-regret measurements.
6. Integrate the shadow/canary lifecycle with protected Operations promotion/rollback authority; public state must remain advisory.
7. Integrate planner route memory, representation selection, pagination and limit guards with Operations acquisition/extractor consumers without duplicating policy ownership.
8. Complete file/code/data/media planner execution adapters and sandbox implementations behind protected authority.
9. Complete GitHub repository governance gaps: main ruleset, secret scanning/push protection, OIDC trust with Cloudflare, artifact attestations, and merge queue after `merge_group` checks are proven.

## Deliberate boundaries

- Planner performs no network I/O.
- Planner never holds provider secrets.
- Planner does not bypass source policy.
- Planner learning cannot modify protected policy.
- Planner does not contain scraper/browser implementations.
- Mapper remains acquisition-free.
- Public workers remain untrusted until trusted evaluation accepts their results.

## Validation rule

A green unit suite proves implementation behavior only. Live provider, deployment, source-access, zero-cost and protected-resource claims require their own authoritative evidence gates.