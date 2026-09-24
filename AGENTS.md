## 2026-09-24 CURRENT AUTHORITY RECONCILIATION

Refresh live GitHub state before mutation. The current main heads immediately before this documentation-only update were:
- Foundation main: 550da96babb5eb2c40b7d18a52774cfc23e03d2f
- Operations main: d0f59b6376fde7a75ca4ea0b789889650684ffcb
- Production Operations pin: 1a12b98981f52de207fa8626cf2e1f5ad06659be
- Nightly research/migration pin: 41db817dee6aa7d369ea9a07dd072b58ece1695a

Current live queue: Foundation #58/#157; Operations #145/#340/#385/#597/#603/#699; 8 open issues and 0 open PRs at verification.

Runtime/evidence:
- Production release #501 succeeded with Foundation 825d301d... and Operations 1a12b989...; Cloudflare public/private provenance was verified against those pins.
- Nightly #893 is provider-gated before LLM execution because the three research-provider configuration values are absent.
- Extractor #362 passed the strict evidence-quality gate but produced 4 ok / 32 empty / 4 blocked receipts.
- Deep scan #365 passed with 8 active issues plus historical #197.
- Smoke #72 remains red on the diagnostic operation mismatch: infrastructure_verify versus infrastructure_verify_public_test.
- Centralized Operations validation #24 remains red with broad test-suite contract mismatches.

This header is current guidance. Older authority reconciliations below are historical. The documentation update itself may advance main; that does not change runtime implementation or deployment authority.

---

## 2026-09-23 CURRENT AUTHORITY RECONCILIATION

**Live main heads verified:**
- Foundation main: `121ff5017c6b11ebc103dbbd26bdffe639fcc8cb`
- Operations main: `b47aa056f50d27df9b5f552495a6cd862ae8a697`

**Runtime/deployment provenance actually observed:**
- Public Worker: `c465ed8cff860cf0f1a1d6de6655aaf9594f02d2`
- Private production Worker: `bfcfaf5941824559cc253ecb2fd7d517cb1f1d7f`
- Nightly research pin: `3a7e350ddd5648caf93f58651323425186544f66`

**Current queue:** Foundation #58/#157; Operations #145/#197/#340/#352/#385/#597/#603/#699/#711.
- No open implementation PRs.
- No open documentation PRs after the completed synchronization merges.

**Current evidence:**
- Latest completed nightly research #861 is blocked before provider execution; the newer scheduled run #862 is in progress.
- Latest completed extractor benchmark #330 failed its gate and used stale Operations #830 (`246e563...`); corrected benchmark run #333 has been queued from the fixed main branch.
- Coverage matrix #301 was cancelled when the follow-up commit arrived; corrected coverage run #302 is queued from the fixed main branch.
- Current live Worker probe on deployed Foundation `c465ed8...` has passed; new main-push runtime checks are queued against the newer repository head.
- Full L4 certification remains evidence-gated.

**Deployment authority:** Foundation GitHub Actions is the sole CI/CD and production deployment owner. Operations must remain without GitHub-hosted workflows. Do not re-enable Cloudflare Workers Builds or Deploy Hooks.

---
---
---

## 2026-09-22 FINAL LIVE REF RECONCILIATION

**Live branch heads queried from GitHub:**
- Foundation `main`: `f9490f36d7ffd877157f26d674b3bfc27388f67e`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`

**Verified runtime implementation pins:**
- Foundation: `e5b26061861e570396b73993a3c8733496cb1956`
- Operations: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`

The live heads may contain documentation and migration-candidate commits after the verified runtime pins. Acceptance workflows intentionally remain pinned to the verified immutable revisions until promotion evidence passes.

## 2026-09-22 LIVE GITHUB REF RECONCILIATION

**Latest live branch heads queried from GitHub:**
- Foundation `main`: `86a7d02b86a78102bf412cdce050c1f9e6c95bd5`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`

**Verified runtime implementation pins:**
- Foundation: `e5b26061861e570396b73993a3c8733496cb1956`
- Operations: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`

**Important:** Operations `main` now contains merged migration-candidate/test fixes after the verified runtime pin. Those candidate revisions are not production/runtime certification and must not silently replace the immutable runtime pin in acceptance workflows. The coverage/runtime guard must fail closed when non-documentation drift exists after the approved pin.

## 2026-09-22 LIVE GITHUB REF RECONCILIATION

