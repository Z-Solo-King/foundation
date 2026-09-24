# Deployment

This repository contains the public contract/Worker boundary. Production control-plane implementation details remain in the private `operations` repository.

## Current verified production state

Historical production verification is retained as historical evidence only. The 2026-09-13 manual verification is not current certification.

Current acceptance requires fresh authenticated evidence from the approved GitHub deployment path and, where applicable, separate Cloudflare production verification.

The public Worker is deployed with Python Worker tooling (`pywrangler`), not plain `wrangler deploy`.

## Canonical production workflow

The canonical Foundation production deployment workflow is `.github/workflows/heroic-ai-production-release.yml`. It contains the single `pywrangler deploy` production owner and runs the public deployment only after `Public tests` succeeds on a push to `main`.

The same workflow performs the public post-deployment smoke checks. There is no second public production deployment workflow.

The workflow dynamically resolves the live D1 database ID and writes a runner-only Wrangler configuration. Generated configuration is removed during cleanup. Credentials are never committed.

The workflow also owns the protected Operations handoff. Production is pinned to the explicitly approved immutable Operations revision:

`44f53283aa308e8a294ae9fe716ab9200a44809b`

The private Operations checkout uses the purpose-specific GitHub App installation credential set:

- `OPERATIONS_APP_ID`;
- `OPERATIONS_APP_PRIVATE_KEY`.

The installation ID is derived dynamically from the App JWT at runtime; it is not a stored secret or independent authority.

The workflow mints a short-lived installation token at runtime, verifies access to the private Operations repository and exact approved revision, then uses that token for checkout. The generated token and key material are masked/removed and never printed. These credentials are for the Foundation deployment handoff only; they are not B2 or Cloudflare credentials.

The canonical credential and backup policy is `docs/CREDENTIAL_AND_BACKUP_AUTHORITY.md`.


## GitHub Actions ownership boundary

All GitHub Actions automation for the active family is executed from public `foundation`.

The private `operations` repository must not contain `.github/workflows` and must not execute CI, scheduled jobs, workflow dispatch, or deployment automation itself.

When Foundation automation needs private Operations source or metadata, it uses the approved Foundation GitHub App and short-lived installation token. This is a source-access/deployment boundary, not a runtime Worker boundary.

The runtime Foundation -> Operations path is a Cloudflare service binding plus the canonical `AUTH_TOKEN` check.


## Credential boundaries

| Secret | Purpose | Owner | Not interchangeable with |
| --- | --- | --- | --- |
| `OPERATIONS_APP_ID` | Identify the GitHub App used for private Operations deployment access | Foundation deployment workflow | B2 secrets, Cloudflare secrets |
| `OPERATIONS_APP_PRIVATE_KEY` | Sign the short-lived GitHub App JWT | Foundation deployment workflow | B2 secrets, Cloudflare secrets |
| `OPERATIONS_APP_ID` + `OPERATIONS_APP_PRIVATE_KEY` | Mint short-lived GitHub App token for private Operations source access during deployment and backup | Foundation deployment/backup workflows | B2 secrets, Cloudflare secrets |
| `B2_KEY_ID` | B2 API authentication | B2 backup boundary | GitHub tokens, Cloudflare tokens |
| `B2_APPLICATION_KEY` | B2 backup/restore authorization | B2 backup boundary | GitHub tokens, Cloudflare tokens |
| `CLOUDFLARE_API_TOKEN` | Cloudflare deployment/API access | Cloudflare deployment boundary | GitHub tokens, B2 secrets |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account identifier | Cloudflare deployment boundary | GitHub tokens, B2 secrets |
| `AUTH_TOKEN` | Application/runtime authentication where required | Application/runtime boundary | GitHub tokens, B2 secrets |

Do not infer credential purpose from the fact that multiple secrets are consumed by one workflow. Each secret has an independent authority and scope.

## Operations deployment gate

Before the private Operations checkout, the workflow must fail closed unless the GitHub App credentials are present, the App JWT is valid, the installation-token exchange succeeds, and the resulting installation token can read `Z-Solo-King/operations`.

The checkout must then fetch and verify the exact approved revision `44f53283aa308e8a294ae9fe716ab9200a44809b`. Before Worker packaging, the deployment materializes the pinned public `foundation_core` package through `operations/scripts/sync_public_core.py`; the generated directory is ignored and never committed. The workflow must not silently track `operations/main`, substitute an older pin, or deploy a mutable branch reference.

A successful public Worker deployment does not prove that Operations was deployed. Operations deployment, D1 governance application, protected configuration and private runtime verification remain separately evidenced.

## Backblaze B2 boundary

Backblaze B2 is the authoritative artifact/backup storage provider under the strict zero-cost target.

Current target:

- bucket: `SoloKing`;
- endpoint: `https://s3.eu-central-003.backblazeb2.com`.

B2 credentials are secrets and never belong in Git, documentation, backup manifests, or logs. B2 stores artifact/backup material; it is not an authority for identity, authorization, routing, policy, resource governance, evidence, deployment approval, or application result state.

The repository backup workflow is `.github/workflows/b2-repository-backup.yml`; execution detail is documented in `backup/README.md` and policy in `docs/CREDENTIAL_AND_BACKUP_AUTHORITY.md`.

## Backup artifact and restore policy

The canonical backup workflow mirrors both active repositories:

- `Z-Solo-King/foundation`;
- `Z-Solo-King/operations`.

It creates immutable Git mirror archives and manifests containing non-secret provenance. Backup verification requires remote B2 download, SHA-256 comparison, extraction, `git fsck --full --no-dangling`, and confirmation of the expected `main` reference.

A successful upload is not disaster-recovery certification. Backup integrity, GitHub CI, Cloudflare deployment and application runtime are distinct evidence classes.

## Runtime architecture

The current public-safe architecture does not make public readiness depend on the private control plane. Protected Operations may use a private Service Binding to call Foundation where the protected verification path requires it.

Foundation uses:

- Cloudflare D1 for compact public/operational metadata where defined by the Foundation contract;
- Backblaze B2 for current artifact storage under the strict zero-cost design;
- no public route for arbitrary private control-plane dispatch.

## Deployment order

The Foundation production workflow owns the deployment path. Private Operations activation must not create a second GitHub deployment owner.

The public path is validated first. The protected Operations handoff is then validated against the exact approved revision. Cloudflare production state is verified separately by the dedicated Cloudflare-side procedure.

## Important operational rules

- Never hard-code an obsolete D1 `database_id`; resolve it from Cloudflare at deployment time.
- Never deploy a generated Wrangler config containing `REPLACE_WITH_*` placeholders.
- Use `pywrangler deploy` for Python Workers.
- Never commit credential values.
- Never put GitHub tokens, B2 keys, Cloudflare tokens, or application authentication tokens into backup manifests or handoff records.
- Do not use B2 credentials or application/runtime credentials as GitHub source-access credentials; use the purpose-specific GitHub App installation credential set.
- Do not reuse B2 credentials as GitHub credentials.
- Keep the strict `$0` policy fail-closed; do not add paid fallbacks to make deployment convenient.
- Do not claim Cloudflare production or application certification without current evidence.
- Keep deployment and its public post-deployment verification in the canonical workflow chain.
- Record material deployment, credential, backup, scope and evidence changes in the canonical policy/record documents.