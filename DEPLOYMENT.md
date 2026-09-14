# Deployment

This repository contains the public contract/Worker boundary. Production control-plane implementation details remain in the private `operations` repository.

## Current architecture (standalone public Worker)

The public Worker is intentionally standalone:

- `/health` returns public runtime health.
- `/readiness` verifies public runtime plus public D1 health and does **not** depend on a private control-plane Service Binding.
- The public chatbot diagnostic (`/api/v1/chatbot/diagnostic`) exposes only the bounded `infrastructure_verify_public_test` operation and requires a valid `AUTH_TOKEN` bearer token in production.
- No public route may dispatch arbitrary private control-plane operations.
- Private Operations may still call Foundation through its own protected Service Binding when an authorized private verification path requires it — but the public Worker does not require or depend on any binding to Operations.

This replaces an earlier design where the public Worker held a Service Binding to a private control-plane Worker. That dependency has been removed; do not reintroduce it without an explicit architecture decision recorded in `docs/FAMILY_ARCHITECTURE.md`.

## GitHub Actions status

The public deployment workflow is `.github/workflows/deploy-public-worker.yml` (not `deploy.yml`). It runs on `push` to `main` and on `workflow_dispatch`.

The workflow:
1. Waits for `test.yml` (`public-tests`) to pass for the current commit.
2. Verifies the configured `CLOUDFLARE_API_TOKEN` and resolves `CLOUDFLARE_ACCOUNT_ID` (from a repository secret or variable).
3. Dynamically discovers the live D1 database ID from Cloudflare instead of relying on a stale hard-coded UUID.
4. Applies D1 migrations remotely.
5. Deploys the Worker with `wrangler deploy`.

A separate workflow, `production-chatbot-deploy-smoke.yml`, runs a post-deployment smoke check against the authenticated chatbot diagnostic endpoint. These two workflows are not yet consolidated into a single canonical path; treat both as currently active until that consolidation happens.

## Runtime architecture

The public Worker uses:

- Cloudflare D1 for canonical graph/run metadata.
- Backblaze B2 S3-compatible object storage for artifacts.

No B2 credentials, authentication tokens, or private database identifiers belong in Git.

## Required deployment inputs

Supply these through the deployment environment or secret store rather than committing them:

- `CLOUDFLARE_API_TOKEN` — must have Workers Scripts:Edit, D1:Edit, and Account Settings:Read permissions scoped to the account (Account Settings:Read is required for account ID resolution).
- `CLOUDFLARE_ACCOUNT_ID` — repository secret or variable.
- `AUTH_TOKEN` — required for the public diagnostic/chatbot/research endpoints in production.
- `B2_KEY_ID`
- `B2_APPLICATION_KEY`

The committed `wrangler.toml` intentionally keeps the D1 database name/ID as `REPLACE_WITH_*` placeholders; the deployment workflow generates a real `wrangler.production.generated.toml` at deploy time with the discovered database ID.

The non-secret B2 configuration is fixed to the zero-cost deployment target:

- bucket: `SoloKing`
- endpoint: `https://s3.eu-central-003.backblazeb2.com`

## Important operational lessons

- Never hard-code an obsolete D1 `database_id`; the workflow resolves the current ID live.
- Never deploy a generated Wrangler config containing `REPLACE_WITH_*` placeholders — only the generated production config (with real values) should ever be deployed.
- Keep secrets out of Git and handoff documents.
- Keep the strict `$0` policy fail-closed; do not add paid fallbacks to make deployment convenient.
- A GitHub Actions secret with an empty value is functionally equivalent to a missing secret; verify values are actually populated, not just that the secret name exists.
