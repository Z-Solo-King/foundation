# Heroic AI Migration / Audit Continuation Handoff — 2026-10-01

## 0. Purpose

This is the durable continuation point for the Heroic AI GitHub + Cloudflare migration/audit work when the current chat reaches its limit.

Repositories:
- Public Foundation: `Z-Solo-King/foundation`
- Private Operations: `Z-Solo-King/operations`

This is a non-feed migration/audit lane.

**Feed work is explicitly excluded.** Do not modify, merge, close, or use these as mutation vehicles unless the user explicitly changes scope:
- Foundation #1247
- Foundation #1249
- Foundation feed PRs #1652, #1653, #1656, #1657, #1658, #1660
- Operations #1361
- Operations #1400 (mixed extractor/feed)

## 1. Fresh live synchronization — 2026-10-01

### GitHub main heads

Foundation main:
`9538b83e95314141ec262b7f691bbbe7ee4fd521`

Operations main:
`3c780e33772c87ec6c3b6df75a857e5404f0b861`

Important state change from the previous handoff:
- The previously certified Operations production pin `ca3864a954569f6f8ce9a94793c53a0ef9ff03ec` has now been explicitly advanced.
- Current `docs/OPERATIONS_PIN_MANIFEST.json` production_runtime pin is:
  da86e92d4e0fdb68912efb54ef95c69281a7d613
- Operations `main` is currently ahead of the production pin; the immutable production pin remains the only production authority and must be explicitly promoted and then runtime-verified.

The Foundation head `55f06767...` is the promotion commit that advanced the public-safe Operations pin to the syntax-corrected persistence diagnostic runtime.

The Operations head `90fa37df...` corrects the persistence diagnostic logger syntax in `private/control_plane_diagnostics.py`.

### Current pin manifest

`docs/OPERATIONS_PIN_MANIFEST.json` current SHA:
`ec8b1fa5f3cac2e4aa4cf25059fb4ee0967e4aa7`

Current purpose-scoped immutable pins:
- production_runtime: da86e92d4e0fdb68912efb54ef95c69281a7d613
- provider_fleet_runtime: `b95e419254a9071beaeef57a1b0da22ba7dd2c4f`
- research_runtime: `1a91efa53b9202f1624ddde892b0e86bd6b360f0`
- secret_sync_utility: `b95e419254a9071beaeef57a1b0da22ba7dd2c4f`

Manifest rules remain:
- 40 lowercase hex SHA
- mutable refs forbidden
- branch/tag refs forbidden
- purpose scoped

## 2. Cloudflare production — freshly reconciled

Account:
`66cd52347a2a64648eb0f4cca8ac88b7`

Latest live deployments observed immediately before this handoff:

### heroic
- role: public TypeScript edge
- live GitHub annotation: Foundation `55f06767...`
- latest deployment id: `be41d757-0eee-4370-9616-4780815eca63`
- version: `8c9059ba-142b-4be3-8d4d-5846c8f3dec3`
- traffic: 100%
- binding: `CORE -> heroic-core`
- secret: `AUTH_TOKEN`
- schedules: none

### heroic-core
- role: Foundation Python semantic/application core
- live GitHub annotation: Foundation `55f06767...`
- latest deployment id: `af2e650f-c12a-4cd2-ad02-15309b13733f`
- version: `e24a69b7-d8d8-4bad-905f-29ebc0db53e2`
- traffic: 100%
- D1: `19f51638-47a5-4218-a9dc-73dbfd6156fe`
- service binding: `OPERATIONS -> operations-edge`
- B2 bindings present: key id, application key, bucket, endpoint
- `ENVIRONMENT=production`
- `RELEASE_FOUNDATION_SHA=55f06767...`
- `RELEASE_OPERATIONS_REF=90fa37df...`
- `STRICT_ZERO_COST_ONLY=true`
- schedules: none

### operations
- role: private Python control plane
- latest live GitHub annotation: Operations `90fa37df...`
- latest deployment id: `cf5be286-de7c-460d-b417-1fe62487274e`
- version: `f6014487-a31b-4da2-b7af-1d300916385f`
- traffic: 100%
- service binding: `FOUNDATION -> heroic`
- native Workers AI binding: `AI`
- cost guards observed:
  - `MAX_DAILY_COST_USD=0`
  - auto-recharge false
  - auto-upgrade false
  - overage false
  - paid-fallback false
  - unknown-pricing false
