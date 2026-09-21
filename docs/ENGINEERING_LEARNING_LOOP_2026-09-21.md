# Engineering Learning Loop — 2026-09-21

## Live family revision

- Foundation main: `24e20c19f02a820afb261f4c43915f46c87a6a9c`
- Operations main: `0f1420b2b7dba3270ff8de874ac2eb5e88995976`
- Active Foundation fix: PR #919 — ResearchRun lifecycle + worker pre-materialization bounds.
- Active Operations fix: PR #668 — deep immutability residue.
- Foundation production deployment ownership remains canonical; Operations remains free of GitHub Actions.

## Cross-paradigm scan method

Every large scan uses four distinct layers:

1. Inventory coverage — enumerate the current Git tree and classify every blob by language/type, explicitly recording exclusions.
2. Repository-wide semantic search — search for patterns that express the lens' failure mode across the whole repository, not only the assigned range.
3. Targeted semantic review — inspect the highest-signal owners, consumers, tests, contracts and workflow gates.
4. Evidence reconciliation — compare findings with open issues, PRs, recent commits, CI receipts and canonical documentation before creating work.

Coverage and semantic review are different claims. A scan may have 100% path inventory coverage without byte-for-byte semantic rereading of every file. Reports must state the exact coverage level.

Language/paradigm lanes must be non-overlapping at the inventory level, but their semantic searches intentionally remain repository-wide so a local lens can discover cross-cutting consequences.

## Findings-to-engineering conversion rules

A finding becomes repository work only after:

`finding -> canonical owner -> existing issue/PR search -> minimal contract-preserving change -> focused regression -> CI -> acceptance rung`

Prefer one canonical issue for one authority/file surface. Merge duplicate issue scope into the existing authority issue instead of creating parallel work.

Related issues stay separate when they have different acceptance rungs, owners or runtime evidence requirements.

## Cross-language principles now mandatory

- One versioned lifecycle/outcome algebra across execution, publication, streaming, recovery and benchmark receipts.
- Frozen dataclasses are not automatically deeply immutable; externally visible nested mappings/lists must be immutable snapshots.
- Configuration parsing must distinguish absent configuration from malformed/unsupported configuration and preserve bounded diagnostics.
- Stream limits must include aggregate output budget in addition to per-event/per-delta limits and event count.
- Input/output materialization budgets apply before unbounded JSON/text creation; hashes should stream over bounded encoder chunks.
- Runtime capability discovery must emit explicit capability receipts when fallback paths depend on import/runtime availability.
- Failure diagnosis must preserve independent blockers instead of collapsing them into one aggregate failure.
- Cancellation, partial, blocked, failed, cancelled, stale and unknown states remain distinct.
- Retry/fallback/recovery inherit the parent execution identity, deadline and remaining resource budget.
- Model/provider health can inform routing but cannot override eligibility, quota, security, evidence or resource authorities.
- No language migration creates a second policy, resource, persistence, replay, evaluator, publication or deployment authority.

## Nightly-research lessons

- `blocked_before_execution` is a first-class execution state, not a silent dry-run.
- Dry-run artifacts are coverage/matrix evidence only; they are never empirical research findings.
- A diagnosis artifact must retain every independent blocker (research preflight, migration review, artifact validation, final gate).
- Operations revision freshness must be checked before accepting nightly results because a stale pin can fail independently of current main.
- Project-improvement findings from LLMs remain candidate-only until deterministic acquisition/evidence qualification.

## Migration decision ladder

`reference -> candidate -> differential -> shadow -> canary -> authority`

A candidate is not promoted from compilation, unit tests or provisional score. Required evidence includes exact functional/error/security/policy/provenance/cancellation parity, realistic benchmark distributions, conversion/serialization overhead, rollback rehearsal and maintainability/tooling portability.

Python remains the protected policy/governance/persistence/provenance/replay/rollback authority. TypeScript is the preferred Cloudflare edge/runtime target; Rust is restricted to measured pure kernels; Go requires a separately justified service boundary.

## Queue and tagging standard

Every open issue must have:
- a type label (bug/security/enhancement/refactor/quality/architecture/maintenance),
- a domain/migration/track label where applicable,
- a `needs:runtime-evidence` label when repository work is complete but live acceptance remains,
- an explicit disposition: `FIX_NOW | INTEGRATE | VERIFY_REPO | RUNTIME_GATE | EXTERNAL_BLOCKED | DUPLICATE | SUPERSEDED | ROADMAP`.

Issue count is not the success metric. The terminal condition is that remaining issues are genuinely runtime/external gated, superseded/duplicate, or roadmap work with an identified canonical owner.

## Rescan trigger

After every 3–5 meaningful mutations, refresh:
- current main heads;
- open issues and active PRs;
- exact touched paths;
- acceptance/check state;
- source-of-truth documents.

Discard stale plans after any main-branch mutation.

## Canonical evidence ladder

`implemented -> tested -> CI_green -> integration_verified -> runtime_verified -> production_certified`

Do not close an issue at a higher rung than its acceptance requires. Do not use repository assertions as live-runtime proof.
