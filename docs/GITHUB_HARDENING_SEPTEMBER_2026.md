# GitHub Hardening Baseline — September 2026

This document records the public-repository controls that are part of the Research Intelligence Engine's GitHub execution model.

## Current project decisions

- `foundation` is the public, runnable CI/test/deployment repository.
- Private repositories are not prerequisites for public tests or public Worker execution.
- Standard GitHub-hosted runners remain the preferred compute path because public repositories using standard GitHub-hosted runners are not charged for runner minutes.
- Do not use larger billed runners for the zero-cost design.
- Third-party GitHub Actions must be pinned to full commit SHAs.
- Every workflow must declare explicit `permissions`.
- Public workflows must not use `pull_request_target`.
- Required CI workflows must also support `merge_group` before merge queue is enabled.

## Required repository settings

Apply a `main` ruleset in GitHub repository settings. Recommended rules are:

1. Require a pull request for changes to `main`.
2. Require the public test check to pass.
3. Require CodeQL for changes that affect code/security paths once its check name is stable.
4. Block force pushes and branch deletion.
5. Require conversation resolution when reviews are enabled.
6. Consider requiring linear history only if it does not make the project's recovery/debugging workflow worse.
7. Use signed-commit requirements only after commit-signing is configured and tested; do not enable a rule that becomes an avoidable self-inflicted outage.

Keep the first ruleset small and enforceable. Add stronger rules only after the corresponding workflow evidence exists.

## Supply-chain controls

- Dependabot watches GitHub Actions and Python (`pip`) dependencies weekly.
- CodeQL runs with the `security-extended` query suite.
- Public CI performs a deterministic scan for obvious private-family references and credential material.
- Workflow source references are statically checked for full SHA pinning.
- GitHub's public-repository secret protection should remain enabled; push protection is especially important because this project is public.
- Dependency review is a useful future PR gate if dependency-bearing changes become common; it should not be added merely to create another flaky status check.

## CI design

`public-tests` runs on pushes, pull requests, and `merge_group` events. It tests Python 3.13 and 3.14 and keeps a 100% branch-coverage gate for product sources. Workflow concurrency cancels superseded runs on the same ref to avoid wasting runner capacity.

Deployment remains a separate workflow that runs only after successful `public-tests` on `main`. Production smoke tests validate the deployed public Worker plus the D1/B2 lifecycle diagnostic.

## Credentials

The current deployment path still uses GitHub Actions secrets for the Cloudflare API token and account ID. GitHub OIDC is the preferred long-term pattern because it replaces long-lived cloud credentials with short-lived, job-scoped identity, but migration should happen only after the target Cloudflare authentication path is verified end-to-end.

The runtime `AUTH_TOKEN` is separate from the deployment credential. Rotate it independently and never commit it to the repository.

## Artifact provenance

When the project starts publishing distributable packages or release binaries, add GitHub artifact attestations to the release workflow and verify them before publication. Attestation workflows require the appropriate `id-token` and attestation permissions.

## What is intentionally not enabled yet

- Merge queue: useful later, but only after the repository is governed by a ruleset that actually requires it and after the `merge_group` checks have been observed on the real repository.
- OIDC deployment: pending provider-side verification.
- Artifact attestations: pending a real release artifact pipeline.
- Larger runners: rejected by the zero-cost policy.
- A large collection of micro-workflows: rejected because it increases failure surface without increasing evidence quality.

## Architecture gaps to track outside GitHub configuration

The historical September 2026 design contains capabilities that are stronger than today's public implementation. They remain product backlog items rather than being disguised as GitHub configuration:

- independently verifiable evaluation receipts;
- richer document/source versions and retention-aware observations;
- stronger evidence certificates and replay metadata;
- calibrated semantic entailment beyond lexical matching;
- adversarial retrieval-poisoning and concentration benchmarks;
- production-sized evaluation corpus plus continuous regression/adversarial sets;
- shadow/canary/rollback learning loop;
- measured external-service-limit re-verification;
- richer source profiles, method health, and replayable acquisition learning.

These must be implemented with the same fail-closed, non-destructive, provenance-first model as the existing system. GitHub status checks are evidence of build/test execution; they are not proof that a research result is factually correct.