- configured provider fleet string includes:
  `cloudflare_workers_ai,openrouter_free,groq,gemini,cerebras,nvidia_nim,cohere_free,huggingface_free,siliconflow`
- default Workers AI model:
  `@cf/zai-org/glm-4.7-flash`
- research max output tokens: 512
- chat max output tokens: 256
- moderation mode: block
- schedule: `*/15 * * * *`

### operations-edge
- role: private TypeScript/JS delegation boundary
- latest live GitHub annotation: Operations `90fa37df...`
- latest deployment id: `35a129c9-8de9-4dbb-9fbf-2ea9256d6a4c`
- version: `ca625f24-7324-416a-ab0c-30c81b103dfc`
- traffic: 100%
- binding: `CORE -> operations`
- schedules: none

## 3. Canonical ownership

Foundation owns:
- public-safe contracts
- public HTTP/SSE edge
- deterministic mapper/core/data-quality primitives
- public evidence publication/admission
- canonical hosted GitHub Actions release/deployment authority

Operations owns:
- private chatbot semantics and routing
- provider/task fabric
- resource/quota/lease governance
- policy/evidence/provenance/idempotency/replay
- private acquisition/extraction runtime
- research orchestration
- private mapper/extractor authority

B2:
- artifact/backup storage only
- never identity, authorization, routing, policy or resource authority

AI_PROJECT_MAP:
- navigation metadata only
- never evidence authority
- never deployment authority
- never policy authority

## 4. Migration language rule

Current intended language roles:
- TypeScript: edge/application/browser/search/tooling contracts
- Python: semantic logic, AI/research orchestration, provider governance, policy, evidence, provenance, replay, idempotency, resource governance and reference implementations
- Rust: only measured CPU/memory-sensitive deterministic kernels
- Go: only measured high-concurrency/network utilities
- other languages: qualification candidates only

Promotion rule:
`language score -> candidate selection`
`benchmarks/static scans/compilation -> supporting evidence`

Authority promotion additionally requires:
- exact functional parity
- deterministic differential tests
- normalized error parity
- security parity
- policy parity
- provenance/lineage parity
- cancellation/timeout parity
- resource/performance measurements
- serialization/conversion measurements
- shadow
- canary
- rollback
- safe retirement of the canonical reference

Never transfer authority merely because an AI model, benchmark, language score, compilation result or static scan says a candidate is better.

## 5. Latest production / nightly evidence

### Production release
Latest exact release associated with the live research gate:
- Foundation: `55f06767...`
- release run: `36818502155`
- nightly production gate accepted this exact release.

### Same-head chatbot smoke
Foundation run:
`36818845457`
- status: completed
- conclusion: success
- purpose: Live chatbot production smoke

### Same-head live nightly research
Foundation run:
`36818843764`
- workflow: Nightly research — production-live
- head: `55f06767...`
- event: `workflow_dispatch`
- production gate: success
- migration review: success
- research CrossFire job: failure
- final truthful-result gate: failure
- diagnosis job: success
- no genuine research closure

Critical failure found in live job `110229827662`:
- exact deployed runtime probe passed
- Foundation/Operations exact revisions matched:
  - Foundation `55f06767...`
  - Operations `90fa37df...`
- provider: `cloudflare_workers_ai`
- generation_status: `model_generated`
- structured output: true
- then research proxy startup failed on the runner because:
  `ModuleNotFoundError: No module named 'httpx'`
- proxy health therefore failed:
  `curl: (7) Failed to connect to 127.0.0.1 port 8765`
- CrossFire never obtained valid live execution
- lane/artifact materialization correctly failed closed
- artifacts were uploaded, but this run is not #157 closure evidence

This is now the primary concrete blocker to investigate next:
**Foundation nightly research workflow must install/provide the Operations research proxy dependency `httpx` before starting `scripts/research_worker_proxy.py`.**
Do not merely rerun the failed workflow; first inspect the dependency ownership/installation contract, then make the smallest correct PR if needed.

