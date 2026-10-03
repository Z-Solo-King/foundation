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

- `.github/workflows/microscope-branch-retirement.yml` is a privileged maintenance workflow. It runs only from trusted `main` pushes carrying the explicit `[microscope-retirement-authorized]` marker or from explicit manual dispatch; branch eligibility is recomputed from live refs and protected/active-PR/release/tag/live-reference/divergent refs remain non-executable.

## Live AI provider cross-fire

- `.github/workflows/live-ai-provider-crossfire.yml` is a privileged benchmark with an autonomous nightly schedule plus explicit manual dispatch. It reads protected provider configuration and a read-only private Operations App token.
- The nightly benchmark is GitHub-hosted and session-independent: execution is driven by the GitHub Actions scheduler/runner, not by ChatGPT, an interactive agent session, or a chat session staying open.
- Manual dispatch remains available for operator-selected runs; scheduled runs resolve their own immutable Operations revision and publish the same public-safe summary artifact.
- The workflow resolves an immutable Operations revision before executing the private benchmark and uses `persist-credentials: false` for the private checkout.
- The workflow validates the canonical platform-access cross-fire contract before provider execution, then runs up to six configured provider lanes concurrently through the existing private benchmark runner.
- The public Foundation bridge contains no provider keys or provider endpoints; credential-bearing provider configuration remains in private Operations/runtime context.

## Migration synchronization — 2026-10-02

The Foundation/Operations migration removes private runtime and feed-execution implementation from the public tree while retaining public contracts, deterministic core behavior, hosted CI and release boundaries. Migration changes must preserve the privileged/unprivileged separation above.

The migration is considered structurally synchronized only when the protected PR checks, workflow-authority validator, public-surface scan, full-history secret scan and cross-system ownership/equivalence gates all evaluate the exact reconciled PR head.

## 2026-10-02 workflow reconciliation

The current GitHub workflow surface is treated as configuration under the same trust boundary as code: workflow YAML is syntax/structure-validated in the required merge gate, privileged workflows remain restricted to trusted triggers, and autonomous dispatch targets are allowlisted by the mission router. A workflow that exists in a historical mission record but does not expose `workflow_dispatch` is not a valid autonomous execution target.

## Public release prohibition — 2026-10-02

Feed-recovery workflows must never create or upload GitHub Releases or publish release download URLs. Normal feed jobs are read-only; the separate cleanup job is narrowly scoped to delete the prohibited feed release/tag.

## Public endpoint reconciliation — 2026-10-02

Credential-bearing workflows that probe or release the public application must target the canonical GitHub-backed Pages project `https://heroic-ai.pages.dev`. The public hostname change does not change the trust boundary: privileged workflows still require trusted `main` or explicit manual dispatch, and private Operations credentials remain inaccessible to pull-request code.

## Post-release chatbot verification — 2026-10-02

- `.github/workflows/chatbot-post-release-runtime-smoke.yml` is a privileged production smoke workflow because it exercises the canonical public endpoint with the protected application authentication token. It is manual-dispatch only and is launched by the trusted production-release workflow after a successful release; it fails closed on Foundation/Operations provenance mismatch.
- `.github/workflows/chatbot-post-release-crossfire.yml` is a privileged post-release benchmark because it reads protected provider configuration and private Operations source. It is manual-dispatch only and is launched by the trusted production-release workflow; it validates the six independent analytical lanes and runs up to six configured provider transports concurrently. Comparative agreement remains descriptive evidence only.
- Both workflows use immutable action references and read-only repository permissions; they do not alter deployment state, provider configuration, policy, or promotion authority.

## 2026-10-02 controlled Operations pin promotion staging

The promotion PR may stage the next immutable Operations revision in post-release workflow consumers before production deployment. Those workflows fail closed on readiness/provenance mismatch. The manifest marks the revision as a candidate until the controlled production release and fresh runtime evidence complete; approval and live-state records continue to identify the currently deployed revision during that interval.

## 2026-10-03 provider CrossFire credential recovery boundary

The privileged provider CrossFire workflow assembles runtime credentials from the protected aggregate provider secret when valid and from canonical direct provider secrets when present. Aggregate JSON parse failure is reported as configuration evidence and does not suppress valid direct credentials. Provider endpoint/model values remain catalog-owned; secrets provide credentials only.

A live run demonstrated that the GitHub connector/App boundary, private Operations checkout, six-lane platform validation, benchmark execution path, receipt generation and artifact upload are operational. Comparative execution remains fail-closed when fewer than two direct providers are configured. This is an environment-configuration blocker, not a repository connector-permission blocker.
