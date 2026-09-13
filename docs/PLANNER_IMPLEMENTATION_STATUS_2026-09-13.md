# Planner implementation status — September 13, 2026

This record ties the feature-first planner ledger to code without pretending the entire roadmap is implemented.

## Implemented in planner PR #23

### Contract and core models
- Expanded ResearchContract with output, claim, freshness, language, source-family, evidence, contradiction, search/browser/AI and wall-time controls.
- Typed task modes and fact types.
- Typed claim and field requirements.
- Coverage, failure, pagination and stop-state taxonomies.
- Method candidates, source plans, actions and resource envelopes.

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

### Execution planning and replay
- Explicit action dependency DAG.
- Cycle and missing-dependency validation.
- Deterministic topological order.
- Deterministic canonical plan serialization/fingerprint.
- Explain-plan diagnostics.
- Basic hard/soft stop logic.
- Immutable replay bundle with contract/plan/context fingerprints including quota/freshness context.
- Context-drift compatibility checks.

### Adaptive planning and learning
- Replan triggers for gaps, contradictions, source degradation, capability/quota/policy/freshness changes and method failures.
- Recovery action selection and failed-method filtering.
- Replayable source/method profile observations.
- Sample-size-aware method success/completeness updates.
- Bounded multi-metric strategy comparison.
- Per-metric quality non-regression guard so efficiency cannot hide a quality regression.

### Compatibility and boundary hardening
- Existing `create_plan()` compatibility facade preserved.
- Canonical `create_task_plan()` lives in `planner_engine`; the compatibility module delegates to it.
- Field requirements now flow from ResearchContract into TaskPlan/action field IDs.
- Legacy Observation positional constructors preserved while provenance/hash validation remains fail-closed.
- CPython test bootstrap handles environments where `workers-py` is installed but no normal `workers` module exists.

## Still required before planner roadmap is complete

1. Connect field-aware route selection directly to the real acquisition consumers and source-route memory.
2. Integrate pagination plans into actual acquisition execution, completeness certificates and source-level route memory.
3. Add adaptive depth/de-escalation, recovery reserve accounting and negative route memory/quarantine/cooldown.
4. Bind replay bundles to canonical capability/source/policy version records and deterministic replay artifacts.
5. Connect planner reservations to the protected Operations runtime resource authority; planner-supplied envelopes must not become budget authority. Operations PR #53 provides the adapter but remains unmerged and currently has no historical test CI until its new workflow is accepted.
6. Build the planner golden corpus and property/metamorphic/differential/fuzz/replay suites; expand toward the 150–300 production corpus with adversarial cases.
7. Integrate EvidenceCertificate, calibrated semantic entailment, independence, freshness, research-regret and poisoning/integrity metrics end-to-end.
8. Implement shadow/canary planner strategy lifecycle, rollback and verified strategy-memory promotion.
9. Integrate the planner with Operations acquisition/extractor field-route consumers without duplicating policy ownership.
10. Complete universal file/code/data/media planning contracts, sandboxed code execution and retention-aware artifact manifests.

## Deliberate boundaries

- Planner performs no network I/O.
- Planner never holds provider secrets.
- Planner does not bypass source policy.
- Planner learning cannot modify protected policy.
- Planner does not contain scraper/browser implementations.
- Mapper remains acquisition-free.
- Public workers remain untrusted until trusted evaluation accepts their results.

## Validation rule

A green unit suite proves implementation behavior only. Live provider, deployment, source-access and zero-cost claims require their own authoritative evidence gates.
