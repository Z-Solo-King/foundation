# Foundation agent execution map

## Read first
1. `REPOSITORY_MAP.json`
2. `docs/CURRENT_SOURCE_OF_TRUTH.md`
3. `docs/FAMILY_ARCHITECTURE.md`
4. `docs/FAMILY_DOCUMENTATION_INDEX.md`
5. `docs/AI_AGENT_EXECUTION_POLICY.md`
6. `docs/AI_SYSTEM_DIRECTORY.md`

Then load only the canonical surface needed for the task. Do not preload handoffs, session observations or every audit document.

## Ownership
Foundation owns public-safe contracts/core, public API/frontend, GitHub Actions and public deployment orchestration.
Operations owns private acquisition/execution, protected policy/resource governance, provider/runtime selection, chatbot orchestration, evaluation and private runtime evidence.
Never create a second authority for an existing behavior.

## Navigation
Use `docs/AI_SYSTEM_DIRECTORY.md` and `docs/AI_SYSTEM_MAP.json` to route intent -> category -> owner -> canonical path -> contract -> tests -> workflow -> evidence -> runtime.
Categories are orthogonal and may overlap; category membership never grants authority.

## Fast issue scheduler
1. Read current issue state.
2. Find canonical owner and mutation surface.
3. Search other surfaces only as needed.
4. Choose `ACTION | INTEGRATE | VERIFY | BLOCKED | DUPLICATE`.
5. Work the earliest missing evidence gate.
6. Cluster symptoms with the same owner and acceptance dependency.

## Parallelism
Use 1–4 disjoint read-only lanes by default. Add lanes only when they reduce total work. Cross-fire means independent evidence. Serialize writes and merges.

## Runtime
For hard paths use `input -> auth/trust -> route -> budget -> provider/tool -> side effects -> terminal -> recovery -> evidence`. Do not reset budgets, self-authorize, self-promote or duplicate durable work.

## Hygiene and documentation synchronization

Run the hygiene and code-documentation gates for every material change:

```text
python tools/repository_hygiene.py --changed-from <base-sha> --format-check --strict
python tools/code_documentation_sync.py --changed-from <base-sha> --strict
```

Use the canonical shared format contract and sync map. Mapped code changes require the owning documentation update unless a reviewed `sync_exemption_reason` is present.

## Completion
Remaining issues must be explicit runtime/external/admin blockers, duplicates/superseded items or roadmap work, with owner and missing proof recorded.
