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
- Foundation main: d2231195982b1a3a82a310a5e5a9e8d54c65c01d
- Operations main: abf7007f4251f80280296c9855e4354502b98541
- Current Foundation production pin for Operations: abf7007f4251f80280296c9855e4354502b98541

### Latest canonical production receipt
Run: 35445892339 (#219)
Foundation commit: d2231195982b1a3a82a310a5e5a9e8d54c65c01d
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
- Main-push Actions control-plane probe run 35445595034: SUCCESS with job creation.
- Main-push secret probe run 35445595001: SUCCESS with job creation.
- Actual nightly-multi-agent-research-v2.yml push run 35445593168: failure with no jobs created.
- Canonical workflow-bridge run 35445592590: failure with no jobs created.
- Canonical nightly pin repair / cross-repository drift / B2 helper runs also remain separate auxiliary failures and are not production deployment authorities.
- Therefore #157 and #263 remain open for their specific supported workflow-dispatch/nightly execution evidence.

### Issue consolidation
- Operations #329–#333 consolidated into #334; #334 is completed after production runtime acceptance.
- Operations #349 consolidated into #352; #352 remains open for broader extractor/mapper replay evidence.
- Foundation #259 is completed after successful post-DoH production acceptance.

### Open queue
Foundation: #27, #58, #157, #263, #452.
Operations: #119, #120, #132, #145, #155, #197, #340, #352, #385.
Total open issues: 14.

### Evidence ladder
- L1: source/document inspection
- L2: repository tests/contracts
- L3: GitHub/control-plane execution
- L4: approved private/runtime/production execution

Never upgrade L1/L2 evidence into L3/L4 claims.

### Maintenance loop
parallel discovery -> classify disposition -> non-overlapping fix lane -> focused tests -> required CI -> merge -> canonical production/runtime probe -> exact issue receipt -> queue rescan.

## Historical continuity notes

The earlier post-DoH and pre-#219 synchronization snapshots below the live-state section are superseded by the current revisions and production receipt at the top of this document.

For maintenance decisions, always use:
- current Foundation main `d2231195982b1a3a82a310a5e5a9e8d54c65c01d`;
- current Operations main / production revision `abf7007f4251f80280296c9855e4354502b98541`;
- latest canonical production receipt `35445892339` (#219);
- the current 14-issue acceptance queue;
- fresh GitHub/Cloudflare runtime evidence.

Never revive an obsolete DoH blocker, stale Operations pin, or pre-#219 runtime receipt solely from historical continuity text.
