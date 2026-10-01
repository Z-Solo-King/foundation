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

A native Dependency Review workflow was tested on the PR during this audit. The live run failed closed with GitHub's explicit message that Dependency Review is not supported because the repository's Dependency Graph is disabled. This is an environment capability gap, not an action syntax failure.

The unsupported workflow was removed rather than leaving a permanently failing check in the project.

## Implemented improvement

Foundation now adds an advisory OSV-Scanner workflow:

- .github/workflows/osv-scanner.yml
- pull-request scanning;
- weekly scheduled scanning;
- manual dispatch;
- contents read plus job-scoped security-events write for SARIF reporting;
- 15-minute timeout;
- concurrency cancellation for obsolete PR runs;
- full SHA pin to OSV-Scanner Action v2.6.0;
- advisory mode during the initial baseline period so existing findings do not silently become unrelated merge blockers;
- deterministic tests enforcing the workflow contract.

OSV-Scanner is an appropriate fallback because it uses the OSV vulnerability database and supports multiple dependency ecosystems. Once the baseline is reviewed, the project can decide whether newly introduced findings should become blocking.

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

10k extraction -> complete classification -> project gap analysis -> native capability where possible -> full-SHA pin -> least privilege -> timeout/concurrency -> deterministic test -> live validation -> baseline review

The Marketplace is a discovery source, not a runtime authority.
