# Deployment

Foundation owns the single production deployment workflow in `.github/workflows/heroic-ai-production-release.yml`. Its workflow name is `Heroic AI production release`. The workflow deploys the public Worker and, after the public deployment succeeds, deploys the explicitly approved private Operations revision.

## GitHub Actions ownership boundary

All GitHub Actions automation for the active family is executed from public `foundation`. The private `operations` repository must contain no `.github/workflows` and must not be its own CI, scheduled-job, workflow-dispatch, or deployment owner. Foundation uses the approved GitHub App to read private Operations source when automation requires it.

## External private-runtime Actions route

Private Operations and the private runtime never dispatch Foundation target workflows directly. Their single public automation ingress is `.github/workflows/foundation-canonical-workflow-bridge-v3.yml`.

The route is:

private runtime -> Foundation GitHub App installation token (Actions: write) -> Foundation `workflow_dispatch` router -> canonical Foundation workflow

The bridge allowlists only the nightly research, production release, cross-repository contract-drift, centralized Operations validation, and main-push control-plane probe workflows. Production still requires explicit confirmation.

The Foundation GitHub App installation used by the private runtime must have Actions: write on `foundation`; the bridge itself creates a short-lived Foundation installation token with Actions: write to dispatch the selected workflow. GitHub documents that GitHub App installation tokens can create workflow-dispatch events with Actions: write. citeturn780911search4turn480911search6

Direct private-to-target workflow dispatch is prohibited so that all family automation remains observable and governed through one public routing surface.

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


## Private Operations validation

The public workflow `.github/workflows/operations-centralized-validation.yml` is the CI owner for the private Operations repository. It uses the approved GitHub App read credential to check out `Z-Solo-King/operations`, validates the private-repository boundary, runs the Operations test suite, and fails if Operations contains any GitHub Actions workflow.

Scheduled and manual validation happen on Foundation runners. Operations itself has no GitHub Actions execution surface.

## Production re-release rule

When production runtime provenance or the deployed private Operations revision must be refreshed, the supported mechanism is a normal merge to `main`. The canonical `.github/workflows/heroic-ai-production-release.yml` is push-to-`main` owned and runs `scripts/production_release.sh`.

Do not create a second deployment workflow, direct Cloudflare deployment path, private Operations Actions workflow, or manual Cloudflare Build/Deploy Hook to refresh production.
## Evidence and closure

A successful repository-side change does not prove production deployment. Deployment issue closure requires an actual successful post-merge Foundation Actions run proving the complete chain. Cloudflare production state, D1 bindings, Worker bindings, scheduled triggers, and live runtime behavior are verified separately in the Cloudflare-only operational context.

## Current approved production revision

The current explicitly approved Operations production revision is:

`79f5e4e413f663fc2d8484acd090676fbe957625`

This is the explicitly approved immutable Operations revision for the next canonical production release. It is not a live runtime certificate until the canonical production workflow succeeds against the corresponding Foundation revision.

## Credential rotation boundary

`OPERATIONS_APP_ID` and `OPERATIONS_APP_PRIVATE_KEY` are dedicated GitHub App deployment credentials. They are intentionally independent from Backblaze B2 application credentials, Cloudflare credentials, and application `AUTH_TOKEN`. The resolved installation token is short-lived and generated only for the approved Operations checkout.
