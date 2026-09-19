# AI Agent Handoff — Research Intelligence Engine

## 2026-09-19 LIVE STATE OVERRIDE — CURRENT SESSION HANDOFF

This section is authoritative over every older section below. It was synchronized from the live GitHub state after the previous maintenance chat ended.

### Exact repository state
- Foundation `main`: `95840f563b51f08c38996d673034ca49fc539f79`.
- Operations `main`: `035bb38e54aa2b81a1e41b95ac01e7d352b75d83`.
- Foundation's canonical production Operations pin: `035bb38e54aa2b81a1e41b95ac01e7d352b75d83`.
- Operations PR #515 is merged into `main`; it adds D1-backed production memory and D1-backed task replay nonce protection.
- Foundation PR #683 is merged. It added the RFC 8484 DoH GET/wire-format transport, but the merged path still fails in the live Python Worker with a runtime `TypeError` during the DoH fetch call.

### Latest canonical production evidence
Latest production run: **35430074029** on Foundation `95840f563b51f08c38996d673034ca49fc539f79`.

Observed:
- public Worker deploy/readiness: PASS;
- private Operations deploy/provenance: PASS;
- Operations provenance: `github:035bb38e54aa2b81a1e41b95ac01e7d352b75d83`;
- authenticated chat: PASS;
- idempotent chat replay: PASS;
- authenticated SSE lifecycle: PASS;
- research endpoint and run readback: HTTP 200;
- research source ingestion: FAIL only at DoH transport:
  `DNS resolution failed for example.com (https://cloudflare-dns.com/dns-query: TypeError; https://dns.google/dns-query: TypeError)`.

Therefore the current production blocker is **Python Workers DoH transport invocation**, not chat, replay, SSE, service binding, or Operations deployment.

### Current DoH PR state
Three Foundation follow-up PRs exist for the same blocker:
- #684 — native Worker Fetch options for DoH runtime; no completed check evidence recorded in the current snapshot.
- #687 — construct the DoH Request through Python Workers FFI; **all required PR checks passed** on head `dd4bea5dbaa09601e082f55f5b9de732f1121ca6`, but the PR targets an older Foundation base and must be reconciled with current `main` before merge.
- #691 — avoid Python Workers RequestInit conversion in DoH; newest candidate, but current snapshot has no completed check evidence.

Do not create a fourth competing DoH implementation. Start by comparing #687 and #691 against current `main`, then keep one canonical fix path.

### Nightly/control-plane evidence
Latest canonical nightly-related push on current `main`: **35430072561**.
- No jobs were created.
- This remains a GitHub Actions control-plane/job-graph acceptance problem.
- Do not weaken permissions or workflow semantics merely to manufacture jobs.
- Keep #157 and #263 open until a supported canonical run creates and executes the expected jobs and retains L3 evidence.

### Current issue queue
There are still **23 open issues** across the two active repositories:
- Foundation: #27, #58, #157, #259, #263, #452.
- Operations: #119, #120, #132, #145, #155, #164, #197, #329, #330, #331, #332, #333, #334, #340, #349, #352, #385.

The issue count is not a completion target. Most Operations issues are runtime/evidence gates.

### Cross-chat execution rule
The next agent must:
1. read this live-state override first;
2. verify current `main` SHAs before mutating anything;
3. treat production run **35430074029** as the current authoritative runtime receipt;
4. do not reopen solved chat/replay/SSE/service-binding work without a new failing receipt;
5. resolve the single DoH transport blocker through one canonical PR path;
6. separately diagnose nightly zero-job control-plane behavior;
7. then rerun the canonical production release and convert exact evidence into issue updates.

Never infer runtime closure from source code or unit tests alone.

---

## 2026-09-19 LIVE STATE OVERRIDE — READ FIRST

This section supersedes older observations in this file when they disagree with the live repositories or the latest execution evidence.

### Exact repository state
- Foundation `main`: `b1e0e6e74e0d3d9a3e280fa146a6c39503628274`.
- Operations `main`: `035bb38e54aa2b81a1e41b95ac01e7d352b75d83`.
- Canonical approved Operations production pin in Foundation: `035bb38e54aa2b81a1e41b95ac01e7d352b75d83`.
- The intermediate Operations SSE revision `282dea820a1a2c24bdf7b5e23298e932ffd94767` is an ancestor of `b43c...`; it is not the current production pin.
- Operations PR #510's SSE fix is included in current `b43c...`.

