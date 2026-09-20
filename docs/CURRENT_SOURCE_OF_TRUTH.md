## 2026-09-20 LIVE MIGRATION RECONCILIATION — CURRENT OVERRIDE

Refresh live GitHub refs before every mutation.

### Current repository heads
- Foundation `main`: `e14b6d07ad32eb6eeb7899ec3b5bfe5140169b63`.
- Operations `main`: `88bc073b5d14c10d83fe7bbff6f78bdbf672cc14`.

### Active migration work
- Foundation #835 is the active TypeScript frontend-controls migration PR; it is blocked only by the required `Public tests` check, currently being repaired.
- Foundation #836 is this documentation reconciliation PR.
- Operations #606 and #607 are merged.
- Operations #608 (rolling four-lane execution scheduler) is merged.
- Operations #603 remains the canonical AI-model/tooling portability tracker.
- No other open implementation PRs are currently known.

### Production/evidence boundary
- The latest documented successful canonical production receipt remains Foundation run `35456292033` (#232).
- Current `main` is not being treated as production-certified until a canonical release proves the current revisions.
- Runtime/control-plane acceptance issues remain evidence-gated; do not manufacture receipts from source inspection or unit tests.

### Architecture invariant
Python remains protected policy/governance/persistence/replay/provenance/rollback authority. TypeScript/Rust/Go migration work remains evidence-gated. Operations remains free of GitHub Actions; Foundation remains the sole CI/CD/deployment owner.

## 2026-09-20 LIVE MIGRATION RECONCILIATION — CURRENT OVERRIDE

Refresh live GitHub refs before every mutation. Last synchronized refs:
- Foundation main: `e14b6d07ad32eb6eeb7899ec3b5bfe5140169b63`
- Operations main: `57211e4058c55e478b763f6d82a30d3f3a4aa789`

Current migration state:
- Foundation #827, #828, #829 and #834 are merged.
- Foundation #835 is the active current-main TypeScript frontend-controls migration PR.
- Stale Foundation candidates #831 and #832 were closed and superseded by #835.
- Operations #599, #600, #602, #604 and #605 are merged.
- Operations #606 is the active TypeScript browser-acquisition hardening lane.
- Operations #607 is the active Go 32-case × 3-repeat benchmark-only lane.
- Operations #603 remains the canonical AI-model/tooling portability tracker.

Production evidence:
- The last successful canonical production receipt remains Foundation run `35456292033` (#232).
- A newer push-triggered canonical production release run `35511331331` (#299) was attempted against Foundation `e14b6d0…` and failed. The available connector receipt confirms job execution and failure but does not expose the failing step output; do not infer a root cause.
- Therefore current `main` is not production-certified.

Migration authority remains unchanged:
Python owns protected policy/governance/persistence/replay/provenance/rollback authority. TypeScript and Rust candidates remain evidence-gated; Go remains benchmark-only.

## 2026-09-20 LIVE RECONCILIATION — AUTHORITATIVE

GitHub refs and fresh runtime evidence override every older continuity section below.

### Exact repository state
- Foundation `main`: `386dcad577cacf729ee49830548597ff5504de14` (includes merged PR #821).
- Operations `main`: `f87b565be102df93baca760261657a8c949479da`.
- Open Foundation PRs: none.
- Open Operations PRs: none.
- Open issues: Foundation #58, #157, #263, #452; Operations #119, #132, #145, #155, #197, #340, #352, #385.
- #821 is merged and supplies the browser-side chat-stream cancellation contract under Foundation #452.
- The canonical workflow bridge is `.github/workflows/foundation-canonical-workflow-bridge-v3.yml`; legacy bridge v1/v2 definitions have been removed; v3 is the sole routing authority.
- Operations remains free of `.github/workflows`; Cloudflare Workers Builds and Deploy Hooks remain prohibited competing deployment authorities.

### Acceptance boundary
Repository-side migration and deterministic validation work is complete for the current lane. Remaining open issues are acceptance gates requiring live control-plane/runtime evidence, not speculative rewrites:
- #157: real 24-program nightly execution/artifact evidence.
- #263 / Operations #155: one real v3 bridge dispatch receipt proving exact SHA and downstream job creation.
- #452: live browser cancellation/disconnect propagation through the public Worker; current provider execution is non-streaming, so provider-error-after-partial-output is not a currently reachable provider path.
- Operations #119/#132: real restart/instance-boundary persistence/replay evidence.
- Operations #145: approved external scheduler tick receipt.
- Operations #197: broader approved-runtime conversational execution evidence.
- Operations #340: deeper interrupted-stream/usage-reconciliation/runtime evidence.
- Operations #352: representative live extractor/mapper replay evidence across API/feed/HTML/browser and failure/retry/restart cases.
- Operations #385: broader cross-surface crash/recovery/late-output runtime evidence.

### Production evidence boundary
The last documented successful canonical production release remains run `35456292033` (#232), which predates the current Foundation/Operations heads. Do not treat current `main` as production-certified until a new canonical release proves the current revisions.

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

- Foundation `main`: `386dcad577cacf729ee49830548597ff5504de14`
- Operations `main`: `f87b565be102df93baca760261657a8c949479da`
- Foundation canonical production Operations pin target: `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`
- Foundation nightly research pin remains: `f6600c068de6e17af1e0e99c1f3ba4b0f06f31b5`

### Latest canonical production receipt

- Latest verified workflow run: `35456292033` (Heroic AI production release, #232)
- Foundation revision: `6a91fbd17143083882e9ac7ebfa52f0b06a344b2`
- Last verified Operations provenance in Cloudflare: `github:f6600c068de6e17af1e0e99c1f3ba4b0f06f31b5`
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
- Foundation PR #812 is merged and the v3 bridge now dispatches the allowlisted target, verifies the exact SHA, polls the target run and requires job creation.
- Foundation PRs #815 and #816 advanced the TypeScript edge shadow into Phase B route/SSE/JSON/public-HTTP contract coverage.
- Foundation PRs #817 and #818 merged Foundation-owned CI lanes for the TypeScript browser shadow and Rust text-normalization pilot. The remaining acceptance is one real execution receipt proving those conditions in the live Actions control plane.

### Current open acceptance queue

Foundation:
- #58 — this master tracker;
- #157 — real 24-program nightly execution evidence;
- #263 — real workflow-dispatch bridge receipt;
- #452 — deeper SSE cancellation/disconnect and provider-error-after-partial-output evidence.

Repository-side migration work merged today:
- Foundation #810/#811 — canonical hybrid-language pilot CI and TypeScript shadow-adapter CI.
- Foundation #812 — dispatch-capable canonical bridge v3 with exact SHA/job-creation receipt contract.
- Operations #576 — hardened TypeScript shadow search-adapter contract.
- Operations #577 — parity-gated Rust URL identity pilot.
- Operations #579 — durable failed terminalization/replay for unexpected chat execution exceptions.
- Operations #581 — provider-stream ERROR/CANCELLED classification codes are now mandatory.
- Operations #583 — TypeScript search-adapter default timeout is enforced.
- Operations #584 — deterministic extractor/mapper replay matrix is merged.
- Operations #585 — unresolved external provider intent now fails closed instead of replaying an unknown side effect.
- Operations #586 — TypeScript browser acquisition shadow is merged.
- Operations #587 — Rust text-normalization parity kernel is merged.

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

There are 12 open issues total, of which 11 are non-meta acceptance gates.

### Evidence boundary

Use the ladder:

`contract -> implementation -> focused test -> CI -> control-plane -> runtime -> production`

Do not upgrade source inspection or repository tests into runtime/control-plane/production certification.

### Next-chat operating rule

Start from Foundation `d3f32e09bd39ca167ae556cb3514709b8ed4644f` and Operations `4128d25c2d116993d6a0868cb129e591b5b815c2`. The production receipt `35456292033` is the current L4 baseline. Work only on a missing acceptance rung or a newly established repository-side defect; do not re-open the already-correct chat/SSE/service-binding/deployment path without new evidence.
