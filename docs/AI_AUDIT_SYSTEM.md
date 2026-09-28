# AI Audit System
**Status:** current family-wide audit operating system.

## Purpose
One composable system for code, documentation, GitHub structure, chatbot behavior, GitHub Actions, benchmarks, research orchestration and migration.

## Audit modes
1. Mechanical inventory — tree/files/issues/PRs/refs only; no mutation.
2. Issue-first — issues/PRs/comments only; cluster before code work.
3. Structure/ownership — authority registry, imports, paths, duplicate ownership.
4. Documentation drift — canonical links, historical/current boundaries, stale references.
5. Cross-language — independent language/paradigm lenses on the same contract.
6. Contract/differential — reference vs candidate on frozen corpora.
7. Security/adversarial — auth, SSRF, injection, secrets, bypass, hostile input.
8. Resource/replay — quota, reservation, leases, idempotency, crash/reclaim, concurrency.
9. Workflow/CI — trigger, permissions, refs, secret flow, job graph, artifacts, deployment.
10. Benchmark — repeated runs, p50/p95/p99, resource cost and lineage.
11. Runtime acceptance — exact deployed revision + live receipt; R3/R4 only.
12. Hybrid — compose multiple modes and reconcile evidence.
13. Evolution — convert new blind spots into rules/tests and detector improvements.

## Issue-first rule
Start large audits without code writes. Enumerate, classify and cluster by canonical owner + file surface + acceptance dependency. Append new findings to an existing issue when those dimensions match. Create a new issue only when no existing issue can own the behavior or acceptance.

## Parallel / simultaneous lanes
Default four capacity lanes:
A forward: producer/entrypoint -> consumer -> terminal state.
B reverse: terminal/consumer -> upstream producer -> policy.
C contract-first: contract/policy -> implementation -> tests -> workflow.
D evidence-first: receipts/tests/workflow -> implementation -> docs -> acceptance.
For six+ lanes, add E policy -> side effect -> recovery and F side effect/telemetry -> receipt/acceptance. More lanes require non-overlapping boundaries. Read-only work may run simultaneously; shared writes remain serialized.

## Cross-fire
Every material deterministic finding gets two independent lenses. Use source/authority, another language/paradigm, focused test/CI, runtime receipt, current external documentation, or issue/history provenance. Agreement is corroboration; disagreement remains a first-class finding.
The AMD CrossFire analogy is only about splitting independent work across execution resources and coordinating delivery; AMD CrossFire itself is a multi-GPU rendering technology.

## Hybrid profiles
Project: inventory -> ownership -> cross-fire -> security -> CI -> docs -> issue cluster.
Chatbot: intent -> route -> provider admission -> resources -> generation -> terminalization -> memory/learning -> evidence.
Actions: trigger -> permissions -> refs -> secrets -> jobs -> artifacts -> deploy -> rollback.
Benchmark: corpus -> reference/candidate -> exact output -> repeats -> cost -> lineage.
Research: contract -> planner -> router -> acquisition -> observation -> evidence -> verification -> gaps -> budget stop -> publication.
Migration: owner -> baseline -> candidate -> differential -> adversarial -> benchmark -> shadow -> canary -> rollback.

## 6. Uniform map record format

Every mapped feature uses: id, surfaces, functions, function_files, key, usage, policies, policy_logic, consumers, tests, workflow links and evidence.
Every connection uses: from, to, via, purpose, owner, auth, policies and evidence.
Every credential uses: surface, name, class, purpose, value_in_repo and scope_rule. Secret values are never map data.
Every language entry uses: language, files, where, why, how and policies.
Credential identity is surface + repository/Worker + environment + purpose. Identical variable names do not imply identical credentials.
Runtime rows require observed_at and evidence source; snapshots must be refreshed before mutation or production claims.

## AI Brain
Node types: file, symbol, feature, policy, issue, PR, workflow, test, artifact, receipt, external source.
Edges: owns, calls, consumes, protects, validates, documents, tests, deploys, produces, depends_on, duplicates, supersedes.
At every turn: resolve ownership -> minimize retrieval -> assign independent boundaries -> merge evidence -> cluster symptoms -> choose smallest safe repair -> second-lens validation -> update rules/map.
Chat history is never a source-of-truth edge.

## Continuous evolution
Classify reproducible surprises as known, new-defect, new-blind-spot, false-positive, stale-data or tool-limit.
new-defect -> existing canonical issue when possible; new-blind-spot -> audit rule/test; false-positive -> detector refinement; stale-data -> freshness rule; tool-limit -> retrieval/lane change; known -> no duplicate ticket.

## Stop/evidence rules
Never close R3/R4 from source inspection or deterministic CI alone. A blocked lane immediately work-steals. Stop only on a definitive receipt, evidenced external/admin block, collision boundary, or known-authority rediscovery with no new information.

## Authority
AI_PROJECT_MAP.json is navigation metadata. REPOSITORY_MAP.json, family authority registries and canonical contracts remain authoritative.

## External basis
GitHub documents CodeQL multi-language/custom analysis, secret scanning, dependency review and least-privilege/full-SHA Actions practices. OWASP ASVS provides structured security verification requirements. AMD documents CrossFire as multi-GPU frame/render scheduling.
References: https://docs.github.com/en/code-security/concepts/code-scanning/codeql ; https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning ; https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review ; https://docs.github.com/en/actions/reference/security/secure-use ; https://owasp.org/projects/asvs ; https://www.amd.com/en/resources/support-articles/faqs/DH-018.html