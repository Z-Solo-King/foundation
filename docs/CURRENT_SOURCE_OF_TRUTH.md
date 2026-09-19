# Current Source of Truth — Foundation Family

## 2026-09-19 LIVE STATE

This file is the compact continuity record for the next maintenance chat. Current GitHub state and fresh runtime receipts override every older dated section elsewhere in the repository.

### Repository topology

- Public repository: `Z-Solo-King/foundation`
- Private repository: `Z-Solo-King/operations`
- Foundation owns public contracts/core, public Worker/API, GitHub Actions, backup/restore orchestration, and the sole canonical production release.
- Operations owns protected policy/resource governance, private execution, provider/runtime control, memory/feedback, promotion/recovery, and chatbot control.
- Operations must remain private and must contain no `.github/workflows`.
- Do not enable Cloudflare Workers Builds or Deploy Hooks as a competing deployment authority.

### Exact current revisions

- Foundation `main`: `6a91fbd17143083882e9ac7ebfa52f0b06a344b2`
- Operations `main`: `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`
- Foundation canonical production Operations pin target: `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`
- Foundation nightly research pin remains: `307ed38fe4c7902220cb981556bf08702babbae0`

### Latest canonical production receipt

- Latest verified workflow run: `35456292033` (Heroic AI production release, #232)
- Foundation revision: `6a91fbd17143083882e9ac7ebfa52f0b06a344b2`
- Last verified Operations provenance in Cloudflare: `github:307ed38fe4c7902220cb981556bf08702babbae0`
- Next production certification target: `github:c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`
- Cross-repository audit receipt artifact: `cross-repository-audit-receipt`

Passed in the canonical production release:

- public Worker deployment/readiness;
- private Operations deployment and exact Cloudflare provenance;
- authenticated chat;
- chat idempotency/replay;
- authenticated SSE lifecycle;
- permitted-source research ingestion/readback using `https://example.com/`;
- D1/B2 lifecycle;
- memory store/query/delete and owner boundary;
- durable task-envelope replay guard;
- candidate learning round-trip;
- rating feedback/evaluation candidate path;
- durable chat terminalization CAS;
- durable resource reservation/consume;
- durable resource reconciliation;
- maintenance scheduler reconciliation;
- provider-stream contract.

The live chat response deliberately remained `PARTIAL` with deterministic fallback because no permitted live chat provider was configured. That is an explicit governed state, not a failed production release.

### Control-plane state

- Main-push Actions control-plane probe on current Foundation `main`: SUCCESS with job creation.
- Main-push secret probe on current Foundation `main`: SUCCESS with job creation.
- Current `nightly-multi-agent-research-v2.yml` push run `35456290060`: failure before job creation; this does not satisfy the real 24-program execution gate.
- Current auxiliary nightly pin-repair, B2 backup/restore and cross-repository drift helper runs are separate automation evidence and are not production deployment authorities.
- The supported workflow-dispatch bridge still lacks one empirical receipt proving exact target SHA + actual job creation.

### Current open acceptance queue

Foundation:
- #58 — this master tracker;
- #157 — real 24-program nightly execution evidence;
- #263 — real workflow-dispatch bridge receipt;
- #452 — deeper SSE cancellation/disconnect and provider-error-after-partial-output evidence.

Operations:
- #119 — memory persistence/restart plus live authorization/deletion evidence;
- #120 — durable feedback ingestion plus evaluation integration;
- #132 — durable replay guard across real restart/instance boundary;
- #145 — approved external scheduler activation;
- #155 — cross-repository audit receipt plus supported bridge-dispatch evidence;
- #197 — broader approved-runtime conversational execution acceptance;
- #340 — deeper provider streaming interruption/cancellation/error acceptance;
- #352 — broader extractor/mapper network replay matrix;
- #385 — broader terminalization/recovery runtime acceptance beyond the fixed attempt-identity defect.

#27 is completed and closed after the confirmed stale temporary/diagnostic/test branch cleanup. Do not reopen it merely for historical branch pruning.

There are 13 open issues total, of which 12 are non-meta acceptance gates.

### Evidence boundary

Use the ladder:

`contract -> implementation -> focused test -> CI -> control-plane -> runtime -> production`

Do not upgrade source inspection or repository tests into runtime/control-plane/production certification.

### Next-chat operating rule

Start from Foundation `6a91fbd17143083882e9ac7ebfa52f0b06a344b2` and Operations `307ed38fe4c7902220cb981556bf08702babbae0`. The production receipt `35456292033` is the current L4 baseline. Work only on a missing acceptance rung or a newly established repository-side defect; do not re-open the already-correct chat/SSE/service-binding/deployment path without new evidence.
