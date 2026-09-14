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

This document does not treat older manual verification as fresh production proof. The current acceptance rule requires the authenticated chatbot/control-plane verification path to produce current D1/B2 evidence.

The public Worker is deployed with Python Worker tooling (`pywrangler`), not plain `wrangler deploy`.

## GitHub Actions status

The canonical public deployment workflow is `.github/workflows/deploy-public-worker.yml`.

The post-deployment smoke/verification workflow is `.github/workflows/production-chatbot-deploy-smoke.yml`. It is intentionally separate from deployment but is triggered by successful completion of `deploy-public-worker` through `workflow_run`; it is not an independent push-triggered production verifier.

The deployment workflow dynamically resolves the live D1 database ID from Cloudflare instead of relying on a stale hard-coded UUID. When the public Wrangler file still contains its bootstrap placeholder, the workflow persists the current non-secret D1 resource identifier into `wrangler.toml`; this keeps Cloudflare Workers Builds usable from the public repository without exposing credentials. It also generates the authoritative production config for the current deployment.

The smoke workflow first verifies the public Worker health surface. Authenticated D1/B2 verification is only claimed when the required `AUTH_TOKEN` is available in that workflow context and the chatbot diagnostic returns successful checks for the public chatbot surface, Cloudflare D1 and Backblaze B2 lifecycle.

## Runtime architecture

The current public-safe architecture does not make public readiness depend on the private control plane. Protected Operations may use a private Service Binding to call Foundation where the protected verification path requires it.

Foundation uses:

- Cloudflare D1 for compact public/operational metadata where defined by the Foundation contract;
- Backblaze B2 for current artifact storage under the strict zero-cost design;
- no public route for arbitrary private control-plane dispatch.

B2 credentials, authentication tokens, private service names, and private control-plane identifiers do not belong in Git. A Cloudflare D1 resource ID is a non-secret infrastructure identifier and may be committed to the public Worker configuration when required for the public Worker binding.

## Required deployment inputs

Supply these through the deployment environment or secret store rather than committing them:

- `AUTH_TOKEN` where the authenticated verification path requires it;
- `B2_KEY_ID`;
- `B2_APPLICATION_KEY`;
- any protected Service Binding required by the private control-plane path.

The public repository's committed Wrangler configuration must contain the live public D1 binding once the deployment workflow has resolved it. Production credentials must never be committed.

The non-secret B2 configuration is fixed to the zero-cost deployment target:

- bucket: `SoloKing`;
- endpoint: `https://s3.eu-central-003.backblazeb2.com`.

## Deployment order

Deploy the private control-plane Worker first when a production change requires it, then deploy the public Worker. Production verification is then performed through the canonical authenticated chatbot/control-plane path; local DNS probing is not production evidence.

Smoke-test `/health` first. Treat `/readiness` according to the currently committed public readiness contract rather than assuming private-control-plane availability.

## Important operational lessons

- Never hard-code an obsolete D1 `database_id`; resolve it from Cloudflare and persist the current non-secret identifier when the public binding is unconfigured.
- Never deploy a generated Wrangler config containing `REPLACE_WITH_*` placeholders.
- For Python Workers use `pywrangler deploy`.
- Keep credentials and authentication secrets out of Git and handoff documents.
- Keep the strict `$0` policy fail-closed; do not add paid fallbacks to make deployment convenient.
- Do not call Cloudflare production verification complete until the authenticated chatbot evidence is current.
- Keep deployment and post-deployment verification as one explicit workflow chain: deployment first, smoke/verification second.
