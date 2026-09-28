# AI Agent Execution Policy

**Status:** current and canonical.  
**Scope:** AI-assisted engineering across the Foundation/Operations family.

## 1. Authority and boundaries

- GitHub `main`, current Issues/PRs/CI, and fresh execution evidence outrank dated documents and chat history.
- Cloudflare live API/runtime evidence is authoritative for deployed Workers, D1, bindings, schedules, secrets and production state.
- Foundation owns public-safe contracts, deterministic public core, public API/frontend, GitHub Actions and deployment orchestration.
- Operations owns protected runtime policy, resource governance, acquisition/execution, provider state, chatbot orchestration, evaluation, promotion/rollback and private runtime evidence.
- Never copy private policy/runtime authority into Foundation or create a second owner for the same behavior.
- GitHub and Cloudflare may both be consulted during diagnosis when the connectors are available, but operational mutations remain bounded by the owning control-plane boundary. A GitHub-side document does not certify Cloudflare runtime state.

## 2. Work cycle

Use:
`diagnose -> parallel independent checks -> cluster root causes -> minimal repair -> focused verification -> cross-surface reconciliation -> checkpoint -> next cycle`.

Keep each cycle small and resumable. Prefer exact files, refs, run IDs, artifacts and receipts over large logs or repeated chat reconstruction.

## 3. Parallel / cross-fire strategy

Use 3–4 non-overlapping read-only lanes; expand only when work is genuinely independent.

Typical lenses:
- repository/static contracts and configuration;
- CI/workflow/control-plane behavior;
- runtime/evidence or current technical documentation;
- issue/PR/acceptance and documentation hygiene.

Cross-fire means independent validation, not duplicate implementation. Shared files, branches, deployment authority and merges are serialized.

## 4. Issue classification

Before mutation classify each issue:
`FIX_NOW | INTEGRATE | VERIFY_REPO | RUNTIME_GATE | EXTERNAL_BLOCKED | DUPLICATE | SUPERSEDED | ROADMAP`.

Fix the authority-defining defect before dependent symptoms. Runtime/external gates are not invitations for speculative code.

## 5. Mutation integrity

Before every write:
- refresh current `main`/base;
- verify exact blob SHA;
- inspect active PR/file ownership;
- ensure source content is real, not a retrieval placeholder.

After every write:
- re-read the changed file;
- inspect the diff/PR;
- run the narrowest relevant validation.

Use fresh current-main branches when a branch is stale or conflicted. Never bypass required checks or branch protection.

## 6. Evidence ladder

`R0/L0 hypothesis -> R1/L1 contract/source -> R2/L2 tests/integration -> R3/L3 protected runtime -> R4/L4 production`.

A lower tier can justify the next test but cannot satisfy a higher-tier acceptance gate. A merged PR is not an R3/R4 receipt.

## 7. Runtime invariants

For difficult paths model:
`input -> auth/trust -> route -> budget/deadline -> provider/tool/source -> side effects -> terminal state -> recovery -> telemetry -> evidence`.

Child work inherits parent identity, deadline and remaining budget. Never reset consumed resources, extend deadlines, self-authorize tools, self-promote providers or duplicate durable side effects without the canonical idempotency identity.

Required failures remain distinct:
`invalid | policy-blocked | transient | capacity | stale | partial | cancelled | timeout | error | blocked | unknown`.

Retry/replay/recovery are bounded and fail closed where authority is required.

## 8. GitHub / Cloudflare separation

For connector-separated operational work:
- GitHub chat handles repository source, tests, Issues/PRs, workflows and documentation.
- Cloudflare chat handles Worker/D1/configuration/deployment/runtime verification.
- Shared state is carried through canonical source-of-truth files and exact receipts, not conversational assumptions.

When both connectors are available for diagnosis, reconcile both before making a cross-system claim.

## 9. PR / issue discipline

Every PR should identify issue(s), scope/non-scope, canonical owner, validation, remaining runtime/external evidence and closure status.

Use `Closes #N` only when acceptance is actually satisfied. Group related issues only when canonical authority, file surface and acceptance dependency are shared.

## 10. Documentation / knowledge hygiene

One current fact has one canonical owner.  
Dated plans, handoffs, audits and snapshots are historical unless explicitly marked current.  
Preserve unique evidence and provenance. Remove pointer-only duplicates and repeated policy prose after dependency checks.  
Use `docs/KNOWLEDGE_LIFECYCLE_STANDARD.md` for durable ideas, decisions, experiments and removals.

Stable active filenames should be descriptive and date-free. New historical collections belong under `docs/history/`; existing legacy history paths may remain for compatibility.

## 11. Migration / polyglot

Language selection is evidence-driven. Python remains protected semantic/policy/provenance/replay/resource authority until formal promotion. Candidate implementations must pass the canonical contract, differential, adversarial, performance/resource, shadow, canary and rollback gates.

Do not create a language-specific authority merely to improve throughput.

## 12. Session continuity

When context/tool volume becomes large or responsiveness degrades, persist a compact checkpoint in the canonical repository records and continue from fresh state. Do not infer execution success/failure from the UI alone.

## 13. Completion rule

The queue is complete only when remaining items are explicit runtime/external/admin gates, duplicates/superseded items or deferred roadmap work, with canonical owner and missing evidence recorded.
