# Privileged Workflow Trust Boundary

Foundation has two classes of GitHub Actions:

1. **Unprivileged validation** — may execute pull-request code and must not receive production/private credentials.
2. **Privileged release/backup** — may access deployment or backup credentials and therefore may execute only from the canonical repository's trusted `main` revision or an explicit manual dispatch of that trusted workflow.

## Required invariants

- Privileged workflows do not use `pull_request` or `pull_request_target` triggers.
- Privileged workflows do not checkout a pull-request head, fork ref, or downloaded pull-request artifact for execution.
- The production release checks both the canonical repository identity and `refs/heads/main` before invoking the credential-bearing release script.
- Production release and backup workflows have `contents: read` GitHub token permissions unless a narrower step-specific permission is explicitly required.
- Third-party actions are pinned to immutable commit SHAs.
- Production release execution is serialized so two credential-bearing deployments cannot race.
- Backup and deployment credentials are separate purposes; backup credentials are never used by the production release path.
- Exact repository revision, private Operations revision, and workflow run identity are retained by the corresponding workflow artifacts/logs where supported.

## Trust model

A pull request from a fork is untrusted input. A protected merge to `main` is the repository's source-level trust boundary. Repository inspection cannot prove that GitHub repository administration has configured least-privilege secret scopes or deployment-environment approval; those remain administrative/runtime evidence requirements.

This contract therefore prevents the repository workflows from intentionally granting privileged credentials to pull-request execution while explicitly retaining the remaining administration gate rather than claiming it is verified.
