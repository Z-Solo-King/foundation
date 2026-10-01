# GitHub Actions Marketplace Audit — 2026-10-01

## Scope

The supplied Marketplace extraction contains 10,000 spreadsheet rows including the header, representing 9,999 action entries.

The complete extracted dataset was classified locally. Keyword clusters overlap and are discovery counts, not quality scores.

| Cluster | Matching entries |
|---|---:|
| Security / secrets / vulnerability | 690 |
| Testing / quality / lint / static analysis | 1,268 |
| Release / deployment / packaging | 2,077 |
| Artifacts / build outputs / caching | 1,437 |
| AI / agent / LLM | 622 |
| Cloudflare / Wrangler | 49 |
| GitHub / PR / workflow tooling | 3,451 |
| Performance / benchmarking | 177 |
| Documentation | 467 |

## Current-project comparison

Foundation already implements many high-value Actions ecosystem controls:

- full-length SHA pinning for third-party actions;
- least-privilege workflow permissions;
- workflow concurrency controls;
- per-job timeouts on hardened workflows;
- OSSF Scorecard and zizmor workflow analysis;
- CodeQL;
- scoped GitHub App credentials;
- artifact receipts and runtime provenance;
- artifact-attestation permissions where required;
- immutable cross-repository revision pins;
- Python and Node dependency caching through setup actions;
- centralized workflow-policy tests.

GitHub currently recommends full-length commit-SHA pinning for third-party actions and minimum GITHUB_TOKEN permissions. OpenSSF Scorecard independently treats pinned dependencies and token permissions as supply-chain controls.

## Dependency-security gap investigation

The Marketplace extraction showed two relevant families:

1. GitHub's native Dependency Review Action.
2. OSV-Scanner / OSV.dev based scanning.

A native Dependency Review workflow was tested live. The action failed closed because Foundation's Dependency Graph is disabled. This is an environment capability gap, not an action syntax failure.

A live OSV-Scanner experiment was also performed. It found no lockfiles/package sources in the Foundation repository and therefore produced no dependency scan. It was removed rather than retaining a permanently ineffective workflow.

## Implemented improvement

The useful native capability is retained as a capability-aware workflow:

- .github/workflows/dependency-review.yml
- pull-request trigger plus manual dispatch;
- a read-only preflight checks the Dependency Graph capability;
- HTTP 200 enables the native dependency-review job;
- HTTP 404 records a notice and skips the unsupported capability;
- unexpected API responses fail closed instead of silently skipping;
- dependency review fails on newly introduced high-severity vulnerabilities when the graph is available;
- 5-minute preflight and 10-minute review timeouts;
- concurrency cancellation for obsolete PR runs;
- all third-party actions are pinned to full commit SHAs;
- deterministic tests enforce the contract.

This means the workflow is useful immediately without creating a permanently failing check, and it automatically becomes an enforcement control if the repository's Dependency Graph is enabled later.


## Strict $0 policy reconciliation — 2026-10-01

GitHub's current billing documentation states that standard GitHub-hosted runners are free for public repositories, while larger runners are charged even for public repositories. Usage above a paid/private allowance can also become billable, and without a valid payment method usage is blocked after the included quota. The Foundation repository is public, so the implementation deliberately restricts workflows to the static `ubuntu-latest` standard runner class. It does not rely on larger runners or private-repository hosted-runner allowances.

The project also treats Marketplace Apps differently from ordinary Actions. GitHub Marketplace permits both free and paid App plans; paid App plans use an account payment method, and a free trial of a paid plan automatically becomes a paid subscription unless canceled. Therefore **free trial is not considered $0-safe** for this project.

The repository-side rules are now:
- App paid plans: forbidden;
- App free trials: forbidden;
- App installation that requires adding a payment method: forbidden;
- external billing dependency: forbidden;
- Marketplace App installation: disabled by default;
- third-party Actions: exact full-SHA allowlist only;
- unknown/new Marketplace Action refs: denied until explicitly reviewed;
- Docker-based Actions: forbidden;
- non-standard/dynamic/paid runner labels: denied;
- zizmor Advanced Security mode: disabled;
- Scorecard result publishing: disabled.

### Current Action census

At the current Foundation `main`, the workflow inventory contains **69 workflow files** after the family-coverage and Foundation-owned feed-hunt additions. The first repository census found **15 unique immutable Action refs across 11 Action repositories**. During live PR validation against the current merge ref, three additional immutable refs already present in the repository were discovered. No unpinned third-party Action ref was found in that census, and all current `runs-on` targets are `ubuntu-latest`.

The reconciled current set is **18 unique immutable Action refs across 14 Action repositories**. The three additional refs are `actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3`, `actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e`, and `actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6`. GitHub maintains the first two and lists them under MIT licensing; artifact attestations are available in public repositories on current GitHub plans. The approved immutable set is recorded in `docs/GITHUB_ACTIONS_ZERO_COST_POLICY.json`. This is intentionally an allowlist rather than a popularity-based Marketplace selection: a newly introduced Action must first pass the zero-cost policy, security review, deterministic tests, and live validation.

The policy does not claim that an arbitrary third-party service is economically free merely because its Action is free to download. It only admits dependencies for which this repository has explicit project-side evidence and bounded policy coverage.

## What was deliberately not adopted

No Marketplace listing was treated as an authority simply because it was popular or present in the 10k extraction.

The project does not add:

- generic AI coding agents;
- overlapping secret scanners;
- generic cloud deployment wrappers;
- third-party Cloudflare deploy wrappers;
- duplicate lint/test aggregators;
- ineffective dependency scanners without dependency manifests;
- arbitrary SBOM generators;
- release automation that competes with the canonical Foundation release authority.

The existing architecture already owns these responsibilities.

## Supply-chain policy

Marketplace actions remain third-party dependencies. They must be:

1. pinned to an immutable full commit SHA;
2. reviewed for behavior and provenance;
3. granted only the permissions required by the job;
4. bounded by timeout and concurrency policy;
5. covered by deterministic repository policy tests.

## Artifact provenance

Artifact attestations remain appropriate for actual released software or artifacts, not for every test output. GitHub documents attestations as a provenance mechanism for artifacts that consumers will run or consume.

## Acceptance pipeline

Future Marketplace-derived improvements follow:

10k extraction -> complete classification -> project gap analysis -> native capability where possible -> full-SHA pin -> least privilege -> timeout/concurrency -> deterministic test -> live validation -> baseline review

The Marketplace is a discovery source, not a runtime authority.


## Hybrid & Alternative $0 implementation model

The 9,999 supplied Marketplace Action entries are a feature-discovery corpus as well as a dependency list. Paid or SaaS-backed Actions are not ignored: their workflow structure, input/output contracts, matrices, caching, release gates, security checks, attestations, retries, notifications, observability and other public behavior are researchable.

Direct paid dependencies remain outside canonical runtime. The useful capability is mapped to existing GitHub primitives, Cloudflare capabilities, open-source tooling, or a bounded free-quota route and then subjected to deterministic tests, security/resource/provenance checks and runtime evidence. The immutable Action allowlist remains the gate for anything actually executed as an Action.
