# Deployment

This repository contains the public contract/Worker boundary. Production control-plane implementation details remain in the private `operations` repository.

## Current verified production state

As of 2026-09-13, the Cloudflare production deployment had been manually verified end to end at that time:

- private control-plane Worker deployed;
- public Worker deployed;
- public Worker URL: `https://research-intelligence-engine-public.soloking-research-intelligence.workers.dev`;
- `/health` returned HTTP 200;
- `/readiness` returned HTTP 200 under the then-verified deployment configuration;
- Backblaze B2 is the artifact-storage provider under the strict zero-cost target.

This document does not treat older manual verification as fresh production proof. The current acceptance rule requires current authenticated verification evidence from the approved runtime path.

The public Worker is deployed with Python Worker tooling (`pywrangler`), not plain `wrangler deploy`.

## GitHub Actions status

The canonical public production deployment workflow is `.github/workflows/codeql.yml`.

It is intentionally named `codeql.yml` for historical compatibility, but it is also the repository's required CI workflow and contains the **only** `pywrangler deploy` production deployment job. The deployment job runs only after `Public tests` succeed and only on pushes to `main`.

The same deployment job performs the post-deployment smoke checks. There is no separate `deploy-public-worker.yml` or `production-chatbot-deploy-smoke.yml` workflow in the current repository.

The deployment job dynamically resolves the live D1 database ID from Cloudflare and generates a runner-only production Wrangler configuration; it removes the generated configuration after deployment. Credentials are never committed.

The smoke stage always verifies the public Worker `/health` and `/readiness` surfaces. The authenticated infrastructure diagnostic is only claimed when `AUTH_TOKEN` is available and the diagnostic confirms the public chatbot surface, Cloudflare D1 and Backblaze B2 lifecycle checks.

## Runtime architecture

The current public-safe architecture does not make public readiness depend on the private control plane. Protected Operations may use a private Service Binding to call Foundation where the protected verification path requires it.

Foundation uses:

- Cloudflare D1 for compact public/operational metadata where defined by the Foundation contract;
- Backblaze B2 for current artifact storage under the strict zero-cost design;
- no public route for arbitrary private control-plane dispatch.

B2 credentials, authentication tokens, private service names, and private control-plane identifiers do not belong in Git. A Cloudflare D1 resource ID is a non-secret infrastructure identifier and may be committed to the public Worker configuration when required for the public Worker binding.

## Required deployment inputs

Supply these through the deployment environment or secret store rather than committing them:

- `CLOUDFLARE_API_TOKEN`;
- `CLOUDFLARE_ACCOUNT_ID`;
- `AUTH_TOKEN` where the authenticated verification path requires it;
- `B2_KEY_ID`;
- `B2_APPLICATION_KEY`;
- any protected Service Binding required by the private control-plane path.

Production credentials must never be committed.

The generated production config uses the current zero-cost B2 target:

- bucket: `SoloKing`;
- endpoint: `https://s3.eu-central-003.backblazeb2.com`.

## Deployment order

The Foundation production workflow owns the public Worker deployment. Private Operations activation and runtime verification remain separate concerns and must not create a second GitHub deployment owner.

Smoke-test `/health` first. Treat `/readiness` according to the currently committed public readiness contract rather than assuming private-control-plane availability.

## Important operational lessons

- Never hard-code an obsolete D1 `database_id`; resolve it from Cloudflare at deployment time.
- Never deploy a generated Wrangler config containing `REPLACE_WITH_*` placeholders.
- For Python Workers use `pywrangler deploy`.
- Keep credentials and authentication secrets out of Git and handoff documents.
- Keep the strict `$0` policy fail-closed; do not add paid fallbacks to make deployment convenient.
- Do not call Cloudflare production verification complete until current authenticated evidence exists.
- Keep deployment and post-deployment verification in the same canonical workflow chain.
