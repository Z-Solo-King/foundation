# AI Agent Handoff — Research Intelligence Engine

**Updated:** 2026-09-18

This is the canonical handoff for a new GitHub-maintenance chat/agent. It is a navigation document, not a replacement for live GitHub state.

## Start here

1. `docs/CURRENT_SOURCE_OF_TRUTH.md`
2. `docs/CLAUDE_GUIDANCE.md` in Operations for family-wide AI maintenance rules
3. `REPOSITORY_MAP.json`
4. `docs/FAMILY_ARCHITECTURE.md`
5. live GitHub issues/PRs/workflows

## Current revisions

- Foundation `main`: `5f2ac608ab05ff922d0fa4f4ed95d7b7b3266109`
- Operations `main`: `b20e02483d25724ee26a560b7feedc900d8ea154`
- Approved Operations production revision: `3afbde926880b91e3e660ee2d35daa5334e542bf`

Verify these against live branch tips before acting.

## Architecture

Foundation owns the public-safe contract/core, frontend/API boundary, GitHub Actions, backup/restore workflow and canonical production release.

Operations owns protected policy/resource authority, private execution, provider/runtime governance, evaluation, promotion/recovery and chatbot control. Operations remains private and must not gain a competing GitHub Actions/deployment path.

The canonical production path is:

`.github/workflows/heroic-ai-production-release.yml`
-> `scripts/production_release.sh`
-> approved Operations revision
-> Cloudflare runtime.

Do not re-enable Cloudflare Workers Builds or Deploy Hooks.

## Open acceptance queue

There are 23 open issues across the two active repositories. The queue is not a progress score.

Use the acceptance ladder:

`contract -> owner -> implementation -> focused test -> CI -> integration -> control-plane -> runtime -> production`

Close an issue only when its required rung is proven or the issue is explicitly superseded/duplicated/deferred according to its acceptance criteria.

## GitHub-only maintenance boundary

This chat/repository path handles GitHub source, documentation, PRs, issues and CI contracts.

Do not claim Cloudflare, B2, provider or production state without the appropriate external/runtime evidence.

Do not expose private Operations topology, credentials or protected implementation through Foundation documentation.

## Handoff rule

After a material change, update the canonical current-source document and affected issue/PR records. Do not create a new dated handoff for every chat continuation; use the living handoff plus current source of truth instead.
