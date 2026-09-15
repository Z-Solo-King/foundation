# B2 repository backup

The scheduled Foundation workflow mirrors both active repositories to the authoritative Backblaze B2 bucket and verifies upload integrity plus a clean Git restore.

Required GitHub Actions secrets:

- `B2_KEY_ID`
- `B2_APPLICATION_KEY`
- `B2_BUCKET`
- `BACKUP_GITHUB_TOKEN`

The GitHub token is used only for read-only repository mirroring. The B2 application key should be bucket-scoped to the authoritative backup bucket and limited to the capabilities required for backup and restore.

The backup workflow does not expose secret values in logs and uses an ephemeral `GIT_ASKPASS` helper for Git authentication.
