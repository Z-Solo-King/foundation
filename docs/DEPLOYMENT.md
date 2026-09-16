# Deployment

Foundation owns the single production deployment workflow in `.github/workflows/codeql.yml`. That workflow deploys the public Worker and, after the public deployment succeeds, deploys the explicitly approved private Operations revision.

## Production authority

- Public Worker deployment authority: `.github/workflows/codeql.yml`
- Private Operations repository: `Z-Solo-King/operations`
- Approved Operations production revision is pinned in the workflow as `OPERATIONS_REF`.
- The Operations production revision is immutable for a deployment run; the workflow fails closed if the expected pin changes.
- Operations remains a private runtime/control-plane repository and is not deployed by a separate GitHub-hosted Operations workflow.

## Required GitHub Actions secrets

The deployment workflow uses separate credential authorities. Do not reuse storage/provider credentials for GitHub repository access.

- `OPERATIONS_READ_TOKEN`: GitHub credential authorized to read the private `Z-Solo-King/operations` repository and the pinned production commit.
- `CLOUDFLARE_API_TOKEN`: Cloudflare API credential required by the canonical deployment workflow.
- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare account identifier.
- `AUTH_TOKEN`: application authentication secret, when protected authenticated smoke verification is enabled.

Backblaze B2 credentials are separate application/runtime credentials. They must never be stored in or substituted for `OPERATIONS_READ_TOKEN`.

## Operations deployment sequence

The canonical workflow performs the following in order:

1. pass Foundation public tests and static analysis;
2. deploy the tested Foundation public Worker;
3. run public production smoke checks;
4. validate `OPERATIONS_READ_TOKEN` against the expected private Operations repository and approved commit through the GitHub API;
5. fetch and verify the exact approved Operations revision;
6. apply the canonical Operations resource-governance D1 schema;
7. deploy the exact Operations Worker revision;
8. remove the ephemeral checkout, temporary authentication helper, and generated configuration.

A credential failure stops the deployment before any Operations deployment step. A wrong credential must not be silently retried with a B2 or other provider credential.

## Evidence and closure

A successful repository-side change does not prove production deployment. Deployment issue closure requires an actual successful post-merge Foundation Actions run proving the complete chain. Cloudflare production state, D1 bindings, Worker bindings, scheduled triggers, and live runtime behavior are verified separately in the Cloudflare-only operational context.

## Current approved production revision

The current explicitly approved Operations production revision is:

`cf28a28cb40de527aff1cd87f96e103669635f70`

This is a signed Operations commit implementing the durable D1 governance runtime. The deployment workflow must not silently substitute a newer Operations `main` commit without a new explicit approval change.

## Credential rotation boundary

`OPERATIONS_READ_TOKEN` is a dedicated GitHub repository-read credential. It is intentionally independent from Backblaze B2 application credentials, Cloudflare credentials, and application `AUTH_TOKEN`. Rotating or replacing one provider's credential must not require changing another provider's secret name or value.
