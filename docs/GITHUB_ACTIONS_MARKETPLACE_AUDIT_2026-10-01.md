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
