# Current Source of Truth — Foundation Family

## 2026-09-19 LIVE STATE

This is a compact synchronization record for future maintenance chats. Live GitHub state and current runtime receipts override older notes.

### Repository topology
- Public: `Z-Solo-King/foundation`
- Private: `Z-Solo-King/operations`
- Foundation owns public contracts/core, GitHub Actions, public Worker/API, backup/restore orchestration, and the sole canonical production release.
- Operations owns protected policy/resource governance, private execution, provider/runtime control, memory/feedback, promotion/recovery, and chatbot control.
- Operations must remain private and must not contain GitHub Actions workflows.
- Do not enable Cloudflare Workers Builds or Deploy Hooks as a competing deployment authority.

### Current revisions
- Foundation main: `95840f563b51f08c38996d673034ca49fc539f79`
- Operations main: `035bb38e54aa2b81a1e41b95ac01e7d352b75d83`
- Current Foundation production pin for Operations: `035bb38e54aa2b81a1e41b95ac01e7d352b75d83`

### Latest canonical production receipt
Run: `35430074029`

Passed:
- public Worker deployment/readiness;
- private Operations deployment/provenance;
- authenticated chat;
- idempotent chat replay;
- authenticated SSE lifecycle.

Failed:
- research source ingestion because both fixed DoH endpoints return a Python Worker `TypeError` from the fetch invocation.

The production blocker is therefore limited to the Python Workers DoH transport invocation. Do not reopen already-proven chat/replay/SSE/service-binding work without a fresh failing receipt.

### Active DoH candidates
- PR #684: native Worker Fetch options; no completed checks in the current snapshot.
- PR #687: JS/Python FFI Request construction; all required PR checks passed on head `dd4bea5dbaa09601e082f55f5b9de732f1121ca6`, but it is based on an older main.
- PR #691: RequestInit-free JS Request path; newest candidate, checks not yet complete in the current snapshot.

Use one canonical candidate only. Rebase/reconcile a validated solution onto current main rather than creating another competing PR.

### Nightly control-plane
Latest canonical nightly-related push on current main: `35430072561`.
No jobs were created. Keep #157 and #263 open until supported canonical workflow execution produces the expected jobs and L3 evidence. Do not weaken permissions to force job creation.

### Open queue
23 open issues remain: Foundation #27, #58, #157, #259, #263, #452; Operations #119, #120, #132, #145, #155, #164, #197, #329, #330, #331, #332, #333, #334, #340, #349, #352, #385.

The issue count is not a completion metric. Close an issue only when its own acceptance graph is satisfied.

### Evidence ladder
- L1: source/document inspection
- L2: repository tests/contracts
- L3: GitHub/control-plane execution
- L4: approved private/runtime/production execution

Never upgrade L1/L2 evidence into L3/L4 claims.

### Maintenance loop
`parallel discovery -> classify disposition -> non-overlapping fix lane -> focused tests -> required CI -> merge -> canonical production/runtime probe -> exact issue receipt -> queue rescan`.

