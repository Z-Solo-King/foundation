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

## Autonomous governance and mechanical hygiene

- `.github/workflows/twice-daily-governance-sweep.yml` is a privileged family coordinator. It executes only from trusted `main`, uses a read-only Operations App token, and may dispatch existing allowlisted workflows plus issue/comment mutations through the Foundation GitHub token.
- `.github/workflows/repository-hygiene-autofix.yml` is a narrowly scoped write workflow. It runs only from trusted `main` by explicit dispatch, changes only mechanically formatted tracked files, opens a review PR, and never merges, deploys, changes policy, or accesses protected credentials.
- The autonomous planner receives aggregate Operations findings before external AI use; private source paths and protected values are not sent as planner context.
- AI output remains candidate assistance. Repository/code ownership, acceptance evidence, deployment, production promotion and rollback remain with their existing authorities.