**Live branch heads observed immediately before this synchronization:**
- Foundation `main`: `baad1daf07ea7d0307077631c4afb3a27fa31e78`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`

**Last verified implementation revisions:**
- Foundation: `e5b26061861e570396b73993a3c8733496cb1956`
- Operations: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`

Documentation-only handoff commits may advance `main` without changing the verified runtime implementation revision. Always refresh live refs before mutation and keep live branch heads separate from runtime-certification pins.

## 2026-09-22 CURRENT RECONCILIATION

**Live-head rule:** query the current GitHub `main` refs at chat startup. Documentation-only commits may advance `main` and must not be mistaken for a new runtime implementation revision.

- Last verified Foundation implementation revision: `e5b26061861e570396b73993a3c8733496cb1956`
- Last verified Operations implementation revision: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`
- Canonical nightly research workflow: `.github/workflows/nightly-multi-agent-research-v2.yml`
- Nightly `OPERATIONS_RESEARCH_REF`: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`
- Final implementation repair waves are merged through Foundation #960 and Operations #753.
- Foundation #157 remains the canonical 24-program nightly acceptance gate.
- Remaining open issues are runtime/provider/Cloudflare/migration evidence gates; do not infer closure from source inspection, unit tests, or dry-runs.
- GitHub Actions remains the sole CI/CD/production deployment authority; Operations must remain free of GitHub Actions, and Workers Builds/Deploy Hooks must not be re-enabled.

## 2026-09-21 CURRENT RECONCILIATION

