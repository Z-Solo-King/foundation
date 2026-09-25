# Heroic AI Worker Identity Migration — 2026-09-25

## Canonical public Worker

The public production Worker name is `heroic`.

The account Workers.dev subdomain target is `ai`.

Canonical free public origin:

`https://heroic.ai.workers.dev/`

## Deployment

Production deployment remains owned by `.github/workflows/heroic-ai-production-release.yml` and `scripts/production_release.sh`.

The release path deploys the renamed public Worker, then deploys the private Operations Worker with its `FOUNDATION` service binding targeting `heroic`, followed by live acceptance checks.

## Custom domain

`heroic-ai.dev` is intentionally not part of this release path because its Cloudflare zone is currently pending/unresolvable. The Workers.dev endpoint does not require that zone.

## Migration safety

The historical `research-intelligence-engine-public` and `research-intelligence-engine-private` Worker names are legacy runtime identities. They are retained until the new deployment completes its live acceptance gate; deletion must never target the canonical `heroic` or `operations` Workers.
