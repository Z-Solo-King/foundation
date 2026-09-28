# AI Audit System

**Status:** current routing system for repository, chatbot, Actions, benchmark, research and migration audits.

## 1. Modes
Use the smallest mode that answers the question:
1. FAST — indexed files, issues, PRs, refs and owners.
2. OWNERSHIP — boundaries, imports, duplicate authority and dataflow.
3. DRIFT — canonical docs, stale references and history/current separation.
4. SECURITY — auth, secrets, trust boundaries and fail-closed behavior.
5. RUNTIME — provider/resource/replay/recovery and live evidence.
6. DIFFERENTIAL — reference vs candidate, language/provider/site compatibility and regression corpus.
7. WORKFLOW — triggers, permissions, refs, secrets, artifacts and deploy/rollback.
8. BENCHMARK — correctness, repeats, latency, retrieval/resource cost and lineage.
9. HYBRID — compose only what the acceptance question needs.

## 2. Default flow
\`index -> owner -> evidence -> independent checks -> root cause -> minimal repair -> focused verify -> reconcile\`.

Do not start with a repository-wide mechanical read when an indexed owner/path or issue already identifies the relevant surface.

## 3. Adaptive parallelism
Start with 1–4 disjoint read-only lenses. Add lanes only when expected information gain exceeds retrieval/coordination cost.
Recommended lenses:
- forward: producer -> consumer -> terminal;
- reverse: terminal/recovery -> upstream;
- contract: policy/contract -> implementation -> tests;
- evidence: CI/runtime/artifacts -> implementation -> acceptance.

A second lens must cover a different boundary or evidence class. Re-reading the same files is not cross-fire. Writes, branch changes, issue mutations and merges are serialized.

## 4. Retrieval budget
Use the project map and owner indexes before broad search. Prefer exact path, relevant ranges, issue/PR summaries and current SHAs over repeated history. Measure retrieval bytes and tool calls when optimizing.

## 5. Evidence
Use one model: \`SOURCE -> TESTED -> RUNTIME -> PRODUCTION\`. Legacy R0–R4/L0–L4 labels are compatibility aliases only.

## 6. Routing graph
The graph may contain file, symbol, feature, policy, issue, PR, workflow, test, artifact, receipt and external-source nodes. Edges include owns, calls, consumes, validates, documents, tests, deploys, produces, depends_on, duplicates and supersedes. The graph is navigation metadata, not authority.

## 7. Optional compute patterns
Use \`docs/AI_COMPUTE_INSPIRED_PATTERNS.md\` only when it gives a measurable improvement. No pattern creates authority or requires a new issue.

## 8. Evolution / stop
new defect -> existing owner/issue when possible; blind spot -> rule/test; false positive -> detector refinement; stale data -> freshness rule; tool limit -> retrieval/lane change.
Stop on a definitive finding, concrete admin/external blocker, protected runtime boundary, or no new information. Never close runtime/production acceptance from static inspection or deterministic CI alone.

## Authority
Repository contracts, source, tests, workflow evidence and runtime receipts remain authoritative; the project map and audit system only route work.
