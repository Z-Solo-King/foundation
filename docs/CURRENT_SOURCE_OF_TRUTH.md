## 2026-09-20 LIVE MIGRATION RECONCILIATION — CURRENT OVERRIDE

Refresh live GitHub refs before every mutation.

- Foundation main: 12cf25f6a5688522f945e48efed915a5d5902703.
- Operations main: 6a3e8577ca9d75b80f592da104e7f997850ed164.
- Foundation #835 (TypeScript frontend controls) is merged.
- Foundation #836 is the active documentation reconciliation PR.
- Operations #606, #607, #608, #609 and #610 are merged.
- Operations #610 fixes a real production-release packaging defect: generated foundation_core was excluded from setuptools package discovery.
- Operations #603 remains the canonical AI-model/tooling portability tracker.
- Current main is not production-certified until a canonical production release proves the current revisions.
- Python remains protected policy/governance/persistence/provenance/replay/rollback authority; Operations contains no GitHub Actions workflow authority.

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
