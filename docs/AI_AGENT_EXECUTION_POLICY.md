# ChatGPT Policy

**Effective: 2026-09-24**

This policy governs AI-assisted engineering work in the Research Intelligence Engine. It is intentionally named **ChatGPT Policy** so any AI agent entering this project can discover the execution and context-safety rules immediately. It does not change production runtime authority.

## 1. Connector usage

GitHub and Cloudflare connectors **may be used in the same work cycle when both are available and healthy**.

- GitHub covers repository source, issues, pull requests, CI, tests, artifacts, branch/ref state, and GitHub-side evidence.
- Cloudflare covers Workers, D1, bindings, secrets/configuration, deployments, runtime probes, cron, live provider configuration, and production receipts.
- Cross-surface checks are encouraged when a conclusion depends on both repository state and runtime state.
- If either connector fails, times out, loses authorization, or returns incomplete data, isolate that surface, preserve the last verified evidence, and continue only with independent work.
- Never infer Cloudflare runtime state from GitHub alone, and never infer repository state from a Cloudflare deployment alone.
- Shared state is carried by compact repository checkpoints/documents; do not reconstruct an entire prior chat.

## 2. Work-cycle structure

Every cycle uses four barriers:

1. **Diagnosis barrier** — inspect the contract, current state, and smallest relevant evidence; identify confirmed root causes and distinguish code defects from evidence/configuration gates.
2. **Repair barrier** — apply only justified fixes, preferably grouped by responsibility.
3. **Verification barrier** — run affected tests/probes and inspect targeted failures only.
4. **Checkpoint barrier** — reconcile Foundation, Operations, GitHub, Cloudflare, evidence class, and remaining blockers.

Do not cross a barrier until the prior stage has a compact result.

## 3. Parallel-lane strategy

Use bounded parallelism to increase execution speed without creating a polling or context explosion.

Default target: **4 lanes**, expandable to **6 lanes** when the work is genuinely independent.

Recommended lane types:
- **L1 Repository/static:** source contracts, workflow definitions, docs, tests, configuration.
- **L2 CI/control-plane:** recent workflow failures, branch/ref behavior, artifacts, required checks, concurrency.
- **L3 Cloudflare/runtime:** Worker versions, routes, bindings, D1, cron, runtime probes, provider responses.
- **L4 Evidence/issues:** open-issue acceptance requirements, prior receipts, closure evidence, stale issue statements.
- **L5 Benchmark/migration:** targeted differential tests, performance/resource measurements, language-migration candidates.
- **L6 Reconciliation:** source-of-truth synchronization, cross-repo pins, deployment provenance, checkpoint integrity.

Lane rules:
- Lanes must be independent at the read/diagnosis stage.
- Each lane returns only: **finding, evidence level, affected files/resources, proposed action, verification target**.
- Shared files, shared refs, and deployment authority are serialized through a single owner lane.
- Do not create parallel lanes that all need continuous polling.
- Prefer parallel reads and independent tests, then one consolidated repair batch.

## 4. Context, output, and session budget

A single ChatGPT Thinking work session is intentionally capped at **20 minutes for this project**, leaving a safety margin below longer platform-side thinking windows. This is a project execution limit, not a claim about an OpenAI product hard limit.

For commands that authorize sustained execution, use explicit wording such as:

> **Keep going until completed, within the 20-minute session limit.**

The phrase means: continue through diagnosis, repair, verification, and checkpoint work within the current session; do not stop after the first useful finding. It does **not** authorize infinite loops or unbounded polling.

To prevent ChatGPT or another AI agent from getting stuck in an oversized session:

- Aim for **8-12 focused repository/runtime reads** per cycle.
- Aim for **no more than 6 detailed file/log/artifact reads**.
- Group related writes into **at most 3 focused PRs** unless a safety-critical repair requires otherwise.
- Inspect running workflows at phase boundaries, not continuously.
- Prefer exact file ranges, failure excerpts, run IDs, artifact IDs, and hashes over full logs.
- Reuse verified evidence while the referenced revision has not changed.
- Never recursively launch scan -> repair -> poll -> rescan without a checkpoint.
- When the 20-minute session window is near exhaustion, checkpoint immediately; do not begin a new expensive scan.
- When context or tool volume becomes large, checkpoint and start a fresh AI chat/cycle.
- At every session boundary, record observed behavior, bottlenecks, connector health, tool-call pattern, and what change should be made to improve the next session.

