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


## 9. Historical recurrence / control forensics

Use this mode when the goal is to explain repeated fixes, long remediation chains, policy drift, or recurring workflow mistakes.

Required lenses:
- closed issues and PRs across the full paginated population;
- current workflow/action definitions;
- representative failed/cancelled Action cohorts;
- owner/repository routing;
- exact revision/pin history;
- public/private disclosure boundaries;
- evidence-tier transitions;
- second-lens corroboration from the saved Master Audit and six-lane systems.

Primary output is a causal chain, not a list of old tickets:

trigger -> authority decision -> implementation surface -> validation boundary -> observed failure -> corrective action -> residual control gap -> preventive rule.

For recurring workflow problems, the audit must ask whether the documented rule is executable. A policy that exists only in Markdown or agent instructions is insufficient when the conflicting execution path remains technically available.

## 10. Workflow authority is a gate

Before selecting or editing a GitHub Action, resolve:
- authority class;
- owning repository;
- event trust level;
- secret/private-resource requirements;
- allowed workflow path;
- exact revision;
- evidence tier.

The workflow authority registry and validator are the machine-checkable control for Foundation workflows.

Public feed discovery is a public-safe Foundation workflow class. Private Operations implementation or registry access does not make Operations the workflow owner.

Privileged workflows must not execute from pull_request, pull_request_target or merge_group. Push-based privileged execution is main-only.

Privileged workflow_run execution is permitted only for an explicitly registered trusted upstream workflow. Do not treat workflow_run as automatically trusted.

## Multi-lens execution engine
The active multi-lens execution engine is the canonical scheduling overlay for cross-language, runtime, browser, extraction, provider, GitHub/workflow, Cloudflare and historical lanes. Use `tools/multi_lens_planner.mjs`, `docs/MULTI_LENS_CHATBOT_PROFILE.json`, `schemas/multi-lens-plan-v1.schema.json` and `.github/workflows/multi-lens-planner.yml`. The scheduler does not become an acceptance or policy authority.

## Current GitHub state
Read active main heads, open issue inventory and open PRs from GitHub live state at audit start. Dated state documents are synchronization evidence, not mutable queue authorities.


## Extractor surface governance
The family audit now has two dedicated lenses: `OLDEST_SURFACE` for Git-history ordering of critical files, and `SURFACE_GOVERNANCE` for capability -> owner -> policy -> test -> evidence -> migration linkage. The Operations tools are `tools/oldest_surface_audit.py` and `tools/extractor_surface_audit.py`.
