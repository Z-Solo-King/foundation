# Planner implementation status — September 13, 2026

This record ties the feature-first planner ledger to code without pretending the entire roadmap is implemented.

## Implemented in planner PR #23

### Contract and core models
- Expanded ResearchContract with output, claim, freshness, language, source-family, evidence, contradiction, search/browser/AI and wall-time controls.
- Typed task modes and fact types.
- Typed claim requirements.
- Coverage, failure and stop-state taxonomies.
- Method candidates, source plans, actions and resource envelopes.

### Deterministic planning
- Task classification.
- Claim decomposition.
- Bounded query portfolio generation.
- Query purpose/source-family/claim targeting.
- Deterministic acquisition method utility scoring.
- Source-profile-aware method ranking hook.
- Gap-specific recovery actions.

### Execution planning
- Explicit action dependency DAG.
- Cycle and missing-dependency validation.
- Deterministic topological order.
- Plan serialization/fingerprint.
- Explain-plan diagnostics.
- Basic hard/soft stop logic.

### Learning primitives
- Replayable source/method profile observations.
- Sample-size-aware method success/completeness updates.
- Bounded multi-metric strategy comparison.
- Candidate rejection on correctness/trust/reliability/efficiency regression.

## Next grouped implementation slices

1. Field-aware evidence requirements + representation planning + pagination/completeness contracts.
2. Plan invalidation/replanning + adaptive depth + recovery reserve + negative route memory.
3. Immutable replay bundle + plan version binding to capability/source/policy records.
4. Stronger resource reservation integration with the canonical runtime resource authority.
5. Planner benchmark corpus + property/metamorphic/differential/fuzz/replay tests.
6. Evidence/evaluation integration: certificates, semantic entailment, source independence and research-regret signals.
7. Shadow/canary planner strategy lifecycle and verified strategy-memory promotion.
8. Cross-repository integration with acquisition/extractor field-route consumers.

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
