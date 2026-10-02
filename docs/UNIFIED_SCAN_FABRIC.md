# Unified Scan Fabric

Status: architecture contract / implementation branch, 2026-10-02.

## Purpose

The project has several valid systems that previously operated as separate audit, monitor, benchmark, migration, governance, extractor/mapper, provider, security and runtime checks. They are now treated as capabilities of one scan fabric rather than independent authorities.

The fabric does not replace an authoritative test, runtime receipt, deployment gate, policy owner, or production promotion workflow. It composes them.

## Capability inventory

| Capability family | Existing surfaces | Fabric role |
|---|---|---|
| Repository inventory | repository maps, AI project maps, structure scans | shared immutable inventory |
| Governance | comprehensive governance scan, governance sweep, verification fabric | deterministic structural/policy evidence |
| CrossFire | six-lane audit, AI CrossFire, engineering/provider CrossFire | independent corroboration |
| Polyglot | polyglot governance, Rust/TS/Go experiments and differential tests | complementary analytical lenses |
| Extractor/mapper | extractor governance, mapper/extractor cross-audit | domain checks over shared inventory |
| Chatbot/provider | provider task fabric, provider crossfire, limitation intelligence | capability/runtime state |
| Runtime/Cloudflare | worker/runtime/browser checks and live receipts | external-state evidence |
| Security | secret scanning, security lanes, trust/policy checks | adversarial evidence |
| Workflow/CI | workflow scans, dispatch acceptance, required checks | automation correctness |
| Migration | ownership/placement/migration audits | boundary and equivalence evidence |
| Performance/resources | benchmarks, budgets, fan-out experiments, resource ledger | cost/latency/capacity evidence |
| Documentation/learning | maps, provenance, regression cases, learning loops | evidence freshness and drift |
| Monitoring | dashboard, scheduled governance sweep, limitation refresh | temporal re-evaluation |
| AI assistance | audit_assist/task fabric and agent benchmarks | advisory synthesis only |

## Composition rules

1. One inventory, many lenses. Every run starts from the same immutable repository/runtime snapshot and receives a run ID.
2. One evidence packet. Deterministic inventory, file hashes, revisions, environment and coverage are produced once and reused by all compatible lanes.
3. Lanes are lenses, not authorities. TypeScript, Rust, Go, security, Cloudflare/runtime and policy lanes may disagree. Reconciliation preserves disagreement instead of averaging it away.
4. Different strengths are intentional.
   - TypeScript/Node: high-throughput breadth, orchestration, cheap path classification and fan-out.
   - Rust: deeper source-quality, parsing/normalization and deterministic resource-safe checks where compiled analysis is valuable.
   - Go: bounded high-concurrency network/runtime probes where appropriate.
   - Python: existing canonical behavior/reference implementations remain valid, but are not a substitute for independent polyglot evidence.
5. 100% coverage is a matrix, not one scanner. Every tracked file is inventoried. Each file is assigned a required minimum lens set by type; unsupported-language lenses emit an explicit disposition instead of silently skipping the file.
6. Fast first, deep second. Quantity lanes establish complete breadth and partition work. Quality lanes consume those partitions and prioritize changed, risky, ambiguous or high-impact surfaces.
7. CrossFire is selective but complete. Critical findings receive at least two independent evidence paths when technically possible. A single-lane finding remains visible and is never silently discarded.
8. Monitors consume scan artifacts. Scheduled monitors compare new packets with prior packets; they do not reimplement scanners.
9. Scanners do not mutate production. Auto-fix may generate a reviewed artifact/branch, never directly promote protected runtime or policy.
10. Cloudflare is an evidence provider, not a second scan authority. Live Workers/Pages/D1 state is joined to the same run packet.
11. AI is advisory. AI may cluster, explain and prioritize deterministic findings; it cannot certify runtime truth or close acceptance.
12. Merge/trim before adding. New checks must declare which existing capability they reuse or replace. Duplicate checks are merged, weak wrappers are removed, and only genuinely orthogonal checks remain.

## Execution graph

inventory -> partition -> fast breadth -> deep quality -> domain probes -> runtime evidence -> reconcile -> deduplicate -> monitor delta -> evidence receipt

The same packet can feed PR validation, exhaustive audit, migration audit, twice-daily governance, provider/limitation refresh, extractor/mapper cross-audit, Cloudflare reconciliation and performance/benchmark runs.

## Cross-language execution matrix

| Lens | Breadth | Depth | Typical target |
|---|---:|---:|---|
| TypeScript | High | Medium | all tracked paths, metadata, workflows, configs |
| Rust | Medium | High | source files, parsers, normalization, resource-sensitive checks |
| Go | High | Medium | bounded concurrent probes and differential runtime checks |
| Security | Medium | High | secrets, trust boundaries, mutation paths |
| Cloudflare/runtime | Low | High | live Workers, Pages, D1, deployment and schedule evidence |
| Policy/reconciler | High | High | ownership, contracts, duplicate authority, evidence lineage |

No language is globally declared better. The scheduler selects a lens based on expected information gain and cost.

## Coverage contract

A run is complete only when:
- inventory_total == covered_total
- every file has a disposition: SCANNED, DELEGATED, or NOT_APPLICABLE
- every lane reports the exact input revision
- all critical findings have provenance
- disagreements are retained in reconciliation output
- runtime claims have live evidence
- no lane reports an unexplained execution failure

A lane crash is a failed lane, not zero findings.

## Consolidation rule

Existing systems should be reduced to:
- detectors: one implementation per invariant;
- lenses: language/domain-specific ways to evaluate the invariant;
- orchestrators: schedule and partition work;
- receipts: immutable evidence;
- monitors: compare receipts over time.

A workflow that merely invokes another workflow without adding an independent acceptance property should become an orchestration edge, not another scanner.

## Non-goals

This contract does not move private Operations implementation into public Foundation, change production pins, change Cloudflare production configuration, treat benchmark output as production proof, or remove existing authoritative runtime/security gates.

## Acceptance

The branch is accepted only after the existing six-lane audit, polyglot governance audit, required checks and affected domain tests agree with this contract.