The objective is not to make the agent stop early. The objective is to make each cycle **small, resumable, and information-dense**.

## 5. CI and polling discipline

- Never tight-loop on a running workflow.
- Record workflow/run/job IDs and revisit them at meaningful barriers.
- A queued or in-progress run is not itself a reason to keep the chat active.
- Newer commits supersede older analysis; stale runs remain historical evidence.
- Use workflow concurrency controls where appropriate so superseded expensive jobs do not accumulate.
- Do not launch a replacement run merely because an earlier run is still running.

## 6. Repair discipline

- One confirmed root cause -> one focused repair.
- Consolidate closely related fixes into one PR.
- Prefer the smallest change that restores the canonical contract.
- Do not change immutable production pins merely to make shadow or migration tests pass.
- Do not introduce a second authority for lifecycle, resource governance, policy, persistence, provenance, replay, or deployment.
- Do not close an L4 issue from L1/L2/L3 evidence.
- Runtime configuration blockers must be recorded as configuration/runtime gates, not misclassified as code defects.

## 7. Evidence ladder

- **L0:** hypothesis.
- **L1:** external/source evidence.
- **L2:** repository implementation/tests.
- **L3:** GitHub Actions/control-plane evidence.
- **L4:** approved runtime/production receipt.

A lower evidence level may justify the next test, but it must never be presented as a higher level of acceptance.

## 8. Cross-surface verification

When a task depends on both GitHub and Cloudflare, use a controlled cross-surface sequence:

**GitHub source/ref -> GitHub CI/evidence -> Cloudflare deployed ref/version -> runtime probe/receipt -> reconciliation checkpoint.**

When possible, perform GitHub and Cloudflare reads in parallel, then reconcile their results at one barrier. Do not repeatedly alternate between connectors without a specific dependency.

## 9. Issue triage and closure

For each open issue, classify it before modifying code:

- **R:** confirmed repository defect; patch now.
- **C:** runtime/configuration prerequisite; verify/coordinate on the owning control plane.
- **E:** evidence-only acceptance gate; execute the required receipt, not speculative code changes.
- **H:** historical/stale description; preserve history and update the current checkpoint instead of reopening old work.

Only R issues should trigger routine mechanical code repair. C and E issues require the evidence named by the issue. H issues should not cause churn.

## 10. Checkpoint requirements

Every completed cycle records, compactly:

- Foundation main SHA.
- Operations main SHA.
- Open issue count and IDs.
- Open PR count and IDs.
- Changed PRs and merge status.
- Relevant workflow/run/job IDs and conclusions.
- Relevant Cloudflare Worker/deployment/version identifiers when available.
- Artifact IDs and evidence class.
- Immutable production pins.
- Remaining blockers and their owner surface.
- Next bounded action.

## 11. Preferred execution order

**Diagnose -> parallel independent checks -> consolidate root causes -> minimal repair batch -> targeted verification -> cross-surface reconciliation -> checkpoint -> next cycle.**

Do not optimize for raw tool-call count. Optimize for **verified progress per cycle**.

## 12. ChatGPT-specific safety rule

OpenAI's troubleshooting guidance recommends starting a new chat when a conversation is long or has many turns, and checking service status when ChatGPT is slow, frozen, or stuck on Thinking/Generating.

Therefore, an AI agent working in this project must not keep expanding a single conversation after it has become large or tool-heavy. It should leave a compact checkpoint and resume from that checkpoint in a fresh chat.

Source:
https://help.openai.com/en/articles/7996703-troubleshooting-chatgpt-error-messages


## 13. Mobile-app/session continuity

- The visible ChatGPT mobile conversation is a transport/UI surface, not an authoritative execution ledger.
- Do not assume that closing or reopening the app either stops or preserves ordinary Chat-mode tool execution. Only GitHub/Cloudflare control-plane receipts, workflow runs, artifacts, commits and runtime receipts establish progress.
- When a long/tool-heavy cycle becomes unresponsive, reaches a practical context/length limit, or the app is closed during execution, checkpoint immediately and resume in a fresh chat. This is an **adaptive early checkpoint**, not a replacement for the 20-minute project ceiling.
- Prefer compact checkpoint payloads over carrying historical chat context forward. A fresh chat should begin from current GitHub heads, the current open-issue queue, the latest accepted runtime evidence, and the next bounded action.
- External user reports, Reddit threads, OpenAI Community posts and other platform reports may inform session-risk hypotheses, but must remain clearly separated from repository/runtime evidence.