Refresh live GitHub state before every mutation. Current canonical heads:
- Foundation `main`: `b2752d6a63aaf646743cc8173fa83b4271b02160`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`
- Foundation immutable Operations pin: `0fa576c10fee30221150110865b11c0132de4575`

Merged repair/documentation waves: Foundation #945/#949/#951/#952/#954/#955/#956; Operations #745-#749. Foundation #953 is closed. Current remaining acceptance queue: Foundation #58/#157/#452; Operations #119/#132/#145/#197/#340/#352/#385/#597/#603/#699/#711.

Do not treat a merged PR, repository test, or GitHub Actions success as Cloudflare/runtime certification. Keep runtime/admin/provider/scheduler evidence gates open until their actual receipts exist. GitHub Actions remains the sole CI/CD/deployment authority; Operations must remain free of GitHub Actions, and Workers Builds/Deploy Hooks must not be re-enabled.

## 2026-09-20 PRODUCTION PIN PROMOTION OVERRIDE

- Foundation main at promotion preparation: 62ff421534034d70a110f1dba32f71975c7e5a2d.
- Operations main: 277ccb9ee33221038c7ca5647f19e27a00d84ea3.
- Canonical production Operations revision for the next release: dd30834aec8f1263d9b35142b1bd16b4ba95f1ca (Operations #610 merge; fixes the previously observed Worker package omission of generated foundation_core).
- Nightly research remains separately pinned to its research revision; production promotion and nightly research are distinct authorities.
- Do not treat this pin promotion as a live runtime certificate until the canonical production workflow succeeds against the exact Foundation revision and emits a fresh Cloudflare provenance receipt.

## 2026-09-20 LIVE MIGRATION RECONCILIATION — CURRENT OVERRIDE

Refresh live GitHub refs before every mutation.

### Current repository heads
- Foundation main: 12cf25f6a5688522f945e48efed915a5d5902703.
- Operations main: b5982fd9c3203d360584f955b8adfcf85cfd1315.

### Active migration work
- Foundation #835 (TypeScript frontend controls) is merged.
- Foundation #836 is the documentation reconciliation PR.
- Operations #606, #607, #608, #609, #610 and #611 are merged.
- Operations #610 fixed the production Worker packaging defect where generated foundation_core was excluded from setuptools package discovery.
- Operations #603 remains the canonical AI-model/tooling portability tracker.
- Current main is not production-certified until a canonical production release proves the current revisions.

### Architecture invariant
Python remains protected policy/governance/persistence/provenance/replay/rollback authority. TypeScript/Rust/Go migration work remains evidence-gated. Operations remains free of GitHub Actions; Foundation remains the sole CI/CD/deployment owner.

# AI / Maintainer Engineering Guidance

Read `REPOSITORY_MAP.json`, `docs/FAMILY_CONTRACT.json`, and `docs/FAMILY_ARCHITECTURE.md` before architecture or cross-repository changes.

## Ownership

Foundation owns public-safe contracts, deterministic research/evidence primitives, planning, the public Worker/API boundary, canonical public CI, and production deployment/backup ownership.

Operations owns protected policy, resource governance, private acquisition/execution, provider/runtime selection, evaluation, promotion, rollback, recovery, private runtime orchestration, and chatbot control.

Dependency direction is:

`foundation public contract/core -> operations consumer/control plane`

Never import Operations source, private credentials, private runtime state, or protected implementation into Foundation.


## Private-runtime automation ingress

Private Operations and approved external runtime callers must use the canonical Foundation workflow bridge for GitHub Actions automation.

`private runtime -> Foundation GitHub App installation token (Actions: write) -> .github/workflows/foundation-canonical-workflow-bridge-v3.yml -> allowlisted Foundation workflow`

The runtime caller must not dispatch arbitrary target workflows directly, create a second bridge, add a private Operations workflow, or introduce another deployment authority. The bridge owns target allowlisting and production confirmation; Operations remains the private source/runtime/policy authority.

## GitHub Actions ownership boundary

All GitHub Actions automation for the active family is owned and executed from the public `foundation` repository.

The private `operations` repository is **not** an Actions execution surface. It must not contain `.github/workflows` or depend on private-repository workflow runs.

When automation needs private Operations source, metadata, or configuration, the Foundation workflow must authenticate through the approved Foundation GitHub App, read the minimum required private content, and execute the action from Foundation.

This boundary is separate from Cloudflare runtime access: Foundation -> Operations Worker uses the Cloudflare service binding and the canonical `AUTH_TOKEN` boundary.

The cross-repository automation guard in `.github/workflows/cross-repository-contract-drift.yml` must fail closed if private Operations gains a workflow file.


## Canonical-owner rule

Before writing code, search both active repositories and active PRs for an existing implementation. Identify the canonical owner first.

Extend the canonical owner. Do not create a second implementation of the same behavior, policy, registry, state model, result semantics, resource ledger, evaluator, promotion authority, trust boundary, or deployment authority.

Compatibility facades are allowed only to preserve supported legacy imports; they must not contain competing business logic.

## Issue queue algorithm

Treat GitHub as the live queue.

For each candidate issue:

1. Read the complete body, labels, comments/status, and acceptance criteria.
2. Search open PRs, recent commits, and the current tree.
3. Classify the work as implementation, deterministic validation, runtime/production acceptance, external dependency, duplicate/superseded, research, or roadmap.
4. Do not add code to runtime-only or external-only issues. Record the missing evidence/dependency and move on.
5. Prefer the oldest actionable issue with a clear canonical owner and no competing file surface.
6. Prefer the smallest coherent slice that satisfies concrete acceptance criteria.
7. Update tests plus issue/PR metadata so the next agent can resume without chat history.

A blocked PR is not a queue stop condition.

## Parallelization and collision control

Parallelize read-only discovery aggressively:

- batch issue/PR/tree/file reads;
- keep roughly 3–4 independent candidate lanes available;
- re-check active PRs and exact touched files immediately before a write.

Serialize repository mutations:

- branch creation;
- file writes;
- issue/label/status changes;
- PR creation/closure;
- merges.

Do not race another agent on the same issue, branch, or file surface.

## Implementation

Start new work from the latest `main`.

Contracts should be versioned when externally consumed, deterministic where required, bounded for size/depth/fan-out/retries/resources, explicit about unknown/partial/stale/blocked states, and provenance-preserving.

Security and privacy boundaries must fail closed. Do not silently truncate, silently pass, or turn missing evidence into success.

Add owner-level regression tests plus focused boundary/adversarial tests. Never create a second evaluator, verifier, publication authority, identity authority, or resource ledger just to satisfy a local test.

## PR discipline

Every implementation PR should state:

- exact issue(s);
- in-scope and out-of-scope behavior;
- canonical owner;
- tests/validation;
- remaining runtime/external evidence;
- whether the PR is a complete closure candidate or one implementation slice.

Use `Closes #N` only when the repository-level closure criteria for that issue are genuinely satisfied.

Related issues may be batched only when they share the same owner/file surface. Do not bundle unrelated work to reduce PR count.

## Merge discipline

Merge only after required checks and branch-protection rules are satisfied.

