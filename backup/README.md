# B2 repository backup

The scheduled Foundation workflow mirrors both active repositories to the authoritative Backblaze B2 bucket and verifies upload integrity plus a remote Git restore.

## Credential separation

The backup workflow uses two independent credential families.

### GitHub repository access

The backup workflow uses `OPERATIONS_APP_ID` and `OPERATIONS_APP_PRIVATE_KEY` to mint a short-lived GitHub App installation token used only to mirror private Operations:

- `Z-Solo-King/foundation`;
- `Z-Solo-King/operations`.

The public Foundation mirror is readable without private credentials. The App installation token is not a B2 credential and must not be substituted with a B2 key or application key.

The workflow validates the App installation/token against the GitHub API before cloning the private Operations repository. It then uses a non-interactive Git HTTP Authorization header and removes App key/JWT material during cleanup.

### Backblaze B2 credentials

- `B2_KEY_ID` — B2 API credential;
- `B2_APPLICATION_KEY` — B2 backup/restore credential;
- `B2_BUCKET` — authoritative backup bucket name.

Current B2 endpoint:

`https://s3.eu-central-003.backblazeb2.com`

The workflow validates the B2 credentials against the configured bucket separately from the GitHub credential check. These B2 credentials authenticate only to B2 and are never valid substitutes for GitHub authentication.

## Deployment credential is separate

Production deployment and backup both use the same purpose-specific GitHub App credential family for private Operations source access; the workflows retain separate authority, lifecycle and acceptance gates.

The production workflow resolves the installed Operations App dynamically and mints a short-lived installation token for the approved Operations checkout. `OPERATIONS_APP_INSTALLATION_ID` is **not** a stored production secret authority.

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


## Retention and storage bound

The scheduled backup creates a new generation only on its daily run or a manual dispatch; ordinary main commits no longer trigger a full backup. After the new generation's object metadata, SHA-256, remote download, extraction and Git integrity checks all pass, the workflow deletes older B2 object versions under the repository-backup/ prefix and retains only the latest verified generation. A failed backup therefore leaves the previous verified generation intact.

Cleanup is version-aware. Backblaze B2 buckets are versioned, so deleting an object by key alone creates a delete marker while older versions can remain stored. The cleanup lists object versions and permanently deletes stale version IDs instead.

The B2 backup Application Key must permit the object listing and deletion capabilities required by the cleanup path. Those deletion capabilities are used only for the dedicated repository-backup/ prefix.

This design bounds the recurring backup storage to roughly one full repository generation rather than accumulating another multi-gigabyte archive on every commit. It is separate from B2 Usage Report monitoring; the Operations dashboard does not need B2 credentials to enforce this retention policy.


## Archive size and B2 upload limit

Backblaze distinguishes the 5 GB single-file/single-request boundary from large-file uploads. Large files can be assembled from parts and are supported up to 10 TB; each part may be up to 5 GB. citeturn625848search0turn625848search2

This workflow measures every compressed archive before upload. It does not send an archive larger than the 5,000,000,000-byte single-PUT threshold as one request. The AWS S3 transfer manager is configured for multipart transfer with a 100 MB threshold and 100 MB parts, so a growing repository is transferred in bounded parts. The workflow fails closed only if the archive exceeds the 10 TB B2 large-file ceiling. citeturn625848search0

The manifest records the archive byte size and upload policy. After upload, the workflow verifies remote size and SHA-256 and then performs the remote restore test.