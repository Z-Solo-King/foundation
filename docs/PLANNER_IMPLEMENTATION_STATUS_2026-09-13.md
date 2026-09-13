# Planner implementation status — September 14, 2026

This record distinguishes validated public implementation from protected/live gates and preserves the established chatbot-based Cloudflare verification path.

## Completed public foundation

Foundation PR #23 is merged at `cf61ee1faef1fe7a702ea4d02e39d0b9bde1696b` after successful Python 3.13/3.14 CI: 307 tests, 100% branch/line coverage, workflow-policy validation, public-boundary scan, and context-budget validation.

Implemented public capabilities include:
- deterministic task/claim/field/query/method planning;
- source-profile routing and negative route memory with cooldown/quarantine/recovery;
- protected recovery-reserve accounting;
- DAG planning, deterministic fingerprints and replay bundles;
- StrategyCard/RetryPolicy/CacheProfile/TokenBudget/TokenDecision contracts;
- deterministic evidence selection/context packets with token reserves and stable cache identities;
- 150-case production/adversarial corpus;
- immutable evaluation input/receipt/artifact binding;
- calibrated semantic entailment with AI adjudication restricted to ambiguous cases;
- enriched evidence certificates, document versions and versioned claim snapshots;
- integrity/poisoning metrics and external-service limit guards;
- shadow/canary/promotable/promoted/rollback lifecycle primitives;
- sandboxed-code contracts where upload never implies execution;
- artifact manifests and token-efficiency/research-regret metrics.

## Cloudflare status

Cloudflare Workers/D1/R2 integration is existing implementation, not an unfinished planner task. The authoritative production verification route is the existing GitHub Actions chain: `public-tests` → `deploy-public-worker` → `production-chatbot-deploy-smoke`. The smoke workflow verifies public Worker health and then calls the authenticated chatbot diagnostic operation `infrastructure_verify_public_test`, which checks `public_chatbot`, `cloudflare_d1`, and `backblaze_b2_lifecycle`.

A local DNS/network failure must not be interpreted as a Cloudflare production failure; this environment cannot directly resolve the production Worker hostname. Cloudflare is therefore verified through the established chatbot/control-plane bridge.

## Protected integration completed

Operations PR #53 is merged at `5a91e026da6e1453c50703a75979080db47a1a12`. The planner-to-Operations resource bridge maps planner envelopes into the canonical protected `ResourceLedger` with atomic rollback, browser-time rounding, storage accounting, and consume/release receipts. Independent local execution of the bridge suite passed 9/9 after correcting two faulty rollback/field assertions in the original PR tests.

Operations PR #54 is merged at `bc136f56dce728c2a7732f16ce307e8b5b72b248`. The protected execution bridge routes untrusted planner fields into the existing chatbot field-routing consumer, validates bounded action/pagination directives, propagates planner fingerprints, and reserves serialized planner resource envelopes through the canonical ledger. Independent local execution of the exact bridge/edge suite passed 7/7 after correcting a real mapping-vs-object resource-envelope bug.

GitHub's Operations `private-tests` workflow repeatedly terminates before job steps materialize (`steps=null`) and its log endpoint returns `BlobNotFound`; this is a GitHub runner-observability defect, not executable test evidence. Do not treat it as hosted private CI green.

## Remaining true gates

1. Connect planner field/pagination plans to the actual permitted acquisition/extractor execution consumer beyond the protected routing/resource bridge.
2. Establish durable protected replay/capability/policy/source version records and end-to-end evaluation consumption.
3. Expand the corpus from 150 deterministic/adversarial cases toward 300 real-source golden cases.
4. Wire independence/freshness/regret/poisoning metrics through protected publication/evaluation.
5. Connect strategy lifecycle to protected promotion storage/rollback authority.
6. Complete protected file/code/data/media execution adapters while retaining the sandbox boundary.
7. Apply admin-level GitHub governance: main ruleset, secret scanning/push protection, stable CodeQL/dependency checks, Cloudflare OIDC trust, attestations, and merge queue where supported.
8. Obtain an authoritative production Cloudflare verification result through the established chatbot smoke/diagnostic bridge and record the D1/R2 evidence before claiming production deployment DoD.

## Deliberate boundaries

- Foundation planner performs no network I/O.
- Foundation/Operations planner bridge does not hold provider secrets or protected policy/billing authority.
- Planner learning cannot mutate protected security/billing/source-access rules.
- Mapper remains acquisition-free.
- Public workers remain untrusted until trusted evaluation accepts their outputs.

## Validation rule

Green public CI proves implementation behavior. Protected hosted CI, chatbot-backed live Cloudflare verification, provider/source-access, deployment, billing/quota and production claims require their own authoritative evidence gates.