Never bypass required checks, authentication, deployment ownership, or runtime evidence gates.

If checks are pending or failing, work on another safe lane instead of waiting.

After a merge, verify current `main` before starting dependent work.

## Duplicate handling

Search before creating a PR.

When an active PR already owns the same implementation, do not create a competitor. Close the duplicate PR with an explicit canonical-PR reference.

Do not close the underlying issue merely because a PR exists; close it only when its acceptance criteria are actually satisfied.

## Runtime and production evidence

Source inspection and repository tests do not substitute for approved runtime/L4 evidence.

Keep runtime-only issues open until required evidence exists. Never fabricate deployments, secrets, bindings, production responses, or acceptance receipts.

Operations repository visibility is not the security boundary; the Operations control plane remains protected. Never expose protected topology, credentials, evaluation holdouts, private runtime state, or protected implementation details through Foundation.

## Cross-repository order

For family changes:

1. Foundation contract/core.
2. Operations integration/control plane.
3. Runtime/production acceptance in the owning environment.

Do not copy implementation between repositories. Share the minimum stable versioned contract.

## Documentation

When ownership, workflow, policy, or agent methodology changes, update the canonical documentation in the same change set.

Non-trivial modules must make responsibility, non-responsibilities, inputs, outputs, invariants, failure semantics, side effects, canonical authority, and tests discoverable without chat history.

## Hybrid runtime and language policy

Read `docs/ARCHITECTURE_LANGUAGE_PROVIDER_MAP_2026-09-20.md` and `docs/LANGUAGE_MIGRATION_RUNBOOK_2026-09-20.md` before introducing or migrating runtime languages.

Rules:

- Do not rewrite Python globally.
- TypeScript is the preferred first migration for the Cloudflare edge Worker because it maps directly to the native V8/web-standard Worker runtime.
- Rust is a candidate for measured CPU/memory hot paths such as deterministic parsing/extraction.
- Go is a candidate only for a separately justified long-lived high-concurrency service.
- PHP, Java/Kotlin, C/C++ are not default project runtimes; introduce them only when a concrete workload and benchmark prove a need.
- Search/retrieval providers are capabilities behind a common eligibility/quota/billing/health contract. Never hard-code provider names into business logic.
- Every migration must have a frozen baseline, shadow comparison, failure-injection coverage, security/authorization parity, and rollback path.
- Never claim performance improvement from a language change without benchmark evidence from the actual project workload.

## Completion loop

`parallel triage -> non-overlapping slice -> latest-main branch -> smallest safe change -> focused tests -> PR -> merge when green -> update issue -> rescan queue -> next slice`

Continue until the remaining queue is entirely runtime/external/blocked, duplicate/superseded, or otherwise lacks a repository-actionable fix.


## Fast queue operating profile

For high-volume maintenance, use a two-stage scheduler: parallel read-only discovery, then a serialized mutation queue. Keep 3-4 non-overlapping candidate lanes available, but never let parallel lanes share an issue, branch, or file surface. Re-check active PRs and exact paths immediately before each write.

Track every candidate as one of: `actionable`, `in_progress`, `blocked_checks`, `runtime_only`, `external_blocked`, `duplicate`, `superseded`, or `complete`. A blocked check lane does not stop other actionable lanes.

Prefer exact-path reads and bounded searches over repeated full-tree scans. After a merge or PR closure, refresh only the affected queue slices first, then perform a broader rescan.

GitHub API operations must respect rate limits: avoid excessive concurrent requests, serialize mutations, space large mutation bursts, and back off on secondary-rate-limit responses. Use stable, narrow queries when polling.

## Queue execution protocol v2

Use this operating contract for high-volume issue reduction.

### Wave scheduler

1. **Discovery wave:** keep 3–4 independent read-only lanes classifying issues, PRs, exact file surfaces, and acceptance evidence.
2. **Mutation wave:** serialize branch creation, file writes, PRs, issue updates, and merges.
3. **Acceptance wave:** while checks run, continue independent discovery and implementation instead of waiting.
4. **Rebase wave:** after a relevant merge changes `main`, refresh dependent branches before merge.
5. **Rescan wave:** after every 3–5 meaningful mutations, refresh the live issue/PR queue and discard stale plans.

Never treat a captured issue list as authoritative after another mutation changes repository state.

### Lane packet

