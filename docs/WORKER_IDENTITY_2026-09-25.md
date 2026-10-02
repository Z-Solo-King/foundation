# Heroic AI public endpoint and Worker identity

## Public front door

Cloudflare Pages project: `heroic-ai`.

Cloudflare-assigned public Pages hostname:

`https://heroic-ai.pages.dev/`

## Backend Worker

The production public Worker identity is `heroic`.

`heroic` is now the native JavaScript edge gateway. It forwards the public request through the `CORE` Service Binding to the private `heroic-core` Python Worker.

The Python core owns the existing application logic, D1, artifact storage bindings and the private Operations Service Binding.

## Deployment ownership

Production Worker deployment remains owned by `.github/workflows/heroic-ai-production-release.yml` and `scripts/production_release.sh`.

The release path deploys Operations, Operations edge, `heroic-core`, and finally the public `heroic` JavaScript edge before running the existing live acceptance checks.

The Pages front door remains a public routing layer only.

## Migration safety

The public `heroic` Worker contains no Python compatibility requirement, application D1 binding, or provider-secret binding. Those capabilities remain behind `heroic-core`.

Rollback must restore a previously accepted version of the canonical Worker pair through the canonical production release/rollback process; do not delete `heroic` or `heroic-core` during migration.

## Reconciliation — 2026-10-02

The canonical public hostname is now `https://heroic-ai.pages.dev/`. The Pages project is GitHub-backed from `Z-Solo-King/foundation` and routes `/health`, `/readiness`, and `/api/*` through `HEROIC_BACKEND` to the production `heroic` Worker.
