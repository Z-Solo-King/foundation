# Credential and Backup Authority Standard

**Status:** normative  
**Owner:** Foundation deployment/backup boundary  
**Applies to:** `foundation` and the private `operations` repository

## Purpose

This is the canonical policy for credential purpose, secret separation, repository backup authentication, Backblaze B2 authority, backup artifacts, restore evidence, and remediation records.

The governing rule is: **a credential is named and scoped by the authority it serves; storage credentials are never repository credentials; repository credentials are never B2 credentials.**

## Credential and authority map

| Credential / resource | Canonical purpose | Authority | Must not be used for |
| --- | --- | --- | --- |
| `OPERATIONS_APP_ID` | Identify the GitHub App used by Foundation deployment | GitHub App / Foundation deployment | B2, Cloudflare, arbitrary repository writes |
| `OPERATIONS_APP_PRIVATE_KEY` | Sign the short-lived GitHub App JWT used to mint an Operations installation token | GitHub App / Foundation deployment | B2, Cloudflare, general repository writes |
| `OPERATIONS_APP_ID` + `OPERATIONS_APP_PRIVATE_KEY` | Mint a short-lived GitHub App installation token for private Operations backup mirroring | Foundation B2 backup workflow | B2, Cloudflare, arbitrary writes |
| `B2_KEY_ID` | Authenticate the backup workflow to the configured B2 S3 API | Backblaze B2 | GitHub, Cloudflare |
| `B2_APPLICATION_KEY` | B2 backup/restore application credential | Backblaze B2 | GitHub, Cloudflare |
| `B2_BUCKET` | Authoritative backup bucket name | B2 backup configuration | GitHub authentication |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API/deployment access | Cloudflare deployment boundary | GitHub, B2 |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account identifier | Cloudflare deployment boundary | GitHub, B2 authentication |
| `AUTH_TOKEN` | Application/runtime authentication where explicitly required | Application/runtime boundary | GitHub repository auth, B2 auth |

Never substitute one credential for another because the workflows run in the same GitHub repository or job.

## Backup GitHub repository access

The backup workflow uses the same purpose-specific GitHub App credential family already approved for private Operations source access: `OPERATIONS_APP_ID` and `OPERATIONS_APP_PRIVATE_KEY`. A short-lived installation token is minted at runtime and used only to mirror the private `operations` repository. The public `foundation` mirror does not require a private GitHub credential.

B2 credentials authenticate only to B2. The GitHub App credentials authenticate only to GitHub repository access. Neither credential is stored in or substituted for the other.

The backup workflow must mint a short-lived installation token, use a non-interactive Git HTTP credential/header, remove private key/JWT material during cleanup, and never print token values.

The backup workflow validates the GitHub App installation/token against the private Operations repository before cloning and validates B2 credentials separately against the configured B2 bucket. Passing both checks proves credential-purpose separation, not production or disaster-recovery certification.

## Production Operations credential

Production deployment uses a short-lived GitHub App installation token minted from the purpose-specific App secrets. The App is installed only on the private Operations repository with read-only Contents permission. Deployment and backup use the same App credential family but separate workflow authority and acceptance gates.

Before checkout, deployment must fail closed unless:

1. the App ID and private key secrets are present;
2. a valid short-lived App JWT is generated;
3. GitHub accepts the installation-token exchange;
4. the installation token can read `Z-Solo-King/operations`;
5. the exact approved immutable Operations revision is readable;
6. checkout verifies the expected commit SHA.

A B2 credential must never be accepted as an Operations GitHub credential.

## Backblaze B2 authority

Backblaze B2 is the authoritative artifact/backup storage provider under the strict zero-cost target.

Current configured target:

- bucket: `SoloKing`;
- endpoint: `https://s3.eu-central-003.backblazeb2.com`.

These are non-secret configuration facts. `B2_KEY_ID` and `B2_APPLICATION_KEY` are secrets and must remain in protected secret storage.

B2 stores backup/artifact material. It does not own identity, authorization, routing, resource limits, research evidence, model eligibility, deployment approval, or application result state.

## Backup artifact requirements

The canonical backup workflow mirrors both active repositories:

- `Z-Solo-King/foundation`;
- `Z-Solo-King/operations`.

Each backup must produce an immutable Git mirror archive and a machine-readable manifest containing non-secret provenance such as repository, visibility, `main` commit, tree, timestamp, archive name, SHA-256, size, and reference count.

A backup is verified only after:

- successful B2 upload;
- remote object metadata/size verification;
- remote download;
- SHA-256 comparison against the local archive;
- extraction;
- `git fsck --full --no-dangling`;
- confirmation that the expected `main` ref exists.

Upload success alone is not restore certification.

## Backup manifest evidence rules

Backup manifests are evidence records, not policy authority. They must never contain tokens, secret values, application keys, authentication headers, or Cloudflare credentials.

A field such as `remote_b2_restore_verified` may be `true` only when the corresponding remote restore test actually ran and passed. Never invent a healthy, zero, empty, or successful value.

## Disaster recovery distinction

Repository backup integrity and disaster-recovery certification are separate evidence classes. A valid archive proves recoverability of Git data only; full disaster recovery requires documented restoration of required operational dependencies and an explicit certification record.

GitHub CI success, B2 backup success, Cloudflare deployment success, and application runtime success must never be conflated.

## Rotation and incident handling

When a credential is shared across purposes, incorrectly named, rejected, exposed, or suspected to have insufficient scope:

1. stop relying on the ambiguous credential;
2. provision the purpose-specific replacement;
3. update the canonical workflow and documentation;
4. validate the replacement against its intended authority;
5. rotate/revoke the obsolete credential through the appropriate administrative surface;
6. retain the remediation record without storing the credential value.

A failed authentication event is evidence about the credential path; it is not evidence that the target repository or B2 is unavailable.

## Documentation ownership

This document owns credential-purpose and backup-boundary policy. `DEPLOYMENT.md` owns deployment procedure. `backup/README.md` and `.github/workflows/b2-repository-backup.yml` own backup execution details. Private runtime configuration remains owned by Operations.

Do not create competing credential-policy documents. Cross-repository records should reference this standard.

## Required change record

Any material credential, backup, retention, restore, deployment-access, or secret-scope change must record:

- what changed;
- why it changed;
- affected authority;
- exact repository/workflow/document;
- validation evidence;
- remaining external/admin gate;
- whether rotation/revocation is still required.

Production certification requires runtime evidence; source-code existence is not certification.
