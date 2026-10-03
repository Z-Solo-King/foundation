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

For hard paths use `input -> auth/trust -> route -> budget -> provider/tool -> side effects -> terminal -> recovery -> evidence`.

Do not reset budgets, self-authorize, self-promote or duplicate durable work.

## Hygiene and documentation synchronization

Run the hygiene and code-documentation gates for every material change:

```text
node tools/repository_hygiene.mjs --changed-from <base-sha> --format-check --strict
node tools/code_documentation_sync.mjs --changed-from <base-sha> --strict
```

Use the canonical shared format contract and sync map. Mapped code changes require the owning documentation update unless a reviewed `sync_exemption_reason` is present.

## Security protocol

Treat privileged automation as a trust boundary, not a convenience mechanism.

1. Any `workflow_run` workflow is privileged because it can access secrets and elevated tokens. Never execute pull-request, fork, merge-group, or otherwise untrusted code in that privilege domain. Checkout only trusted `main` or an explicitly verified immutable SHA.
2. Grant `GITHUB_TOKEN` and GitHub App tokens the minimum permissions required. Private Operations checkout for Foundation workflows is read-only unless a separately owned workflow explicitly requires a write permission.
3. AI automation, CrossFire, benchmarks, research synthesis and model outputs are evidence/advisory inputs only. They cannot self-authorize, self-promote, merge, deploy, alter policy, or establish production truth.
4. Production Cloudflare Workers, bindings, secrets and deployment pins are changed only through the canonical Foundation production-release workflow on protected `main`. Direct connector mutation is inspection-only except for a separately documented break-glass procedure with explicit authorization.
5. Never publish raw private GitHub/Cloudflare API responses, credentials, private revision metadata or provider payloads into public issues, logs or artifacts. Store private inspection data transiently, sanitize receipts, then delete the raw material before upload.
6. Treat immutable pins as lineage controls. A newer Operations `main` commit is not itself an integrity failure when the approved revision is an ancestor; fail only on divergence, invalid identity, or an unauthorized authority change.
7. Do not bypass required checks, protection rules, security scans or release gates to make a run green. Record unresolved external/admin credential failures as `EXTERNAL/ADMIN` blockers.
8. Parallelism is for independent read-only investigation. Serialize repository writes, production changes and merges.

## Completion

Remaining issues must be explicit runtime/external/admin blockers, duplicates/superseded items or roadmap work, with owner and missing proof recorded.
