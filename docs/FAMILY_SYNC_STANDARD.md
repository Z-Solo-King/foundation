# Family Synchronization Standard

**Status:** normative; current
**Owner:** Foundation family boundary
**Scope:** Foundation + Operations

## Purpose

This document defines the uniform format and synchronization contract for the two-repository Heroic AI family. It prevents source code, documentation, tests, issue records, pull requests and evidence records from describing different system states.

The rule is simple: **one canonical fact, one owner, one format, one current revision, and one evidence level.**

## Repository identity

| Field | Foundation | Operations |
| --- | --- | --- |
| Role | public-safe contract, deterministic/evidence core, public Worker, CI and deployment/backup workflow | private Heroic AI control plane/runtime |
| Dependency direction | independent of Operations internals | may consume Foundation public contracts/core |
| Production deployment owner | canonical | receives explicitly approved revision |
| Private runtime CI | not applicable | intentionally external/private; no GitHub-hosted private runtime |

Exactly two repositories are active. Former extractor/mapper repositories are historical only.

## Canonical synchronization hierarchy

For a current fact, use this precedence:

1. current merged source on repository `main`;
2. executable contract/tests and current GitHub Actions evidence;
3. canonical source-of-truth/ownership documentation;
4. current open PRs, explicitly labeled proposed/unmerged;
5. active issue acceptance records;
6. historical audits, plans, handoffs and chat transcripts.

A lower layer must not override a higher layer.

## Current synchronization record

`docs/FAMILY_SYNC_STATE.json` is the uniform machine-readable audit snapshot for the family. Its `last_audited_main_sha` fields are observations of the branch tips at audit time; they are not authoritative aliases for the branch tips and become stale by design when `main` advances.

The current-state documents must therefore record both the observed branch SHA and the audit timestamp. A stale recorded SHA is a documentation synchronization finding, not evidence that the branch has reverted.

For the 2026-10-02 reconciliation, the Family Sync State records the live Foundation `main` head `4d54a85944ad28f8c22e80909dec874692d4dd4b` and live Operations `main` head `5cf716b8c8d9be4691f2544f2799dfd95cc29d4a` as observations. The immutable production Operations pin `da86e92d4e0fdb68912efb54ef95c69281a7d613` remains a separate production-authority value and is not replaced by the moving `main` head.

## Required current-state record

Every current-state document that records repository or family state should use these sections in this order when applicable:

1. **Status**
2. **Owner / canonical authority**
3. **Current repository revisions**
4. **Responsibilities / non-responsibilities**
5. **Canonical paths / contracts**
6. **Current tests / evidence**
7. **Active PRs / proposed changes**
8. **Open gates / external dependencies**
9. **Evidence boundary**
10. **Last material synchronization trigger**

Do not mix proposed, merged, deployed and verified states in one undifferentiated list.

## Uniform status vocabulary

Use these exact states for lifecycle/evidence summaries:

- `CURRENT` — present on the referenced merged revision;
- `PROPOSED` — exists only in an open PR or design proposal;
- `VERIFIED` — current execution evidence exists at the required level;
- `BLOCKED` — required evidence/control exists but an external dependency prevents completion;
- `DEFERRED` — intentionally postponed with a documented revisit condition;
- `HISTORICAL` — retained for provenance only;
- `SUPERSEDED` — replaced by a newer canonical record;
- `REMOVED` — deliberately deleted from the current tree.

Never use “done”, “complete”, “ready”, “healthy”, or “production” without an explicit status and evidence level when the distinction matters.

## Uniform evidence vocabulary

Use the evidence classes defined by `AI_AUDIT_AND_VERIFICATION_STANDARD.md`:

- **L0:** hypothesis;
- **L1:** source inspected;
- **L2:** repository-level inspection including callers/tests/ownership;
- **L3:** current execution/CI evidence;
- **L4:** current approved runtime/production evidence.

Claims must never exceed their evidence level.

## Uniform ownership format

Every canonical subsystem record should identify:

| Field | Meaning |
| --- | --- |
| `owner` | repository + canonical implementation |
| `contract` | stable consumer-facing interface/schema |
| `authority` | policy/state/data authority used by the subsystem |
| `non_authority` | responsibilities it explicitly cannot own |
| `tests` | focused suites protecting the contract |
| `compatibility` | facade/deprecation state, if any |