### Latest production proof
Canonical production run **35420683298** on Foundation commit `b1e0e6e...` reached Cloudflare deployment and passed:
- Operations provenance: `github:035bb38e54aa2b81a1e41b95ac01e7d352b75d83`;
- authenticated chat: PASS;
- idempotent chat replay: PASS;
- authenticated SSE lifecycle: PASS, including start/delta/done;
- research POST/readback endpoints: HTTP 200.

The run still failed because the bounded research smoke source `https://example.com/` returned:
`DNS resolution failed for example.com`.
Therefore production certification is **not complete**. Do not reopen the already-fixed SSE work as the primary blocker.

### Latest GitHub Actions/nightly proof
- Main-push control-plane probe run **35420683253**: PASS.
- Main-push secret probe run **35420683329**: PASS.
- Nightly multi-agent research run **35420680901** on the same main commit: failure with **zero jobs**.
- Canonical nightly pin-repair run **35420682251**: failure before useful job evidence.

Interpret zero-job nightly failures as a GitHub Actions control-plane/job-graph acceptance gate unless a future run produces executable job evidence. Do not change valid workflow permissions or semantics merely to manufacture jobs.

### Open issue queue
Foundation has **6 actual open issues**: #27, #58, #157, #259, #263, #452.
Operations has **17 actual open issues**: #119, #120, #132, #145, #155, #164, #197, #329, #330, #331, #332, #333, #334, #340, #349, #352, #385.
Issue count is not the goal; closure requires each issue's stated acceptance rung.

### Current open Foundation PRs
- **#675** canonical workflow bridge control-plane evidence: verifies post-dispatch run creation and job creation, explicitly surfacing accepted-trigger/zero-job states.
- **#674** research DNS transport fix: adds a bounded secondary DNS-over-HTTPS resolver while preserving fail-closed public-address validation.
- **#673** nightly artifact-integrity contract: validates the complete lane/diagnosis/project-summary/baseline bundle.
- **#671** remains diagnostic-only and should not be merged blindly.
- **#666**, **#650**, **#657**, **#661** are stale/superseded and should not be resumed.

### Required next strategy
1. Reconfirm current `main` SHAs.
2. Fix the **research DNS/transport failure** first using the smallest reproducible source adapter probe; verify the exact Cloudflare Python Workers fetch contract.
3. Separately verify the nightly zero-job control-plane condition; do not mix it with research/runtime code changes.
4. Run the canonical production workflow again.
5. Only after production research succeeds, use the exact run receipt to advance #259.
6. For nightly, retain #157/#263 until a real canonical nightly run creates and executes its expected lane/final-gate jobs.
7. Treat chat/SSE/idempotency as already passing on current main unless a new run regresses them.

Never infer L3/L4 runtime success from repository source alone, and never resurrect superseded SSE/service-binding work without new evidence.


Updated: 2026-09-18

This file is the canonical handoff for a new GitHub-maintenance chat/agent. Treat the live repositories and the latest production evidence as authoritative; do not revive older chat conclusions when newer commits supersede them.

## Repository topology

- Public repository: `Z-Solo-King/foundation`
- Private repository: `Z-Solo-King/operations`
- Foundation owns public contracts/core, public Worker/API, GitHub Actions, backup/restore orchestration, and the sole production release authority.
- Operations owns protected policy, resource governance, provider/runtime selection, private execution, promotion/rollback/recovery, and chatbot control.
- Operations must remain private.
- Foundation -> Operations runtime path is Cloudflare Worker service binding + `AUTH_TOKEN`.
- Foundation -> private-source/deployment path is the approved GitHub App installation credential resolved dynamically at runtime.
- Do not re-enable Cloudflare Workers Builds or Deploy Hooks as a competing deployment authority.
- Do not add GitHub Actions to the private Operations repository.

## Current canonical revisions

