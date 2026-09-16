# B2 repository backup

The scheduled Foundation workflow mirrors both active repositories to the authoritative Backblaze B2 bucket and verifies upload integrity plus a remote Git restore.

## Credential separation

The backup workflow uses two independent credential families.

### GitHub repository credential

`BACKUP_GITHUB_TOKEN` is a GitHub read credential used only to mirror:

- `Z-Solo-King/foundation`;
- `Z-Solo-King/operations`.

It is **not** a B2 credential and must not contain or be substituted with a B2 key or application key.

The workflow validates this credential against the GitHub API before cloning the private Operations repository. It then uses an ephemeral `GIT_ASKPASS` helper for Git authentication and removes the helper during cleanup.

### Backblaze B2 credentials

- `B2_KEY_ID` — B2 API credential;
- `B2_APPLICATION_KEY` — B2 backup/restore credential;
- `B2_BUCKET` — authoritative backup bucket name.

Current B2 endpoint:

`https://s3.eu-central-003.backblazeb2.com`

The workflow validates the B2 credentials against the configured bucket separately from the GitHub credential check. These B2 credentials authenticate only to B2 and are never valid substitutes for GitHub authentication.

## Deployment credential is separate

Production deployment uses the purpose-specific GitHub App credential pair (`OPERATIONS_APP_ID`, `OPERATIONS_APP_PRIVATE_KEY`), not `BACKUP_GITHUB_TOKEN`.

The production workflow resolves the installed Operations App installation dynamically and mints a short-lived installation token for the approved Operations checkout. `OPERATIONS_APP_INSTALLATION_ID` is not a stored production secret authority and should not be documented as one.

The App is installed with read-only Contents access on the private Operations repository. The App key and generated token are never printed or stored in the backup artifact set.

The normative credential and backup policy is `docs/CREDENTIAL_AND_BACKUP_AUTHORITY.md`.

## Backup contents

The workflow creates for each repository:

- immutable Git mirror archive;
- machine-readable manifest;
- `main` commit and tree identifiers;
- reference count;
- archive SHA-256;
- archive size;
- local Git integrity evidence;
- remote B2 restore evidence.

Backup manifests contain non-secret provenance only. They must never contain tokens, B2 application keys, Cloudflare credentials, authentication headers, GitHub App private keys, or other secret values.

## Verification standard

A backup is not considered verified merely because B2 accepted an upload.

The workflow must perform:

1. B2 object metadata/size verification;
2. remote archive download;
3. SHA-256 comparison;
4. extraction;
5. `git fsck --full --no-dangling`;
6. confirmation that the expected `main` reference exists.

A valid repository archive is evidence of Git-data recoverability. Full disaster-recovery certification remains a separate acceptance class.

<!-- GitHub App deployment-auth boundary verified 2026-09-16; no B2 credential reuse. -->
