# Current Source of Truth

**Status:** LIVE RECONCILIATION  
**Audit date:** 2026-09-26  
**Evidence cutoff:** 2026-09-26T16:43Z  
Fresh GitHub, Cloudflare, workflow, artifact, and D1 evidence override older dated checkpoints.

## Family heads and production pins

| Surface | Revision |
|---|---|
| Foundation main | `ee312632fce5be5da9536194e94f38fa2cdabb6b` |
| Operations main | `122a334d85708e2e42db59b74114d1396ca98f31` |
| Public runtime Foundation provenance | `ee312632fce5be5da9536194e94f38fa2cdabb6b` |
| Production/nightly Operations pin | `566fe7b90c15a8e0ad8210bd98a7b514de6f5fc3` |
| Operations main vs production pin | 26 commits ahead, 0 behind |

## Canonical topology
Foundation owns the public-safe contracts, deterministic research/evidence core, public frontend boundary, and deployment authority. Operations owns the private chatbot control plane, policy/resource authority, private memory, provider runtime, and promotion logic.

`Pages project ai (ai-cio.pages.dev) -> public Worker heroic -> private Worker operations`

Cloudflare currently shows `heroic` version 30 at 100% with current Foundation provenance, and `operations` version 90 at 100% with the immutable production pin. The legacy `foundation` Worker remains but is not the canonical public backend.

## Cloudflare inventory
- Pages: `ai`, `heroic`, `heroic-ai`
- Workers: `foundation`, `heroic`, `operations`, `logtech-endpoint-lab`, `opencart-feed-probe-20260926`, `shopify-feed-probe-20260926`
- D1: `research-intelligence` / `19f51638-47a5-4218-a9dc-73dbfd6156fe`
- KV: 0
- Queues: 0
- Durable Objects: 0
- R2 bucket listing unavailable: Cloudflare error 10042 asks for R2 enablement.
- `heroic-ai.dev`: pending, activation failure `unresolvable`.
- Cloudflare user-token verification unavailable through the current credential (errors 1000/9109), while account-scoped product reads work.

## Current GitHub queue
### Foundation — 7 open issues
#1281 ChatGPT documentation parity  
#1265 full-content public-repo secret scan  
#1249 Custom/API Merchant-feed recovery  
#1247 WooCommerce Merchant-feed recovery  
#1157 project-native AI/agent benchmark  
#157 nightly 24-program research acceptance  
#58 exhaustive coverage tracker

### Foundation — 8 open PRs
#1282 ChatGPT doc/prompt-map parity; current issue-matrix audit checks fail  
#1280 full-tree/git-history secret scan; current checks pass  
#1279 secret-scan variant; six-lane audit fails on issue/surface-map divergence  
#1278 Foundation/Operations synchronization; deep-scan lanes fail  
#1276 DOMAIN_PACKS extraction; public coverage gate 98% vs 100%  
#1275 text/identifier normalization; public coverage gate 98% vs 100%  
#1253 public GitHub Action boundary; deep-scan/open-issue matrix fails  
#1248 Custom/API XML feed matrix; observed checks pass

### Operations — 12 open issues
#1005 active-hours-aware maintenance/self-update scheduling  
#998 enforce session-continuity updates to current-state/family-sync  
#997 exhaustive-audit documentation, Cloudflare/B2 lane, consolidation, aggregate score  
#994 detailed capability map linking code/GitHub/Cloudflare  
#713 Rust URL/IPv6 policy parity defect  
#603 AI-model/tooling portability  
#597 mapper decomposition/evidence lanes  
#699 umbrella audit/roadmap  
#145 periodic maintenance tick  
#197 Heroic AI conversational live acceptance  
#340 governed streaming/token-accounting integrity  
#385 single terminalization/side-effect semantics

### Operations — 4 open PRs
#985 Shopify feed discovery  
#984 WooCommerce feed-discovery hardening  
#983 WooCommerce merchant-feed validation hardening  
#981 public catalog transport extraction hardening

## CI defects currently visible
- Open-issue/surface-map matrix drift is breaking deep-scan/six-lane audit jobs; the clearest traceback compares the persisted issue count with `OPEN_ISSUE_SCAN_RULES`.
- #1276 and #1275 fail at 98% coverage against a 100% gate; uncovered modules are `domain_packs.py` and `text_normalization.py`.
- #1280 has four current checks passing.
- #1248 has a successful observed check suite.
- Operations PR detail logs returned 404 from the available job-log surface, so no finer root cause is asserted for #985/#984/#983/#981 here.

## Nightly research
Latest observed run `36141145555` (#375):
- aggregate state `blocked_before_execution`
- research job `cancelled`
- 3 lanes × 8 slots = 24 prepared programs
- no provider-backed execution
- diagnosis artifact `10868805522`
- migration-review score 60/100
- 40 matrix cases + 24 capacity cases
- blockers: `lane_validation_incomplete`, `research_job_not_successful`, `research_preflight_blocked`
- 24-program live acceptance is not certified

## Extractor benchmark
Run `36141127492` (#448), artifact `10867020802`, digest `sha256:073ad2ba3df5bad3f9536abe95281ec596e109d7293b4bc4d30499e11cb21e62`.
40 receipts: API 12 / browser 8 / feed 8 / HTML 12; 4 ok / 32 empty / 4 blocked. Completion rate 0.10; error rate 0; provenance, route provenance, repeat reliability 1.0; unstable repeated groups 0; structural quality pass.
This is a structural/integrity benchmark, not proof of 40 successful real business-data acquisitions. The four ok receipts are synthetic listing placeholders without populated business fields.

## D1 live state
707 `research_runs` (484 completed, 223 planned); 440 observations; 0 research publications; 581 resource-governance reservations; 135 quota rows; 1,436 chat-idempotency rows; 1 `document_versions` row; 0 `source_lineage` rows; no artifact-specific table. Direct `sqlite_master` schema/query access succeeds even though stale control-plane metadata previously reported zero tables.

## ChatGPT / continuity
Both Custom GitHub and Custom Cloudflare connectors worked in the same project chat on 2026-09-26. This is empirical session evidence, not a guarantee for every future interface.

OpenAI documentation currently states that Projects keep related chats, files, and instructions together; connected apps can be used in project chats when available; project memory can use same-project context depending on memory mode; and starting a new chat is a supported troubleshooting step for long/unresponsive conversations:
https://help.openai.com/en/articles/10169521-projects-in-chatgpt
https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt
https://help.openai.com/en/articles/8590148-memory-in-chatgpt
https://help.openai.com/en/articles/7996703-troubleshooting-chatgpt-error-messages

## Source-of-truth rules
1. Live GitHub/Cloudflare/workflow/artifact evidence outranks dated notes.
2. Production pins remain separate from branch heads.
3. Runtime/L4 acceptance is separate from deterministic CI.
4. 403/429/blocked remains transport-unverified, not “no data”.
5. Correct this file or the compact family-sync JSON; do not add another competing current snapshot.
