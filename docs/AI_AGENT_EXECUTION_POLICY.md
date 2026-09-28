# AI Agent Execution Policy

**Status:** current.  
**Scope:** AI-assisted engineering across the Foundation/Operations family.

## 1. Authority and boundaries
- Fresh GitHub \`main\`, current Issues/PRs/CI and execution evidence outrank dated notes and chat history.
- Fresh Cloudflare runtime/control-plane evidence is authoritative for deployed Workers, D1, bindings, schedules, secrets and production state.
- Foundation owns public-safe contracts/core, public API/frontend, GitHub Actions and public deployment orchestration.
- Operations owns protected policy/resource governance, acquisition/execution, provider state, chatbot orchestration, evaluation and private runtime evidence.
- Never copy private authority across the public/private boundary or create a second owner for the same behavior.
- GitHub/Cloudflare chat separation is a **transport constraint**, not product architecture: use separate chats when connector availability is isolated or unreliable; when both are available, one session may inspect both surfaces. Never infer live state from conversation context.

## 2. Work cycle
\`diagnose -> select evidence -> independent checks -> cluster root cause -> minimal repair -> focused verification -> reconcile -> checkpoint\`.

Prefer exact paths, SHAs, run IDs and receipts. Do not retrieve large histories when an indexed owner/path is sufficient.

## 3. Adaptive parallelism
- Default to the smallest number of genuinely independent read-only lanes that improves information gain; 1–4 is normal.
- Add more lanes only when boundaries are disjoint and the extra lane reduces time or retrieval cost.
- Cross-fire means **independent validation**, not duplicate reading.
- Shared files, branches, issue mutation and merges remain serialized.

Useful lenses: forward dataflow, reverse terminal/recovery, contract/policy, evidence/CI. Add security, runtime or language lenses only when the question requires them.

## 4. Issue handling
Use one primary disposition: \`ACTION | INTEGRATE | VERIFY | BLOCKED | DUPLICATE\`.
Mark superseded/roadmap status as metadata when needed.

Cluster work when canonical owner, mutation surface and acceptance dependency are shared. Do not create a new issue merely because a new symptom appeared.

## 5. Mutation integrity
Before a write: refresh base; verify exact blob/ref; check conflicting PRs; confirm canonical owner.
After a write: re-read the changed file; inspect diff/PR; run focused verification.
Never bypass branch protection or required checks.

## 6. One evidence model
Use one gate axis: \`SOURCE -> TESTED -> RUNTIME -> PRODUCTION\`.
Legacy R0–R4/L0–L4 references are compatibility labels for older records, not a second policy system. A lower gate cannot satisfy a higher gate. A merged PR is not runtime/production evidence.

## 7. Runtime invariants
For difficult paths model:
\`input -> trust/auth -> route -> budget/deadline -> provider/tool -> side effects -> terminal -> recovery -> telemetry -> evidence\`.

Child work inherits identity, deadline and remaining budget. Do not self-authorize, mint quota, extend deadlines, self-promote providers, or duplicate durable work. Keep cancellation, timeout, transient failure, capacity, policy denial and unknown state distinct.

## 8. Documentation
One current fact has one canonical owner. Session notes and handoffs are transport aids, not authority.
- Stable active docs use date-free names.
- Historical receipts/plans may retain dates and belong under \`docs/history/\` when relocated.
- Do not add a new document when an existing owner can be updated.
- Do not put private credentials or protected runtime values in public documentation.

## 9. Audit routing
\`docs/AI_AUDIT_SYSTEM.md\` is the routing guide; \`docs/AI_PROJECT_MAP.json\` is navigation metadata. Contracts, owner registries, source, tests and runtime receipts remain authoritative.
Large audits begin issue/context-first and use map-first retrieval, adaptive lanes, root-cause clustering and second-lens validation. Compute-inspired patterns are optional engineering analogies.

## 11. Migration / polyglot
Language changes are evidence-driven. Python remains protected semantic/policy/provenance/replay/resource authority until formal promotion. Candidates need contract, differential, adversarial, performance/resource, shadow, canary and rollback evidence.

## 12. Completion
Remaining work must be explicit \`RUNTIME\`, \`EXTERNAL/ADMIN\`, \`DUPLICATE/SUPERSEDED\` or \`ROADMAP\`, with canonical owner and missing evidence recorded.