Before mutation, each lane records: issue and exact acceptance target; queue disposition; canonical owner/file surface; competing PR/branch; focused tests; and remaining runtime/external evidence. A lane with overlapping authority or files must yield before writing.

### Fresh-main rule

Start from current `main`. If `main` advances before merge, update the work branch through a normal non-force-push flow and rerun required checks. Never make an old PR mergeable by bypassing protection or altering status metadata.

### Acceptance ladder

Treat evidence as:

`implemented -> tested -> CI_green -> integration_verified -> runtime_verified -> production_certified`

Close an issue only at the highest rung explicitly required by its acceptance criteria. Repository tests do not become runtime or production evidence by wording.

### Failure routing

When a lane fails, narrow the failure to the exact contract, file, test, branch-protection rule, or external dependency. Fix the root cause or record a precise blocker, then switch to another independent lane. Never weaken a gate to manufacture progress.

### Batch discipline

Batch issues only when they share the same canonical authority and touched file surface. The PR body must enumerate every included issue and explicitly mark any issue that remains only partially satisfied.

### Queue truth

Issue count is a metric, not the goal. Do not close an issue merely because code, a PR, or green tests exist. Preserve runtime/admin/external gates until their required evidence exists.

### Maintainer handoff

Every substantive issue update should leave the canonical files, completed acceptance items, remaining items, current PR/commit, and blocker/evidence state discoverable without chat history.
## Hard-case protocol v3 — runtime, control-plane and external-evidence issues

The final queue is not homogeneous. Treat every issue as an acceptance graph rather than a code task.

### Acceptance graph

For every hard issue, explicitly separate:
- R0 repository contract — source, schemas, tests and invariants;
- R1 CI evidence — required checks and reproducible fixtures;
- R2 integration evidence — real repository/service boundary;
- R3 control-plane evidence — GitHub/Cloudflare/admin admission, permissions, bindings or deployment workflow;
- R4 production/runtime evidence — approved live execution, restart/recovery, real providers/sources and production state.

Never promote evidence between levels.

### Hard-gate routing

When an issue has R3/R4 acceptance:
1. implement every missing R0/R1 contract that can be proven locally;
2. record the exact remaining R3/R4 observation needed;
3. search for a supported connector/API path to obtain that evidence;
4. if the required control plane is unavailable, leave the issue open with a machine-checkable evidence recipe;
5. continue another lane immediately.

Do not repeatedly rewrite repository code when the missing acceptance is outside the repository.

### Control-plane diagnostic discipline

For zero-job, rejected-trigger, missing-binding, permissions, merge-queue, deployment or secret failures:
- distinguish trigger admission, graph admission, job creation, execution, artifact/downstream reachability and diagnostic availability;
- never infer a root cause from “zero jobs” alone;
- never change permissions, timeouts, triggers or deployment authority without causal evidence;
- preserve a known-good probe workflow as the control experiment;
- compare the failing workflow against the known-good control and record the exact difference.

### Runtime certification discipline

A runtime result must identify:
- environment;
- endpoint/workflow;
- exact code/config revision;
- execution/request identity;
- start/end time;
- relevant policy/resource snapshot;
- result state;
- provenance/digests;
- observed side effects;
- failure or missing-evidence reason.

Never close a runtime issue from source code plus CI alone.

### External-source evidence

For real-source/oracle/browser/network issues:
- use bounded representative fixtures before live execution;
- keep source identity, timestamp, contract version and input/output digests;
- distinguish unavailable source, blocked source, stale source, partial extraction and true negative;
- never turn network silence or tool failure into “no data”;
- never place holdout/oracle data into public CI merely to make a check green.

### Cross-repository hard gate

Foundation may define public-safe contracts and read approved metadata. Operations retains protected runtime/policy/resource/evaluation authority. For a cross-repository change, verify both contract compatibility and canonical authority ownership.

A private Operations dependency must use the existing approved credential/deployment path. Do not create a new token, mirror private implementation into Foundation, or bypass the boundary for convenience.

### Production/deployment gate

Treat deployment as a separate authority chain:
PR -> required checks -> canonical Foundation release workflow -> pinned Operations revision -> Cloudflare deployment -> live endpoint verification

A merged PR is not a deployment. A successful deployment workflow is not necessarily runtime certification. Never claim a live revision until endpoint/version/provenance evidence is actually observed.

### Hard-issue decomposition