A compatibility facade is not a second owner.

## Uniform PR format

Every material PR should state:

1. **Scope** — exact behavior or structural boundary;
2. **Canonical owner changed** — exact path/module;
3. **Non-goals** — authority or infrastructure deliberately untouched;
4. **Safety** — policy/trust/resource/evidence implications;
5. **Tests** — exact focused tests and CI jobs;
6. **Evidence** — source/CI/runtime level actually observed;
7. **Remaining gate** — precise blocker, if any;
8. **Current base/head SHA** — revision pair used for review.

A stale base SHA must be called out and must prevent a PR from being treated as merge-ready until reconciled.

## Cross-system autonomous governance sweep

The Foundation autonomous supervisor is the family scheduler/decision coordinator; it does not replace component authorities. A dedicated Foundation workflow invokes it twice daily at **02:17 and 14:17 UTC** after deterministic, aggregate-only hygiene/code-document synchronization checks across Foundation and Operations.

The sweep uses the existing `audit_assist` task family through the canonical Operations provider runtime. Provider/model choice remains runtime-driven and zero-cost governed. The planner may dispatch only workflows represented in the mission router and project-improvement matrix.

The sweep may create or update GitHub issue/comment records with evidence references. Code changes are produced only by deterministic, explicitly allowlisted repair workflows that open review PRs; the AI planner cannot write source directly and cannot merge. Operations private runtime code remains under its existing protected authority and is not mutated by the public sweep.

A sweep finding is a candidate governance record until the referenced CI/runtime/evidence gate confirms it.

## Cross-system equivalence and CrossFire gate

The family CrossFire audit compares Foundation and Operations without merging their authorities. Its deterministic receipt materializes typed Cartesian comparisons for policy catalogs, feature domains, function declarations, tracked-file content and architecture flows; the symbolic model is N² × N² = N⁴, while execution remains bounded and evidence-producing.

Six semantic lenses are defined for independent review: ownership/policy, TypeScript edge/application, Rust deterministic kernels, Go concurrency/network, Cloudflare/runtime/deployment, and security/evidence/provenance. Parallel lanes may work independently, but mutations remain serialized through the canonical repository owner.

The live AI provider cross-fire may exercise up to six configured direct providers with bounded repeats/concurrency. Fewer than two configured providers produces an explicit non-comparative receipt rather than an inferred or fabricated provider comparison. Provider/model results remain supporting evidence and cannot transfer policy, correctness or deployment authority.

The family workflow treats full tracked-file classification, shared-policy divergence, focused differential evidence and fresh runtime receipts as separate gates. A 100% inventory result establishes coverage of the supplied tree; it does not by itself establish semantic equivalence or production readiness.

## Uniform issue format

Material issues should contain:

- **Current status**;
- **Current main evidence**;
- **Canonical owner**;
- **Required change**;
- **Acceptance evidence**;
- **External/admin/runtime gate**;
- **Closure rule**.

Closing an issue requires its written acceptance condition to be satisfied, or a durable reason such as superseded/duplicate/not-planned.

## Documentation synchronization rules

When source ownership, contract, policy, workflow, evidence class, credential purpose, route structure or test organization changes:

1. update the canonical owner document in the same change set when practical;
2. update the AI navigation map if the canonical path changed;
3. update the current source-of-truth record if current state changed;
4. update the family sync snapshot when the audit state changes;
5. update affected issue/PR records;
6. remove or mark superseded records that now contradict current state;
7. retain historical material only when it preserves useful provenance.

Do not create duplicate policy documents merely to describe a new conversation. Dated audit snapshots are allowed when they are explicitly historical or are the single current reconciliation record for a defined audit date.

## Uniform test/coverage rules

Coverage must be feature-owned. Generic aggregation suites must not become substitute ownership boundaries.

A coverage claim must identify:

- scope of code covered;
- statement/branch requirement;
- focused suites;
- current execution evidence;
- any excluded runtime/platform boundary.

A configured 100% gate is not evidence of a 100% executed result until CI actually runs and passes it.

Requirement coverage and execution coverage are separate claims: a requirement may be fully classified while its implementation or runtime certification remains `BLOCKED`, `DEFERRED`, or `EXTERNAL`.

## Uniform runtime/prod truth rules

The following are separate evidence classes and must never be conflated:

