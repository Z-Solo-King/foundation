# Live GitHub ↔ Cloudflare Sync — 2026-09-25 R4

## Current public endpoint

- Requested public hostname: `https://ai.pages.dev/`
- Cloudflare project name created: `ai`
- Cloudflare-assigned hostname: `https://ai-cio.pages.dev/`
- Reason: Cloudflare assigned the project the globally available `ai-cio.pages.dev` hostname; the exact `ai.pages.dev` hostname is not assigned to this account.
- Current Pages production deployment: `[REDACTED-DEPLOYMENT-ID]`
- Pages deployment status: `success`
- Pages Service Binding: `HEROIC_BACKEND -> heroic (production)`

## Worker identity

- Intended public Worker: `heroic`
- Account Workers.dev subdomain: `heroic-ai`
- Intended backend origin: `[REDACTED-BACKEND-WORKER-ORIGIN]`
- The `heroic` Worker currently exists in Cloudflare.
- Current Cloudflare bootstrap implementation is a compatibility proxy to the existing `foundation` production Worker so the Pages binding has a valid target.
- Final application implementation is delivered by Foundation PR #1210 and must replace this bootstrap before production certification.

## GitHub

- Foundation PR: #1210
- Foundation branch: `worker-identity-heroic-ai-2026-09-25`
- Operations migration PR #965 is merged at `[REDACTED-OPERATIONS-SHA]`.
- Operations `wrangler.toml` points `FOUNDATION` to service `heroic`.
- Foundation release acceptance and live probes use the verified Pages hostname.

## Production safety

- `[REDACTED-CUSTOM-DOMAIN]` remains pending/unresolvable and is not required for this release path.
- Legacy Workers `[REDACTED-LEGACY-PUBLIC-WORKER]` and `[REDACTED-LEGACY-PRIVATE-WORKER]` remain retained until the renamed pair passes full live acceptance.
- Cloudflare Worker listing currently contains `foundation`, `heroic`, `operations`, and the two legacy Worker identities.
- D1 `[REDACTED-PRIVATE-D1]` remains the canonical persistence database.

## Acceptance status

The current state is **not yet production-certified**. The remaining certification gate is a fresh GitHub merge/release run proving the final `heroic` implementation, Pages front door, private Operations binding, real model generation, replay/convergence, SSE, research readback, persistence rollover, resource governance, and provenance together.

Repository/CI evidence is not substituted for Cloudflare L4/runtime evidence.
