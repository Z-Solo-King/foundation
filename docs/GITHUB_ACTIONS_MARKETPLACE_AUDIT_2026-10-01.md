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

## Gap selected for implementation

The extracted Marketplace contains many dependency-security actions, but Foundation did not have a direct dependency-review gate.

That control is materially different from workflow static analysis: it evaluates dependency changes introduced by a pull request.

The project therefore adds the native GitHub actions/dependency-review-action rather than several overlapping third-party scanners.

Implemented:

- .github/workflows/dependency-review.yml
- pull-request trigger plus manual dispatch;
- contents: read only;
- 10-minute job timeout;
- concurrency cancellation for obsolete PR runs;
- failure threshold at high;
- full SHA pin to the verified v5.0.0 release commit;
- regression tests enforcing the contract.

## What was deliberately not adopted

No Marketplace listing was treated as an authority simply because it was popular or present in the 10k extraction.

The project does not add:

- generic AI coding agents;
- overlapping secret scanners;
- generic cloud deployment wrappers;
- third-party Cloudflare deploy wrappers;
- duplicate lint/test aggregators;
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

10k extraction -> complete classification -> project gap analysis -> native capability where possible -> full-SHA pin -> least privilege -> timeout/concurrency -> deterministic test -> PR validation

The Marketplace is a discovery source, not a runtime authority.
