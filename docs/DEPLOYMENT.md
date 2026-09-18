# Deployment

Foundation owns the single production deployment workflow in `.github/workflows/heroic-ai-production-release.yml`. Its workflow name is `Heroic AI production release`. The workflow deploys the public Worker and, after the public deployment succeeds, deploys the explicitly approved private Operations revision.

## Production authority

- Public Worker deployment authority: `.github/workflows/heroic-ai-production-release.yml`
- Private Operations repository: `Z-Solo-King/operations`
- Approved Operations production revision is pinned in `scripts/production_release.sh` and validated by the workflow policy.
- The Operations production revision is immutable for a deployment run; the workflow fails closed if the expected pin changes.
- Operations remains a private runtime/control-plane repository and is not deployed by a separate GitHub-hosted Operations workflow.

## Required GitHub Actions secrets

The deployment workflow uses separate credential authorities. Do not reuse storage/provider credentials for GitHub repository access.

- `OPERATIONS_APP_ID`: GitHub App identifier used to resolve the installed Operations repository authorization at runtime.
- `OPERATIONS_APP_PRIVATE_KEY`: GitHub App private key used only to mint the short-lived installation credential for the approved Operations checkout.
- `CLOUDFLARE_API_TOKEN`: Cloudflare API credential required by the canonical deployment workflow.
- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare account identifier.
- `AUTH_TOKEN`: application authentication secret, when protected authenticated smoke verification is enabled.

`OPERATIONS_APP_INSTALLATION_ID` is **not** a stored production secret authority. The workflow resolves the current installation from the GitHub App at runtime.

Backblaze B2 credentials are separate application/runtime credentials. They must never be stored in or substituted for the Operations GitHub App credentials.

## Operations deployment sequence

The canonical workflow performs the following in order:

1. pass Foundation public tests and static analysis;
2. resolve the installed Operations GitHub App installation from the App JWT;
3. deploy the tested Foundation public Worker;
4. run public production smoke checks;
5. fetch and verify the exact approved Operations revision using the short-lived installation credential;
6. apply the canonical Operations resource-governance D1 schema;
7. materialize the exact pinned Foundation public deterministic core into the ignored Operations checkout and verify its generated package entrypoint;
8. deploy the exact Operations Worker revision;
9. remove the ephemeral checkout, temporary authentication helper, private key material and generated configuration.

A credential failure stops the deployment before any Operations deployment step. A wrong credential must not be silently retried with a B2 or other provider credential.

## Evidence and closure

A successful repository-side change does not prove production deployment. Deployment issue closure requires an actual successful post-merge Foundation Actions run proving the complete chain. Cloudflare production state, D1 bindings, Worker bindings, scheduled triggers, and live runtime behavior are verified separately in the Cloudflare-only operational context.

## Current approved production revision

The current explicitly approved Operations production revision is:

`90e3c692bfd43da25d08bf5d47a6a6c5167e0f7f`

This is a signed Operations commit implementing the durable D1 governance runtime. The deployment workflow must not silently substitute a newer Operations `main` commit without a new explicit approval change.

## Credential rotation boundary

`OPERATIONS_APP_ID` and `OPERATIONS_APP_PRIVATE_KEY` are dedicated GitHub App deployment credentials. They are intentionally independent from Backblaze B2 application credentials, Cloudflare credentials, and application `AUTH_TOKEN`. The resolved installation token is short-lived and generated only for the approved Operations checkout.