The failure is runner dependency/setup, not a Cloudflare model-generation failure.

## 6. Nightly trigger architecture

The earlier accidental 01:00 IST schedule problem was fixed before this handoff.

Current intended model:
- canonical nightly research workflow is dispatch-driven
- successful canonical production release dispatches provider preflight, then live nightly
- manual/API dispatch remains available
- the separate `nightly-invariants` scheduled workflow is regression checking, not the research engine
- the post-nightly canary is downstream `workflow_run` consumption, not a research starter

Do not reintroduce a direct cron schedule to `nightly-multi-agent-research-v3.yml`.

The current research runtime remains purpose-pinned independently at:
`1a91efa53b9202f1624ddde892b0e86bd6b360f0`

CrossFire scheduler contract currently uses:
`RESEARCH_MAX_CONCURRENCY=6`

Do not confuse this with older historical artifacts that still mention a 20-agent aggregate contract.

## 7. Remaining acceptance issues

### Foundation #157 — genuine 24-program research
Open.

Required fresh evidence:
1. exact Foundation production deployment
2. exact Operations production revision
3. Worker-backed model preflight
4. actual provider-backed live execution
5. 24 distinct programs
6. 3 valid lane artifacts
7. diagnosis success
8. truthful final result gate success
9. complete artifact bundle + provenance/attestation

24 IDs by themselves are insufficient.
Historical 6+2 lane failures are not closure evidence.
Current run `36818843764` is also not closure evidence because of the `httpx` runner dependency failure.

### Operations #597 — mapper migration
Open.

Current status:
- repository-side decomposition/governance exists
- candidate evidence exists for selected TS/Rust lanes
- no authority promotion

Next valid work:
- choose a concrete candidate
- generate fresh candidate-specific runtime receipt
- 32 orthogonal cases x >=3 repeats where required
- cold start/raw samples as applicable
- differential functional/error/security/policy/provenance/cancellation/timeout parity
- performance/resource/conversion measurements
- shadow
- canary
- rollback

### Operations #603 — AI/model/tooling portability
Open.

Current status:
- portability architecture/evidence framework exists
- no language/model/tooling promotion by score/benchmark
- candidate-specific evidence remains required

Next valid work:
- select one concrete candidate
- 32-case parity corpus x >=3 repeats where required
- functional/security/policy/provenance/cancellation evidence
- serialization/conversion/resource measurements
- canonical authority comparison
- shadow
- canary
- rollback

### Foundation #58
Open meta/tracker issue.
It derives completion from #157/#597/#603 plus broader coverage. Do not close it from repository scans alone.

## 8. Open PR state — current scope

Current open PR inventory after refresh is empty; feed-trigger PR #1791 merged and remaining feed evidence is tracked separately.

Foundation:
- #1663 — feed recovery handoff docs — feed-only
- #1660 — feed guessing v8 — feed-only
- #1658 — feed guessing v7 — feed-only
- #1657 — Common Crawl feed recovery — feed-only
- #1656 — historical feed URL recovery — feed-only
- #1653 — SVMPForge feed guessing — feed-only
- #1652 — targeted live Google XML hunt — feed-only

Operations:
- #1361 — WooCommerce feed recovery docs — feed-only
- #1400 — extractor evolution/coverage connection — mixed extractor/feed; keep excluded

Therefore there is currently no open non-feed PR that should be merged as the next migration change.

## 9. Browser Run

Live Cloudflare Browser Run `/content` has already been verified.

Repository candidate adapter uses the Cloudflare `BrowserWorker` binding contract.

Guardrails:
- HTTPS/read-only acquisition policy
- explicit host allowlist
- bounded timeout/page/response limits
- candidate-only

Do not promote/add a production BROWSER binding until full:
- resource
- security
- policy
- provenance
- differential
- shadow
- canary
- rollback
evidence exists.

## 10. Providers

Strict zero-cost policy is mandatory.

Current:
- SiliconFlow: governed/integrated
- Cerebras: intentionally unactivated for free path because card requirement is not satisfied
- Mistral: conditional/excluded
- Cloudflare Workers AI: live native provider
- OpenAI-compatible transports are not assumed semantically equivalent