- Foundation production-code baseline at handoff: `972e1b05c1e2d51905029b602d0c4120eac1d399`
- Operations production-code baseline at handoff: `035bb38e54aa2b81a1e41b95ac01e7d352b75d83`
- Canonical approved Operations production revision: `035bb38e54aa2b81a1e41b95ac01e7d352b75d83`
- Operations PR #505 / commit `3afbde92...` corrected the Cloudflare Python service-binding request construction to use `workers.Request(url, **kwargs)` and added regression coverage. The previous deployed-runtime `Request.new` failure is therefore a superseded blocker, not a reason to redesign the boundary.
- Foundation PR #642 advanced the production pin and synchronized the nightly research/pin-repair contracts to the corrected Operations revision.

## Production release chain

Canonical owner:
`.github/workflows/heroic-ai-production-release.yml` -> `scripts/production_release.sh`

The release is intentionally ordered and fail-closed:

1. required Foundation checks;
2. dynamic GitHub App installation resolution;
3. exact private Operations repository/SHA verification;
4. public Worker deploy + public health/readiness/UI smoke;
5. exact Operations D1 schema application;
6. exact pinned Operations checkout/core materialization;
7. private Operations Worker deploy with `AUTH_TOKEN`;
8. Cloudflare active-version provenance verification;
9. real authenticated production chat;
10. chat idempotent replay;
11. real SSE lifecycle;
12. real research execution + readback;
13. broader authenticated infrastructure diagnostic/B2 check.

A merged PR is not production certification. A successful deploy step is not runtime acceptance. Keep runtime issues open until the required evidence exists.

## Authentication and secrets

- Never print or commit the plaintext `AUTH_TOKEN`.
- Canonical application authentication secret: Foundation Actions `AUTH_TOKEN`.
- The same secret is intended for public Worker, private Operations Worker, and authenticated production probes.
- Repo-safe AUTH_TOKEN record is stored in Operations as `docs/AUTH_TOKEN_REPOSITORY_SAFE_RECORD.docx`; it contains only non-secret audit metadata/fingerprint.
- `OPERATIONS_APP_ID` and `OPERATIONS_APP_PRIVATE_KEY` are for GitHub App access only and must never be substituted with storage/provider credentials.
- Cloudflare credentials and B2 credentials remain separate authorities.

## Resource governance baseline

Canonical protected resource kinds:
`d1_reads`, `d1_writes`, `queue_operations`, `workflow_steps`, `browser_minutes`, `workers_ai_neurons`, `model_calls`, `github_minutes`, `search_calls`, `storage_bytes`.

Starter limits:
```json
{
  "d1_reads": 100000,
  "d1_writes": 20000,
  "queue_operations": 10000,
  "workflow_steps": 5000,
  "browser_minutes": 60,
  "workers_ai_neurons": 100000,
  "model_calls": 2000,
  "github_minutes": 500,
  "search_calls": 1000,
  "storage_bytes": 5000000000
}
```

Promotion/canary/shadow/rollback reservation baseline: `workflow_steps: 10` each.

The canonical D1 is `research-intelligence`; Operations uses `OPERATIONS_DB` for durable governance. Do not create a second resource ledger or second D1 authority.

## Current open queue

GitHub currently has 23 open issues across the two active repositories.

Foundation (6):
- #27 stale branch/reference hygiene
- #58 coverage/meta tracker
- #157 24-program nightly research live execution
- #259 production release acceptance
- #263 GitHub Actions control-plane/job-graph evidence
- #452 public SSE lifecycle/runtime acceptance

Operations (17):
- #119 memory safety/runtime
- #120 feedback loop/runtime
- #132 authenticated task-envelope/replay runtime
- #145 periodic maintenance scheduler
- #155 cross-repository audit bridge
- #164 durable resource governance runtime
- #197 conversational execution runtime
- #329 adaptive execution budgets/runtime breadth
- #330 fast/deep routing + research-stop integration
- #331 provider health/circuit breaker
- #332 cache/coalescing live path
- #333 admission/backpressure/fairness
- #334 capacity forecasting/fallback
- #340 provider streaming interruption/idempotency
- #349 extractor/mapper failure visibility
- #352 network-enabled extractor/mapper replay
- #385 terminalization/recovery

## Queue interpretation

The issue count must not be used as a progress target.

Most of the remaining Operations issues already have substantial repository implementations and are acceptance gates. Their remaining rung is normally real private-runtime/control-plane/production evidence, not another speculative implementation.

