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