Before starting a difficult issue, create a short checklist of:
contract -> implementation -> focused tests -> CI -> integration -> control-plane -> runtime -> production.

Mark every rung as pass, missing, or not applicable. This prevents solving the same repository layer repeatedly while the actual blocker lives elsewhere.

### Safe closure rule

Close only when the issue's own acceptance graph has no unproven required rung. If only optional or future enhancements remain, state that explicitly and close. If a required rung is externally blocked, keep it open.

### Terminality test

A queue is finished only when every remaining issue is one of:
- externally blocked with exact missing evidence documented;
- duplicate/superseded with canonical owner identified;
- roadmap/future work whose acceptance is explicitly deferred;
- awaiting an unavailable platform/admin operation.

Do not label an issue complete merely because no further code change is obvious.

## Fast Execution Protocol v4 — final-queue scheduler

This section is authoritative for high-volume autonomous maintenance when the remaining queue contains many partially implemented or runtime-gated issues.

### 1. Classify before touching code

Every open issue must receive exactly one primary disposition before mutation:

| Disposition | Meaning | Action |
|---|---|---|
| FIX_NOW | concrete repository defect is present | implement/test/PR |
| INTEGRATE | contract exists but is not wired to its canonical path | wire existing authority, test/PR |
| VERIFY_REPO | implementation appears complete but deterministic acceptance is missing | add smallest missing test/gate/evidence contract |
| RUNTIME_GATE | repository work is complete; approved runtime/control-plane evidence remains | document probe; do not add speculative code |
| EXTERNAL_BLOCKED | GitHub/Cloudflare/admin/secret/provider dependency is unavailable | record dependency and switch lanes |
| DUPLICATE | another issue/PR is canonical | reference canonical owner; do not duplicate |
| SUPERSEDED | newer architecture/PR replaces it | record replacement and close when justified |
| ROADMAP | future capability, not current acceptance debt | defer explicitly |

Never use RUNTIME_GATE to avoid a concrete repository gap. Never use FIX_NOW when the only missing fact is live evidence.

### 2. Proof-first issue decomposition

For every non-trivial issue, identify the first unproven rung:

contract -> owner -> implementation -> focused test -> CI -> integration -> control-plane -> runtime -> production

Only work on the first missing required rung and the minimum dependencies needed to reach it.

### 3. Four execution lanes

Maintain four logical lanes when the queue allows it:

- Lane A — core implementation: deterministic repository fixes.
- Lane B — integration: wire existing contracts into real call paths.
- Lane C — validation: tests, benchmark gates, fixtures, CI contracts, acceptance evidence.
- Lane D — queue hygiene: duplicate/superseded consolidation, stale PR/branch triage, issue synchronization.

Each lane owns one issue at a time and declares its touched file/authority surface before mutation. When a lane blocks, work-steal the next unclaimed actionable issue. Never idle waiting for another lane.

### 4. Serialized mutation queue

Read-only work is parallel. Repository mutations are serialized:

branch -> smallest coherent change -> focused tests -> PR -> required checks -> merge -> issue receipt -> queue refresh

Do not race another lane on the same issue, branch, canonical authority, or file surface.

### 5. Candidate ranking

Prefer, in order: dependency-unblocking work; shared canonical-authority fixes; CI/control-plane blockers; security/trust boundaries; integration of already-merged contracts; deterministic validation gates; queue hygiene; roadmap.

Within the same class, prefer the oldest non-conflicting issue. Never prioritize by issue number alone.

### 6. Shared-authority rule

Before editing a hard issue, search both active repositories and current PRs for the canonical authority.

Single-owner concepts include ResourceLedger/DurableResourceLedger, execution identity/deadline, provider eligibility/health/fallback, admission/backpressure, tool authorization/idempotency, memory/feedback lifecycle, evidence verification/EvaluationReceipt, promotion/rollback, and production deployment.

If a patch creates a competing owner, reject the approach and extend the existing authority.

### 7. Hard-issue fast path

1. Read issue body and latest status.
2. Locate canonical module.
3. Inspect newest related PR/merge.
4. Compare acceptance criteria with actual code/tests.
5. Implement only the missing repository-side slice.
6. Run focused tests.
7. Put exact remaining R2/R3/R4 evidence in PR/issue.
8. Merge when green.
9. Immediately rescan the queue.

Do not reopen solved design work because runtime certification is missing.

