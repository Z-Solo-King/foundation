# Planner implementation status — September 13, 2026

This record ties the feature-first planner ledger to code without pretending protected integrations are complete when their authoritative evidence is missing.

## Merged public planner foundation

Foundation PR #23 completed and merged after Python 3.13/3.14, 307-test, 100% coverage and public-boundary validation.

### Implemented
- Expanded ResearchContract with output, claim, freshness, language, source-family, evidence, contradiction, search/browser/AI and wall-time controls.
- Typed task modes/fact types, claims/fields/coverage/failure/pagination/stop states.
- Deterministic bounded query portfolio generation and acquisition method scoring.
- Source-profile-aware and field-preference-aware routing.
- Route negative memory with cooldown, quarantine, recovery and planner filtering.
- Protected recovery-reserve accounting in the deterministic budget ledger.
- Action DAG validation, deterministic ordering, canonical serialization/fingerprints and replay bundles.
- StrategyCard/RetryPolicy/CacheProfile/TokenBudget/TokenDecision contracts.
- Deterministic evidence selection, deduplication and context packets with answer/verification reserves and stable cache identities.
- 150-case production/adversarial evaluation corpus.
- Evaluation receipts plus immutable evaluation-input/artifact binding.
- Calibrated semantic entailment; semantic AI adjudication remains advisory and ambiguous-only.
- Enriched EvidenceCertificate provenance, temporal, version, lineage, retention and replay metadata.
- DocumentVersion and version-aware claim snapshots.
- Integrity/poisoning metrics: retrieval/origin concentration, temporal anomalies, disagreement and UGC ratio.
- External-service limit observations and fail-closed route activation guards.
- Shadow/canary/promotable/promoted/rollback strategy lifecycle.
- Sandboxed-code contracts where upload never implies execution.
- Universal artifact manifests with content identity and retention metadata.
- Token efficiency and research-regret/evidence-gain evaluation metrics.

### Cloudflare implementation retained
- Existing Workers/D1/R2 integration remains the runtime/persistence implementation.
- Public health/readiness and infrastructure diagnostic contracts remain in place.
- No duplicate Cloudflare control plane was introduced by the planner work.

## Still required / externally gated

1. Integrate planner field/pagination plans into actual Operations acquisition/extractor consumers.
2. Connect planner reservations to the protected Operations resource authority; Operations PR #53 remains open.
3. Establish durable protected replay/capability/policy/source version records.
4. Expand the 150-case corpus toward 300 real-source golden/adversarial cases.
5. Close end-to-end semantic/independence/freshness/regret/poisoning evaluation wiring across protected execution.
6. Connect strategy lifecycle to protected promotion storage/rollback authority.
7. Complete production file/code/data/media execution adapters while retaining the sandbox boundary.
8. Apply GitHub repository governance: ruleset, secret scanning/push protection, stable CodeQL/dependency checks, OIDC trust, attestations and merge queue where actually supportable.
9. Re-verify current live Cloudflare production health/readiness/D1/R2 evidence before claiming production deployment DoD.

## Deliberate boundaries

- Foundation planner performs no network I/O.
- Foundation never holds provider secrets or protected policy authority.
- Planner learning cannot mutate protected policy/security/billing/source-access rules.
- Mapper remains acquisition-free.
- Public workers remain untrusted until trusted evaluation accepts their outputs.

## Validation rule

A green public test suite proves public implementation behavior. Protected Operations, live provider/source-access, deployment, billing/quota, and production Cloudflare claims require their own authoritative evidence gates.