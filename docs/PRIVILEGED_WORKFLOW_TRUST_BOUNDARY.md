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

## Live AI provider cross-fire

- `.github/workflows/live-ai-provider-crossfire.yml` remains a manual-dispatch privileged benchmark because it reads protected provider configuration and a read-only private Operations App token.
- The workflow resolves an immutable Operations revision before executing the private benchmark and uses `persist-credentials: false` for the private checkout.
- The workflow validates the canonical platform-access cross-fire contract before provider execution, then runs up to six configured provider lanes concurrently through the existing private benchmark runner.
- The public Foundation bridge contains no provider keys or provider endpoints; credential-bearing provider configuration remains in private Operations/runtime context.


## Cross-fire automation gate

The twice-daily governance sweep may dispatch `.github/workflows/live-ai-provider-crossfire.yml` only after the deterministic scanner emits `ai_escalation_required=true`. The sweep checks for an already queued/in-progress CrossFire run before dispatch, and explicit dry-runs never dispatch providers.

This is an escalation path into an existing benchmark, not a second AI scheduler or provider router. The benchmark remains independently bounded to six provider/API lanes, preserves private responses, and reports evidence strength without changing acceptance, policy or deployment authority.