### 8. Control-plane and zero-job diagnosis

For GitHub Actions, merge queue, deployment, secret, permissions, or binding failures, classify the fault as trigger -> workflow graph -> job creation -> execution -> artifact/downstream -> runtime.

Zero jobs is an observation, not a root cause. Use a known-good control workflow where possible. Change only the earliest causally supported layer. Never weaken permissions/protection or create a second deployment owner.

### 9. Cross-repository execution rule

Active family = Foundation + Operations.

Foundation is the public contract/core/deployment authority. Operations is the protected runtime/policy/resource/evaluation authority.

Private Operations access must use the existing approved GitHub App/deployment credential path. Never create personal-token dependencies, public mirrors of private runtime code, second secret authorities, or second production deployment paths.

The retired extractor/mapper repository is historical, not an active production authority.

### 10. Evidence transport rule

Never upgrade evidence strength by narration.

Unit tests prove local behavior. CI proves reproducible repository checks. Integration evidence proves a real service boundary. Control-plane evidence proves admission/configuration/bindings. Runtime evidence proves real execution. Production certification proves the approved deployed environment.

A runtime issue may be repository-complete while still open.

### 11. Evidence packet

Every hard-issue update should contain:

issue | disposition | canonical owner | current revision | completed rung | missing rung | test/check | PR | remaining evidence

Do not rely on conversation history.

### 12. Stale work elimination

Before opening/updating a PR, search for another active PR on the same issue/authority, compare its base SHA with current main, and inspect exact touched files.

After a relevant merge, dependent PRs become suspect until rechecked against current main. Close stale/superseded PRs rather than consuming more check/review bandwidth.

### 13. Merge-wave discipline

After each meaningful merge, refresh current main, refresh affected issues/PRs first, update lane packets, and start the next safe lane while unrelated checks run.

After 3–5 meaningful mutations, perform a broader queue rescan.

Never poll one PR repeatedly while independent work exists.

### 14. Testing strategy

Use the cheapest proving layer first:

pure contract test -> focused module test -> integration fixture -> targeted workflow -> approved runtime probe

Do not rerun the entire suite repeatedly during pure local iteration. Required repository checks remain mandatory before merge.

### 15. Closure rules

Close only when every required acceptance rung is proven.

Safe closure: deterministic implementation plus tests plus required CI; duplicate with canonical owner; superseded by an explicitly accepted replacement; obsolete/roadmap with documented disposition.

Unsafe closure: PR exists but evidence is missing; code is merged but runtime is required; a fixture simulates a real provider/control plane; a deployment is inferred from source/workflow text; or a failed gate is ignored because another gate is green.

### 16. Completion definition

Do not optimize for zero open issues mechanically.

The final queue is complete only when remaining issues are explicitly RUNTIME_GATE, EXTERNAL_BLOCKED, DUPLICATE, SUPERSEDED, or ROADMAP, and each has a canonical owner, exact missing evidence/dependency, current revision, and reproducible next probe/action.

Everything else is actionable queue debt.


## Cross-chat continuity override — 2026-09-19

Before any new mutation, read `docs/AI_AGENT_HANDOFF.md` and `docs/CURRENT_SOURCE_OF_TRUTH.md`. Live GitHub state and fresh runtime evidence override dated continuity text.