For provider portability, validate provider-specific:
- structured output
- streaming
- context limits
- tool behavior
- errors/retries
- normalization
- cost-policy behavior

No provider score becomes authority by itself.

## 11. Audit method for the next chat

Use independent lenses and cover BOTH repositories:
1. ownership/policy
2. TypeScript edge/application
3. Rust deterministic kernels
4. Go concurrency/network
5. Cloudflare/runtime/deployment
6. security/evidence/provenance

Map-first retrieval:
`AI_PROJECT_MAP -> REPOSITORY_MAP -> canonical feature/function -> policy/tests/workflows -> live runtime receipt`

For each mutation:
1. inspect current main
2. identify canonical owner
3. identify policy gates
4. inspect tests/workflows
5. inspect live runtime when relevant
6. smallest correct change
7. focused validation
8. required CI
9. merge only with verified green evidence
10. update migration/evidence/map state
11. re-check Cloudflare for deployment changes

Shared writes remain serialized and authority-owned.

## 12. Immediate next-chat execution order

### Phase A — fix the known live blocker
1. Re-read this handoff.
2. Refresh Foundation/Operations main heads and the current pin manifest.
3. Verify Cloudflare four-worker state.
4. Inspect `nightly-multi-agent-research-v3.yml`, `scripts/research_worker_proxy.py`, and dependency installation files.
5. Determine the canonical dependency owner for `httpx`.
6. Add `httpx` to the correct workflow/setup contract if missing; do not duplicate incompatible dependency management.
7. Run focused workflow-contract/unit validation.
8. Open PR on Foundation.
9. Wait for all required checks.
10. Merge only green.
11. Let canonical production release redeploy.
12. Re-run the real production-dispatched nightly research.
13. Verify all gates and artifacts before changing #157 status.

### Phase B — complete #157
Do not use dry-run evidence.
Do not count the current failed run.
Do not close until the entire 24-program live artifact/provenance contract passes.

### Phase C — mapper candidate #597
After #157 blocker is resolved, create a concrete candidate-specific evidence experiment for one migration lane.
Preserve Python canonical authority.
Generate the full parity/performance/shadow/canary/rollback receipt before promotion.

### Phase D — AI/model/tooling #603
Select one concrete candidate and repeat the same evidence ladder.
Do not infer portability from OpenAI-compatible API shape alone.

### Phase E — broad non-feed audit
Only after the runtime acceptance blockers are controlled, continue the six-lens audit across:
- mapper
- extractor architecture
- chatbot
- search/provider APIs
- Workers AI
- Browser Run
- B2
- policy/rules
- public/private structure
- maps/evidence
- deployment workflows

## 13. Failure handling rules

When a live run fails:
- identify exact stage
- capture exact error/HTTP status
- separate runner/setup failure from provider failure from application failure
- preserve the failed receipt
- do not convert execution failure into a negative research finding
- do not rerun blindly
- fix the owning layer
- repeat focused validation
- then repeat live acceptance

Historical receipts remain provenance only.

## 14. Do not accidentally regress

Do not:
- reintroduce nightly cron into the canonical research workflow
- deploy Operations manually
- create a second GitHub Actions deployment authority
- promote moving Operations main without explicit evidence
- expose private Operations implementation in Foundation
- put secrets in maps/receipts
- use B2 as authority
- use AI_PROJECT_MAP as authority
- use a benchmark as production proof
- bypass Cloudflare/GitHub access controls
- touch feed work in this lane

## 15. Success condition for this continuation

The work is complete only when every non-feed open issue is either:
- fixed and live-verified,
- explicitly evidence-gated with a concrete next experiment,
- or intentionally retained with documented rationale.

Target architecture:
- one authority per responsibility
- deterministic behavior
- strict $0 operation
- low resource/token overhead
- strong security/policy boundaries
- complete provenance
- measurable migration decisions
- shadow/canary/rollback safety
- fast recovery from runtime failures



## AI navigation

Use `docs/AI_SYSTEM_DIRECTORY.md` and `docs/AI_SYSTEM_MAP.json` before broad retrieval. They route intent to overlapping categories, owner, canonical path, contract, tests, workflow, evidence and runtime while keeping navigation non-authoritative.
