# AI Agent Handoff — Research Intelligence Engine

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

- Foundation `main`: `972e1b05c1e2d51905029b602d0c4120eac1d399`
- Operations `main): `3afbde926880b91e3e660ee2d35daa5334e542bf`
- Canonical approved Operations production revision: `3afbde926880b91e3e660ee2d35daa5334e542bf`
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
2. Verify current Foundation/Operations `main) SHAs before changing anything.
3. Inspect the latest canonical production-release run after the `972e1b0...` pin update.
4. If the run fails, classify the earliest proven failure (workflow admission -> job creation -> execution -> binding/configuration -> live endpoint) and fix only that layer.
5. If the run succeeds, convert its exact evidence into issue receipts and close only issues whose own acceptance graph is fully satisfied.
6. Then process the remaining 23-issue queue using non-overlapping lanes and rescan after every 3–5 meaningful mutations.

Never infer Cloudflare/runtime success from GitHub source alone. Never expose private Operations implementation or secrets through Foundation documentation.