Current verified family state:
- Foundation main: `6a91fbd17143083882e9ac7ebfa52f0b06a344b2`
- Operations main: `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129` (production pin target; last verified production remains `307ed38fe4c7902220cb981556bf08702babbae0`)
- Latest canonical production receipt: run `35456292033` (#232), successful on Foundation `6a91fbd17143083882e9ac7ebfa52f0b06a344b2` with Cloudflare provenance last verified at `github:307ed38fe4c7902220cb981556bf08702babbae0`; re-certification target is `github:c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`.
- Current acceptance queue is the 13-issue set recorded in `docs/CURRENT_SOURCE_OF_TRUTH.md`.

Current queue policy:
- #27 is completed and closed after confirmed stale temporary/diagnostic/test branch cleanup; do not reopen merely for historical branch pruning.
- #157 requires a real 24-program nightly execution with retained artifacts; the current push-triggered nightly run still fails before job creation.
- #263 requires an empirical supported workflow-dispatch receipt proving exact target SHA and actual job creation.
- #452 requires real client cancellation/disconnect propagation and provider-error-after-partial-output evidence.
- Operations #119, #120, #132, #145, #155, #197, #340, #352 and #385 remain runtime/control-plane/external evidence gates unless a new repository-side defect is established.
- Operations must remain private and must not contain GitHub Actions workflows.
- Foundation remains the sole GitHub Actions and canonical production deployment owner.
- Do not enable Cloudflare Workers Builds or Deploy Hooks as a competing deployment authority.

Never close a required runtime/control-plane issue from source inspection or repository tests alone.


## Hybrid implementation policy

Prefer capability-based selection over one-language standardization. Use TypeScript for new asynchronous edge/search fan-out work, retain Python for current deterministic public primitives, and require measured evidence before introducing Rust/Wasm or Go. PHP is a legacy-integration option, not a performance-driven rewrite target. Provider choice belongs behind typed capability contracts and must not move protected policy or resource ownership into Foundation.


## AI model portability
Keep `AGENTS.md` as the concise execution map. The public-safe cross-agent contract is `docs/AI_PORTABLE_ENGINEERING_CONTRACT.md`. Do not encode business rules in a model-specific instruction file.


## Adaptive hybrid execution and ChatGPT session strategy

For high-volume migrations, use the shared four-lane execution model documented by Operations in `docs/ADAPTIVE_POLYGLOT_EXECUTION_POLICY_2026-09-20.md`.

Default when migration pressure is high: **3 migration lanes + 1 acceptance/blocker lane**. Rebalance dynamically for critical runtime/control-plane failures, collision pressure, duplicate work, or externally blocked migration.

Uniformity:
- canonical owner;
- exact revision;
- file-surface ownership;
- evidence ladder;
- rollback;
- security/policy/provenance gates.

Diversity:
- language;
- component surface;
- evidence mode;
- risk class.

Foundation owns CI/CD and deployment. Operations owns protected policy/runtime authority. Candidate compilation or static benchmarks never grant production authority.

For ChatGPT/multi-agent sessions:
1. refresh live GitHub state before every mutation;
2. batch discovery and independent evidence reads;
3. allocate lanes adaptively instead of permanently assigning issues to sessions;
4. serialize mutations per authority/file surface;
5. continue independent work while CI runs;
6. collapse repeated failures into one root-cause fix;
7. refresh affected queue slices after merges;
8. leave exact evidence/rung state in PR and issue metadata so another session can resume without chat history.


## Adaptive scan learning loop — 2026-09-21

Treat repository scanning itself as a maintained engineering method, not a one-off audit.

### Coverage contract
- Begin with a live recursive tree inventory for every active repository.
- Record blob count, language/file-type counts, binary exceptions, and a deterministic path index.
- Preserve 100% path/inventory coverage even when semantic inspection is selective.
- For large trees, partition by disjoint path ranges and assign different language paradigms as independent lenses.
- Include Python in every scan; Python is the current semantic authority and must never be accidentally excluded because the lens is non-Python.

### Lens diversity
Each wave should mix structural and operational paradigms: typed functional/state-machine, actor/concurrency, systems/ownership, dataflow, managed OO, and runtime/stream-oriented lenses. Reuse a language only when a prior finding needs confirmation.

### Evidence method
1. repository-wide search for invariant patterns and boundary symbols;
2. direct inspection of high-signal owner modules and consumers;
3. compare against existing contracts, tests and issue/PR history;
4. normalize findings into behavior/policy/security/resource/provenance/migration categories;
5. distinguish candidate observations from verified defects;
6. create or attach a regression issue only when a reproducible owner-level defect or explicit evidence gap exists.

### Learning extraction
After each wave, record reusable design rules, security/policy/resource invariants, migration candidates and explicit non-candidates, scan-method improvements, false-positive patterns to avoid, and documentation/AGENT changes needed to make the learning durable.

### Migration rule
No language promotion follows from stylistic similarity or benchmark enthusiasm. Use the gate: reference -> candidate -> contract -> differential -> adversarial/error taxonomy -> shadow -> canary -> rollback rehearsal -> authority.
Python remains policy, semantic, persistence, replay, provenance and rollback authority unless an explicit evidence-gated ownership transfer is documented.

### Queue rule
Convert findings into the smallest canonical issue/PR surface, tag the issue by type and evidence rung, and keep runtime/external gates open until the required evidence exists. Issue count is not completion; the acceptance graph is.