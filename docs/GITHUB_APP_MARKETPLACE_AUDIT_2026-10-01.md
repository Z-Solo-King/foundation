# GitHub App Marketplace Audit — 2026-10-01

## Dataset integrity

The supplied workbook was inspected in full. It contains **1,408 GitHub App entries**, all with unique Marketplace names/URLs in the extracted sheet.

This is **not 10,000 Apps**. The earlier 10,000-row extraction was the separate GitHub Actions dataset. This workbook contains 1,408 Apps, and the audit below covers all 1,408 supplied rows.

## Functional clusters

Keyword/function clusters overlap. Counts are discovery signals, not quality scores or rankings.

| Cluster | Matching apps |
|---|---:|
| Security / secret management | 125 |
| AI / agent / code intelligence | 303 |
| Code review / quality | 183 |
| CI / build / deployment | 126 |
| Project / issue / chat | 99 |
| Observability / monitoring | 26 |
| Documentation / knowledge | 57 |
| Performance / optimization | 36 |
| Cloud / infrastructure | 37 |

## High-relevance examples found in the supplied dataset

Representative apps include GitGuardian, Snyk, Semgrep, Socket Security, SonarQube Cloud, CodeRabbit, Qodo, DeepSource, Linear, Atlassian/Jira, Slack + GitHub, Datadog, and several AI coding-agent apps.

These are examples of capability families discovered in the dataset. Their presence in the Marketplace does not imply that they should be installed in Foundation or Operations.

## Current architecture comparison

The project already has a first-party GitHub App boundary for private Operations access. Current workflows create a short-lived, repository-scoped installation token with `contents: read`; existing controls also validate the private repository boundary and keep Operations out of hosted GitHub Actions. The canonical production workflow remains Foundation-owned.

The project also already uses least-privilege GitHub Actions permissions and immutable revision pins. Existing workflow policy enforces full-SHA third-party Action references.

## Main App-specific lessons applied

GitHub documents that installing a GitHub App grants the app the permissions requested during installation and allows repository selection. GitHub also distinguishes installation from user authorization. Apps should therefore be treated as a separate capability boundary from ordinary Actions.

GitHub's current guidance for creating Apps recommends minimum permissions, scoped installation tokens, expiration/revocation, minimal webhooks, secret-protected webhooks, rate-limit awareness, and regular security scanning.

Those principles are now encoded in `docs/GITHUB_APP_INTEGRATION_POLICY.json` and validated by a dedicated repository workflow.

## Implemented project changes

### 1. Explicit App installation policy

`docs/GITHUB_APP_INTEGRATION_POLICY.json` now defines:

- Marketplace installation disabled by default;
- explicit approval required before any external App is activated;
- repository scope restricted to Foundation and Operations;
- a read-only permission baseline;
- stronger permissions requiring documented need, review, deterministic testing, live evidence, and rollback;
- deployment and production-authority roles forbidden;
- secret mutation authority forbidden;
- webhooks disabled by default;
- signature validation and HTTPS required when webhooks are introduced;
- minimum-event subscription policy;
- Marketplace treated as discovery-only rather than runtime authority.

### 2. Deterministic validator

`scripts/validate_github_app_policy.py` rejects unexpected repository scope, external Marketplace Apps activated outside review, non-read-only baseline permissions, disabled security controls, or any attempt to grant deployment/production authority.

### 3. CI enforcement

`.github/workflows/github-app-governance.yml` runs on changes to the App boundary and executes the policy validator and dedicated regression tests. The workflow itself uses least privilege, a 10-minute timeout, concurrency cancellation, and full-SHA pinned Actions.

## What was not installed

No Marketplace App was installed automatically.

The dataset contains many AI agents, code-review services, security SaaS products, project-management integrations, deployment platforms, and observability products. Introducing them without an explicit installation decision would expand the permission and external-service surface. GitHub requires an App to be installed on the relevant account/repositories before it can operate there, and the installation grants the requested permissions. Therefore an audit can safely improve the project's governance without silently installing external services.

## Specific capabilities that remain research-only

- AI coding agents: research only;
- autonomous code review: research only;
- third-party secret/SaaS security services: research only;
- project-management synchronization: research only;
- third-party deployment: forbidden for canonical production;
- production authority: forbidden for Marketplace Apps.

This preserves the existing one-authority-per-responsibility architecture.

## Acceptance model

Future GitHub App changes follow:

`Marketplace extraction -> complete classification -> current-project gap analysis -> explicit installation decision -> minimum repository scope -> minimum permissions -> short-lived credential -> webhook minimization -> signature validation -> deterministic policy test -> live evidence -> rollback plan`

Marketplace discovery is not itself an authorization or deployment boundary.
