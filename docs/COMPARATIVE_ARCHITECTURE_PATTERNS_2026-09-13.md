# Comparative Architecture Patterns — 2026-09-13

This note records reusable design patterns discovered while comparing the Research Intelligence Engine against mature extractor, mapper, AI-agent, LLM-runtime, GitHub and cloud infrastructure repositories.

## 1. Core rule

Copy **interfaces and control-plane boundaries**, not entire frameworks.

The engine remains contract-first:

`ResearchContract -> Policy/$0 Gate -> Planner -> Capability/Resource Router -> Acquisition -> Observation -> Integrity/Lineage -> Mapper -> Verification -> Publication -> Evaluation -> Controlled Learning`

## 2. Extractor patterns

### Adopt

- Persistent request identity and queue semantics.
- Explicit attempt/retry/idempotency fields.
- Acquisition strategy selected separately from execution.
- Pagination as a state machine with terminal reasons and completeness evidence.
- Cheap representation escalation: API/feed/structured/page/browser.
- Negative observations retained for future route selection.
- Parser/router ownership remains explicit.

### Do not adopt blindly

- Framework-specific middleware stacks that duplicate policy ownership.
- Browser-first extraction.
- Unbounded crawl/retry loops.

## 3. Mapper/entity-resolution patterns

Treat mapping as multiple stages:

1. deterministic identity checks;
2. candidate generation/blocking;
3. normalized field comparison;
4. similarity/semantic scoring only where needed;
5. variant/entity/offer decision;
6. conflict preservation and verification state.

Every mapping should be explainable through a `MappingDecision` referencing observations and evidence.

## 4. AI chatbot / coding-agent patterns

Capability should be represented explicitly:

- tool inputs/outputs;
- permissions;
- resource class;
- cacheability;
- reliability;
- failure classes;
- provenance;
- version.

Code/file/data/media execution must use an explicit tool envelope and isolated runtime boundary. Generated output is an artifact, not authority.

## 5. LLM-runtime patterns

Separate scheduling from cache management.

For our engine this means token planning becomes a first-class resource:

- input limit;
- output limit;
- total limit;
- verification reserve;
- final-answer reserve;
- exact cache eligibility;
- prefix reuse eligibility;
- compression availability;
- model downgrade availability.

Do not optimize token count without hard correctness/provenance floors.

## 6. Retry / queue methodology

Use explicit `RetryPolicy` and `BackoffPolicy` data rather than scattered retry constants.

Every queued unit needs:

- idempotency key;
- attempt number;
- parent request/run;
- retryable vs permanent classification;
- alternate-strategy possibility;
- dead-letter reason.

Operations remains authoritative for resource/quota enforcement.

## 7. Cloudflare / object-storage patterns

- Prefer direct Worker bindings over avoidable REST detours.
- Use D1 batch/transaction semantics for related state transitions.
- Use Queues for bounded independent work.
- Escalate to Workflows for durable long-running tasks, sleeps, retries and external waits.
- Artifact manifests must include content hash/checksum, size, type, retention and producer/version metadata.
- B2/R2 implementations remain replaceable behind the artifact contract.

## 8. Typed-language patterns

The Python implementation should borrow the semantics of stronger type systems without creating a heavyweight framework:

- Java sealed-state idea -> `Enum` + frozen dataclasses.
- Rust typestate idea -> explicit transition functions and reason-coded decisions.
- TypeScript discriminated unions -> tagged decisions/contracts.
- Swift actors/structured concurrency -> one owner for mutable resource state and explicit async boundaries.

## 9. StrategyCard methodology

Every measurable strategy should expose:

- family;
- inputs/outputs;
- assumptions/prerequisites;
- expected quality/completeness;
- latency/resource estimate;
- evidence directness;
- failure classes;
- retryability;
- token profile;
- cache profile;
- canonical owner;
- version.

Strategies are evaluated under bounded cross-pairs and a multi-metric promotion gate. One metric never authorizes promotion.

## 10. Cache methodology

Prioritize cache layers in this order:

1. exact request/result cache;
2. normalized query/result cache;
3. content fingerprint cache;
4. prefix/prompt reuse;
5. semantic cache only after benchmark evidence.

Every cache result must carry freshness, provenance and invalidation state.

## 11. Evaluation methodology

Production evaluation should bind results to exact:

- case IDs;
- corpus ID/version;
- oracle digest;
- candidate/baseline artifact/commit digest;
- evaluator version;
- pass/fail counts;
- per-category results;
- evidence digest;
- execution receipt.

A summary count is not enough evidence that a benchmark actually ran.

## 12. Maintainability

The family audit established a useful engineering constraint: cognitive complexity is a major risk even when algorithmic complexity is acceptable. Keep production modules/functions/classes bounded, use path-specific AI instructions, and continuously check duplicate implementations/policy text across repositories.

## 13. Current implementation slice

The planner branch now contains `backend/intelligence/strategy_contracts.py`, providing public-safe `StrategyCard`, `RetryPolicy`, `CacheProfile`, `TokenBudget`, and `TokenDecision` contracts. The module performs validation and deterministic token-decision logic only; provider/resource authority remains outside Foundation.

## 14. Benchmark-before-adoption rules

Do not make semantic/vector retrieval, large-model routing, Durable Objects, or agentic memory mandatory merely because another repository uses them. Add them only when a controlled benchmark demonstrates improvement under the engine's hard trust and $0 constraints.
