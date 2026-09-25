# Heroic AI public endpoint and Worker identity — 2026-09-25

## Public front door

Cloudflare Pages project: `ai`.

Cloudflare-assigned public Pages hostname:

`https://ai-cio.pages.dev/`

The requested `https://ai.pages.dev/` hostname was not assignable to this account; Cloudflare assigned the project the globally available `ai-cio.pages.dev` hostname.

## Backend Worker

The production public Worker identity is `heroic`.

The account Workers.dev subdomain is `heroic-ai`, so the backend Worker origin is:

`https://heroic.heroic-ai.workers.dev/`

The Pages front door uses the `HEROIC_BACKEND` Service Binding to the `heroic` Worker.

## Deployment ownership

Production Worker deployment remains owned by `.github/workflows/heroic-ai-production-release.yml` and `scripts/production_release.sh`.

The release path deploys the public `heroic` Worker, then the private `operations` Worker with its `FOUNDATION` service binding targeting `heroic`, followed by live acceptance checks.

The Pages project is a public routing layer only; it is not a competing Worker deployment authority.

## Custom domain

`heroic-ai.dev` is intentionally not part of this release path because its Cloudflare zone is currently pending/unresolvable.

## Migration safety

The historical `research-intelligence-engine-public` and `research-intelligence-engine-private` Worker names are legacy runtime identities. They are retained until the new `heroic` deployment and live acceptance gate complete; deletion must never target the canonical `heroic` or `operations` Workers.
