# Runtime Bootstrap Handoff — 2026-09-18

## Purpose

This document is the current cross-chat handoff for the Foundation/Operations production recovery. It records verified repository and Cloudflare facts without inventing protected secret or policy values.

## Canonical GitHub state

- Foundation `main`: `972e1b05c1e2d51905029b602d0c4120eac1d399`
- Operations `main`: `3afbde926880b91e3e660ee2d35daa5334e542bf`
- Canonical Foundation production owner: `scripts/production_release.sh`
- Canonical production Operations revision currently pinned by Foundation: `3afbde926880b91e3e660ee2d35daa5334e542bf`
- Operations repository remains private.

## Cloudflare state reported/observed on 2026-09-18

Worker: `legacy private Worker`

- active version: `15`
- traffic: 100%
- version ID: `5ee4364d-b26a-4a6e-b2e8-22e9129e1fdc`
- deployment ID: `61b1a4fe-be10-441a-9307-8301b5e3e94`
- deployment source: API / automatic deployment on configuration upload

Configured runtime topology reported by the Cloudflare recovery check:

- `OPERATIONS_DB` -> D1 `research-intelligence`
- `FOUNDATION` -> `legacy public Worker`
- `ENVIRONMENT=production`
- `STRICT_ZERO_COST_ONLY=true`
- cron `*/15 * * * *`
- `RESOURCE_GOVERNANCE_SCOPE` configured
- `RESOURCE_GOVERNANCE_WINDOW` configured
- `RESOURCE_RESERVATION_LEASE_SECONDS` configured

The configuration change itself created version 15. This is a Cloudflare platform/configuration deployment, not proof that the approved Operations application revision is running.

## Still missing / intentionally not guessed

The following protected runtime values are not established:

- `RESOURCE_LIMITS_JSON`
- `RESOURCE_RESERVATIONS_JSON`
- private `AUTH_TOKEN`

The resource JSON values have no authoritative recoverable values in source or Cloudflare and must not be inferred from tests, examples, legacy versions, or Cloudflare platform quotas.

The existing public `AUTH_TOKEN` value is not readable from Cloudflare. Any synchronization requires one controlled rotation of the canonical application token and installation of that same value on both public and private Workers.

## Production interpretation

Version 15 is **not production-certified** because the underlying application code is reported as stale relative to the canonical approved Operations revision.

Do not close runtime issues from this configuration evidence alone.

Required sequence:

1. establish/approve the two canonical resource-policy JSON values;
2. rotate and synchronize the single canonical application `AUTH_TOKEN`;
3. deploy the exact Operations revision pinned by Foundation's canonical production release;
4. verify private Worker runtime, D1, service binding and cron;
5. collect L3/L4 evidence for resource governance, chat/SSE, replay/idempotency, memory/feedback and recovery;
6. close each issue only against its stated acceptance criteria.

## Non-negotiable boundaries

- No second Worker.
- No second D1.
- No GitHub-hosted private runtime.
- No Cloudflare Workers Builds.
- No Deploy Hooks.
- No personal/PAT credential authority.
- No second ResourceLedger.
- No guessed protected policy values.
