# Current Source of Truth — Foundation Family

## 2026-09-19 LIVE STATE

This is the compact synchronization record for future maintenance chats. Live GitHub state and current runtime receipts override older notes.

### Repository topology
- Public: Z-Solo-King/foundation
- Private: Z-Solo-King/operations
- Foundation owns public contracts/core, GitHub Actions, public Worker/API, backup/restore orchestration, and the sole canonical production release.
- Operations owns protected policy/resource governance, private execution, provider/runtime control, memory/feedback, promotion/recovery, and chatbot control.
- Operations must remain private and must not contain GitHub Actions workflows.
- Do not enable Cloudflare Workers Builds or Deploy Hooks as a competing deployment authority.

### Current revisions
- Foundation main: 450fb977957db716e60655778e6263bb15064073
- Operations main: abf7007f4251f80280296c9855e4354502b98541
- Current Foundation production pin for Operations: abf7007f4251f80280296c9855e4354502b98541

### Latest canonical production receipt
Run: 35444893823 (#217)
Foundation commit: 450fb977957db716e60655778e6263bb15064073
Operations revision: abf7007f4251f80280296c9855e4354502b98541

Passed:
- public deployment/readiness;
- authenticated chat;
- chat idempotency/replay;
- authenticated SSE lifecycle;
- permitted source ingestion from https://example.com/ (HTTP 200);
- persisted research readback;
- D1 and B2 lifecycle checks;
- private runtime diagnostic.

Private runtime checks passed:
- execution amplification budget;
- admission/backpressure;
- fairness;
- circuit breaker;
- cache/coalescing;
- provider capacity;
- routing/stop;
- provider-stream contract;
- memory store/query/delete and ownership boundary;
- replay protection;
- candidate learning round-trip;
- durable resource reservation/reconciliation;
- maintenance scheduler reconciliation.

### Current control-plane evidence
- Main-push Actions control-plane probe: run 35444893881, SUCCESS with job creation.
- Main-push secret probe: run 35444893733, SUCCESS with job creation.
- The actual nightly-multi-agent-research.yml push run 35444890399 still failed before job creation.
- The canonical-workflow-bridge run 35444891050 also failed before job creation.
- Therefore #157 and #263 remain open for their specific workflow-dispatch/nightly execution evidence. Do not generalize the earlier zero-job defect to all main pushes.

### Open queue
Foundation: #27, #58, #157, #263, #452.
Operations: #119, #120, #132, #145, #155, #197, #340, #352, #385.
Operations #329–#333 were consolidated into #334, and #334 is now completed. Operations #349 was consolidated into #352.

Total open issues: 14.

### Evidence ladder
- L1: source/document inspection
- L2: repository tests/contracts
- L3: GitHub/control-plane execution
- L4: approved private/runtime/production execution

Never upgrade L1/L2 evidence into L3/L4 claims.

### Maintenance loop
parallel discovery -> classify disposition -> non-overlapping fix lane -> focused tests -> required CI -> merge -> canonical production/runtime probe -> exact issue receipt -> queue rescan.

## 2026-09-19 POST-DOH MAINLINE SYNC

Current Foundation main includes commit 61353f4351778a57e5abf602c961d26bc4d208c9, which fixes canonical workflow bridge run matching by passing the actual workflow head SHA into the control-plane probe, and commit aa966f4365b66351f28ea88946b1408344184c07, which fixes the Python Workers DoH transport by constructing a standard JavaScript Request and mutating its real Headers before JavaScript fetch.

Current approved Operations production pin remains 035bb38e54aa2b81a1e41b95ac01e7d352b75d83.

The latest authoritative production receipt before the DoH merge still proves deployment/provenance, authenticated chat, idempotent replay and SSE while research source ingestion failed at the older DoH invocation. A fresh canonical production run is required before #259 can close.


## 2026-09-19 CURRENT RECONCILIATION

Foundation main now includes the workflow-bridge dispatch timestamp race fix (PR #708, merged as `33331e37c66fb77b60098e8adb3c80ef63942bc6`).

The canonical production and nightly paths are being advanced from obsolete Operations revision `8258d0bcee2bef9427a60aed522a14e0ff95ea2b` to the current immutable Operations main `abf7007f4251f80280296c9855e4354502b98541` in PR #709.

No fresh post-change production receipt exists yet. Do not claim Cloudflare L4 certification or close runtime-gated issues until the canonical production workflow produces current evidence.
