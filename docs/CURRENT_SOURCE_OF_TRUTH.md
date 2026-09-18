# Current Source of Truth

**Status:** CURRENT. **Evidence boundary:** L2 repository evidence unless explicitly marked L3/L4.
**Owner:** Foundation family synchronization boundary.
**Updated:** 2026-09-18.

## Current revisions

- Foundation `main`: `5f2ac608ab05ff922d0fa4f4ed95d7b7b3266109`.
- Operations `main`: `b20e02483d25724ee26a560b7feedc900d8ea154`.
- Approved Operations production revision: `3afbde926880b91e3e660ee2d35daa5334e542bf`.
- The approved production revision is distinct from current Operations `main`.

These are audit observations. Live branch tips remain authoritative when they advance.

## Family ownership

Foundation owns:
- public-safe contracts and schemas;
- deterministic evidence/intelligence primitives;
- public Worker/API and frontend;
- GitHub Actions;
- repository backup/restore orchestration;
- the canonical production release workflow.

Operations owns:
- protected policy and resource authority;
- private acquisition/execution;
- provider/runtime governance;
- private memory/feedback;
- evaluation, promotion and recovery;
- chatbot orchestration.

Operations remains private. Foundation must not reproduce protected Operations implementation.

The retired `Z-Solo-King/extractor-mapper` repository is historical. The active extractor/mapping implementation is the `operations/extractor_mapper/` directory.

## Canonical deployment authority

The only production owner is:

`.github/workflows/heroic-ai-production-release.yml`
-> `scripts/production_release.sh`
-> explicitly approved Operations revision
-> Cloudflare runtime.

Cloudflare Workers Builds and Deploy Hooks are not alternative authorities.

Operations must not gain GitHub-hosted private CI/deployment workflows.

## Current GitHub issue gates

There are 23 open issues across the two active repositories. The count is not a completion target.

Foundation:
- #27 administrative branch/reference cleanup;
- #58 cross-family coverage/meta tracker;
- #157 live 24-program nightly research evidence;
- #259 production release acceptance;
- #263 GitHub Actions control-plane/job-graph evidence;
- #452 public SSE lifecycle/runtime acceptance.

Operations:
- #119 memory safety/runtime;
- #120 feedback loop/runtime;
- #132 task-envelope/replay runtime;
- #145 maintenance scheduler;
- #155 cross-repository audit bridge;
- #164 durable resource governance runtime;
- #197 conversational execution runtime;
- #329 execution budget/runtime breadth;
- #330 routing/research-stop integration;
- #331 provider health/circuit breaker;
- #332 cache/coalescing live path;
- #333 admission/backpressure/fairness;
- #334 capacity forecasting/fallback;
- #340 streaming interruption/idempotency;
- #349 extractor/mapper failure visibility;
- #352 network-enabled extractor/mapper replay;
- #385 terminalization/recovery.

Most Operations issues already have repository implementation and focused tests. Their remaining acceptance is primarily runtime/control-plane evidence. Do not create speculative code solely to reduce the queue.

## Current implementation summary

Repository-side capabilities already present include:
- deterministic chatbot intent/routing/strategy selection;
- bounded provider selection/retry/streaming;
- durable resource accounting;
- idempotency and terminalization contracts;
- cache/coalescing eligibility;
- admission/backpressure/fairness;
- provider capacity forecasting;
- research stop/continue decisions;
- evaluation receipts and protected promotion lifecycle;
- bounded public research ingestion/evidence publication contracts.

The complete production-shaped research chain is not claimed merely because these primitives exist.

## Runtime evidence boundary

- L0: hypothesis;
- L1: source inspected;
- L2: repository inspection including callers/tests/ownership;
- L3: current GitHub Actions execution;
- L4: approved runtime/production execution.

A merged PR is not a deployment. A deployment workflow result is not automatically production certification. Source inspection and repository tests cannot prove external runtime state.

Protected runtime values and private platform details are intentionally omitted from this public repository.

## Documentation lifecycle

Living documents:
- this file;
- `docs/AI_AGENT_HANDOFF.md`;
- `docs/DOCUMENTATION_INDEX.md`;
- `docs/FAMILY_SYNC_STANDARD.md`;
- `docs/FAMILY_SYNC_STATE.json`;
- topic-specific standards and contracts.

Historical/dated material is retained only where it preserves unique provenance, a decision, benchmark evidence or a useful historical record. Redundant handoffs, stale status snapshots and duplicate current-state documents should be removed after their useful facts are incorporated here.

## Next-maintenance rule

Start with this file, `docs/AI_AGENT_HANDOFF.md`, `REPOSITORY_MAP.json`, the live issue/PR state and the current family sync snapshot. Verify the current branch tips before changing anything.
