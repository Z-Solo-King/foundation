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

## Comprehensive twice-daily governance sweep
This scheduled control scans the combined family across eight disjoint observation lanes: structure/hygiene, migration/public-private boundary, research/feed, provider/runtime, work items/workflow, maps/docs/policy, quality/learning/evolution, and performance/resources. It is observation and triage telemetry, not a second authority. The sweep publishes deterministic findings, comments on affected open PRs, and wakes the existing autonomous engineering supervisor for bounded remediation.

## Migration completion gate — 2026-10-02

The public/private migration is an ownership change, not a test-deletion exercise. Independent audit lenses must verify that removed private implementation is represented by one canonical Operations owner and that the retained Foundation surface remains public-safe.

The migration pass sequence is:

1. compare current Foundation and Operations maps;
2. enumerate changed tracked files and matched documentation groups;
3. scan workflow authority and public-surface policy;
4. run cross-system equivalence and duplicate-content detection;
5. run focused tests and protected PR checks;
6. verify exact production/runtime revisions when a live claim is made;
7. update only the canonical owning repository/document.

AI planners can prioritize and cross-check evidence but cannot certify production truth, change policy, promote a provider, or replace a runtime receipt.

## Six-lane CrossFire standard

For difficult audits, use independent ownership/policy, TypeScript, Rust, Go, Cloudflare/runtime, and security/evidence lenses. Each lane works from the same immutable input snapshot and emits bounded evidence. Intermediate findings are not treated as shared truth until deterministic reconciliation completes. A provider comparison is meaningful only when enough independently configured providers actually execute; unavailable providers are reported as limitations rather than simulated.


## 2026-10-02 current-main reconciliation
Cross-system audit now includes deterministic Foundation/Operations N4 structural comparison, six-lane CrossFire provider/verification surfaces, current issue/PR synchronization semantics, and dispatch-target validation. Repeated autonomous failures must produce a new strategy or a terminal state; stale/non-dispatchable workflow references are configuration defects, not evidence of successful execution. Runtime and production conclusions still require their dedicated live receipts.
### Provider benchmark automation routing

Provider CrossFire benchmark findings are routed to the existing `runtime_reconciliation` allowlist before generic nightly-research matching. This keeps provider benchmark work attached to the dedicated `live-ai-provider-crossfire.yml` evidence workflow instead of accidentally dispatching the broader nightly research path.