`source` → `tests` → `GitHub Actions` → `deployment attempt` → `runtime smoke` → `production certification`

Cloudflare, B2, private Operations runtime and GitHub administrative state must only be called current/verified from their appropriate operational evidence path.

## Uniform naming rules

Use the exact canonical names for cross-repository concepts:

- `Foundation` / `foundation`;
- `Operations` / `operations`;
- `OPERATIONS_READ_TOKEN`;
- `BACKUP_GITHUB_TOKEN`;
- `B2_KEY_ID`;
- `B2_APPLICATION_KEY`;
- `B2_BUCKET`;
- `AI Analysis Map`;
- `Current Source of Truth`;
- `Family Documentation Index`;
- `Family Sync State`.

Do not introduce aliases for the same authority unless a compatibility contract requires one.

## AI maintenance rule

AI agents should start from the current source-of-truth and navigation maps, then open only the canonical implementation and focused tests required for the requested change. Historical plans are context, not authority.

Every material AI-generated change must remain understandable from repository source, tests and linked documentation without the original conversation.

## Synchronization completion condition

A family synchronization pass is complete only when:

- repository roles agree;
- current main SHAs are recorded as audit observations in the sync state;
- canonical owners and paths agree with source;
- policies/rules agree with implementation;
- tests describe the same contracts as the source;
- PR/issue state matches the actual GitHub state;
- stale or contradictory records are corrected or explicitly marked historical;
- unresolved gates are explicit;
- no claim exceeds its evidence level.

## Machine-enforced hygiene and format coordination

Repository formatting is governed by the identical machine contract in `docs/REPOSITORY_HYGIENE_FORMAT_CONTRACT.json` in both repositories.

The strict change gate is implemented by `tools/repository_hygiene.py` and `tools/code_documentation_sync.py`. Foundation also runs a read-only family coordinator to compare the shared contract/configuration bytes against Operations `main`.

This machine layer is subordinate to this document's authority/evidence hierarchy: it detects structural drift, formatting divergence and missing documentation deltas, but it does not convert source or CI results into runtime/production certification.

Formatting policy is deliberately ratcheted. Existing historical debt is reported without a repository-wide mass rewrite; newly changed files must satisfy the strict gate.

## Release-publication boundary — 2026-10-02

Foundation feed-recovery workflows are artifact-only. Feed workflows do not receive repository write permission; the separate governance workflow has only the narrow permission required to remove the specifically prohibited `wc-google-feed-latest` release/tag if recreated.


## 2026-10-02 Migration Factory CrossFire

The six-lane Migration Factory CrossFire workflow is an unprivileged read-only CI capability. It inventories Python across Foundation and an immutable Operations revision, produces independent runtime/dependency/tooling/test/language/retirement observations, and aggregates them without changing production authority. Migration promotion still requires the existing evidence and authority-transfer gates.

## 2026-10-02 live microscope reconciliation

The family sync ledger was refreshed from live GitHub state on 2026-10-02. Foundation main is `1195d4a9ccdb51688bf9e1086b9cdb7dd99512c0` and Operations main is `10dc9eff134609494ebb034df824616bbbcc7c97`. The microscope cleanup checkpoint records 2,931 initial branches, 2,564 current branches, and 367 refs retired by the fail-closed retirement workflows. Remaining refs are not assumed safe for deletion; protected, active-PR, release/tag, live-reference, young, and diverged branches remain governed by the retirement rules.


## 2026-10-02 continuous Migration Factory

The Migration Factory CrossFire is a trusted-main automation surface. It may read the private Operations repository only through the purpose-scoped read-only GitHub App token; pull-request and other untrusted execution remains excluded. Trusted pushes resolve a single immutable Operations SHA before the six independent lanes start, preserving the CrossFire snapshot invariant.


## Live reconciliation 2026-10-02T12:00:31.000Z

Current live GitHub heads: Foundation `43ccf7b4379863fa3a8112194d1b3c6b68181378`, Operations `f364a39d79ce30e8f1b63b67c623c41a898af320`. Current branch counts are Foundation 1319, Operations 991, total 2310; 621 refs have been retired from the initial 2,931-ref microscope baseline. Open pull requests are 0 in both repositories. The Migration Factory remains Foundation-owned; Operations remains free of competing hosted GitHub Actions authority.