For every issue use:
`contract -> canonical owner -> implementation -> focused test -> CI -> Foundation integration -> control-plane -> runtime -> production`.

Primary dispositions:
`FIX_NOW`, `INTEGRATE`, `VERIFY_REPO`, `RUNTIME_GATE`, `EXTERNAL_BLOCKED`, `DUPLICATE`, `SUPERSEDED`, `ROADMAP`.

Do not close runtime-gated issues because a PR merged or unit tests passed.

## Immediate next action for a new chat

1. Read this file plus `docs/DEPLOYMENT.md`, `REPOSITORY_MAP.json`, and `docs/FAMILY_ARCHITECTURE.md`.
2. Verify the current Foundation/Operations `main` SHAs before changing anything.
3. Inspect the latest canonical production-release run after the `972e1b0...` pin update.
4. If the run fails, classify the earliest proven failure (workflow admission -> job creation -> execution -> binding/configuration -> live endpoint) and fix only that layer.
5. If the run succeeds, convert its exact evidence into issue receipts and close only issues whose own acceptance graph is fully satisfied.
6. Then process the remaining 23-issue queue using non-overlapping lanes and rescan after every 3–5 meaningful mutations.

Never infer Cloudflare/runtime success from GitHub source alone. Never expose private Operations implementation or secrets through Foundation documentation.


## 2026-09-19 LIVE STATE OVERRIDE — CURRENT CHAT HANDOFF

This section supersedes older handoff revisions when they conflict with the live repositories.

### Exact current revisions
- Foundation `main`: `4dd63df25f34d8489d9abb8f75611a511d2a3c2a`.
- Operations `main`: `8258d0bcee2bef9427a60aed522a14e0ff95ea2b`.
- Operations remains private; Foundation remains the sole GitHub Actions and canonical production-deployment owner.

### Research transport progression
- Foundation PR #697 merged: raw JavaScript `fetch(url)` DoH path.
- Foundation PR #699 merged: documented `Request.new` path; live production still showed an FFI `AttributeError`.
- Foundation PR #700 merged after all required PR checks and CodeQL passed. It explicitly converts the fixed DoH URL through Pyodide `to_js` before the JavaScript fetch boundary.
- Foundation PRs #684, #687 and #691 were closed as superseded after the newer validated path was merged.
- Do not reopen or stack another transport variant without a fresh production receipt identifying a new failure mode.

### Private-runtime acceptance progression
- Operations PR #517 merged at `8258d0bcee2bef9427a60aed522a14e0ff95ea2b`.
- Foundation PR #698 merged the corresponding protected-runtime diagnostic/pin update.
- The production diagnostic is now capable of exercising D1 memory store/query/owner-bound delete, D1 replay rejection, candidate-learning persistence, durable resource reservation/reconciliation, and maintenance reconciliation.
- These capabilities remain runtime acceptance gates until the canonical production release records the exact PASS evidence.

### Current production gate
Canonical production run **35434275607** is the latest deployment run for Foundation `main` `4dd63df...` and was still in progress at the last refresh. Do not infer research/runtime success from the merge or from CI.

### Nightly/control-plane state
The latest push-triggered nightly-related workflows on `4dd63df...` created **zero jobs** (including the canonical nightly research, pin-repair, bridge, backup/restore and cross-repository drift runs). The dedicated main-push control-plane and secret probes still passed. Treat zero-job workflow runs as an independent GitHub control-plane/job-graph acceptance gate; do not change valid permissions merely to manufacture jobs.

### Open issue queue
The live queue remains 23 issues: Foundation #27/#58/#157/#259/#263/#452 and Operations #119/#120/#132/#145/#155/#164/#197/#329/#330/#331/#332/#333/#334/#340/#349/#352/#385.

### New-chat continuation protocol
1. Inspect the final result and logs of production run **35434275607**.
2. If research still fails, use the exact production exception and the current Foundation #700 implementation as the starting point; do not repeat already-tested fetch shapes blindly.
3. If production passes, write the exact receipt to #259 and only close issues whose own acceptance graphs are fully satisfied.
4. Independently handle the zero-job nightly/control-plane gate for #157/#263.
5. Do not close runtime-gated Operations issues from source/CI alone.

Updated: 2026-09-19
