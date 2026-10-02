# AI Audit System

Status: current routing system for repository, chatbot, Actions, benchmark, research, provider fleet and migration audits.

## Modes
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

## Default flow
index -> owner -> evidence -> independent checks -> root cause -> minimal repair -> focused verify -> reconcile.

Do not start with a repository-wide mechanical read when an indexed owner/path or issue already identifies the relevant surface.

## Adaptive parallelism
Start with 1–4 disjoint read-only lenses. Add lanes only when expected information gain exceeds retrieval/coordination cost.
A second lens must cover a different boundary or evidence class. Re-reading the same files is not cross-fire. Writes, branch changes, issue mutations and merges are serialized.

## Retrieval budget
Use the project map and owner indexes before broad search. Prefer exact path, relevant ranges, issue/PR summaries and current SHAs over repeated history. Measure retrieval bytes and tool calls when optimizing.

## Evidence
SOURCE -> TESTED -> RUNTIME -> PRODUCTION. Legacy R0–R4/L0–L4 labels are compatibility aliases only.

## Provider / AI synchronization
The private Operations task fabric is the runtime authority for provider selection, quota, freshness, cost, privacy and provider-specific capability state.
The Foundation public contract mirrors only the supported provider-family set and task families. It must never expose credentials or duplicate private endpoint configuration.

For every provider audit, reconcile:
- Operations provider_catalog.py
- Operations provider_runtime.py
- Operations ai_task_fabric.py
- Operations tools/provider_fleet_probe.py
- Foundation AI_PROVIDER_FLEET_2026-09-30.json

A provider-family count/list mismatch is configuration/documentation drift and must be fixed before treating the fleet as synchronized.
OpenAI-compatible transport is not semantic equivalence. System/developer-role, tools, structured output, streaming, context and error semantics require differential evidence where those capabilities matter.

## Extractor / mapper synchronization
The extractor/mapper family boundary is two responsibility layers, not a third authority. Operations owns private acquisition/extraction/orchestration/evidence; Foundation owns delegated public deterministic mapping/identity/quality.
AI extraction_assist is candidate assistance only. It cannot create evidence, select mapper authority, bypass acquisition policy or promote a candidate.

## Evolution / stop
New defect -> existing owner/issue when possible; blind spot -> rule/test; false positive -> detector refinement; stale data -> freshness rule; tool limit -> retrieval/lane change.
Stop on a definitive finding, concrete blocker, protected runtime boundary, or no new information. Never close runtime/production acceptance from static inspection or deterministic CI alone.

## Twice-daily governance control loop

The autonomous supervisor is also the scheduled governance coordinator. At 02:17 and 14:17 UTC, the Foundation workflow gathers deterministic family hygiene/code-document synchronization summaries, then calls the canonical `audit_assist` task family with aggregate Operations state. The planner chooses up to three non-overlapping existing evidence workflows.

Each run has a bounded mission issue. Candidate findings can be deduplicated into issue comments or new issues, but findings never close acceptance gates. Mechanical formatter drift may dispatch the deterministic hygiene autofix workflow, which creates a review PR rather than merging it. Runtime, provider, Cloudflare, migration and production claims still require their existing execution/evidence authorities.

Cross-fire remains mandatory: the sweep combines repository/contract evidence with independent workflow/runtime evidence rather than asking one model to validate its own plan.

## Current GitHub state
Read active main heads, open issue inventory and open PRs from GitHub live state at audit start. Dated state documents are synchronization evidence, not mutable queue authorities.