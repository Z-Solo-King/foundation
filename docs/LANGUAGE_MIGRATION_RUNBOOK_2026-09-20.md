# Language Migration Runbook — 2026-09-20

## Principle

Use the best language for the specific workload, not the language with the best generic benchmark.

The migration program is incremental and parallel. At no point should a rewrite become the sole production implementation before contract equivalence and failure-path parity are proven.

## Parallel migration lanes

| Lane | Scope | Candidate | First gate |
|---|---|---|---|
| L1 | Public Worker edge/router | TypeScript | Exact HTTP/auth/SSE contract |
| L2 | Extractor parser hot path | Rust | CPU + RSS + correctness benchmark |
| L3 | Search adapters | TypeScript/Python | Provider contract + quota/billing policy |
| L4 | High-concurrency standalone service | Go | Only if external service need is proven |
| L5 | Browser acquisition | Keep Python/Playwright initially | No migration until browser latency attribution proves language is relevant |
| L6 | Policy/evidence/LLM orchestration | Keep Python | No migration without measured bottleneck |
| L7 | Durable state/idempotency | Keep Python initially | No migration until D1/transaction contention is measured |

Lanes can run in parallel only when they touch different ownership boundaries. Shared contract changes must land first.

## L1 — TypeScript Worker migration

### Preserve
- all public routes;
- authentication and authorization;
- request schema;
- response schema;
- SSE start -> delta -> done behavior;
- error taxonomy;
- request/correlation identifiers;
- rate/resource gates;
- public/private routing;
- exact production deployment owner.

### Shadow methodology
1. Build worker-ts beside the Python Worker.
2. Generate contract fixtures from current production receipts.
3. Run both implementations against the same fixture corpus.
4. Compare normalized response envelopes, headers, status codes, SSE event sequences, and failure classes.
5. Load-test identical requests.
6. Canary only routes with zero semantic diff.

### Promotion threshold
- 100% contract fixture equivalence;
- 0 authorization regressions;
- 0 SSE semantic regressions;
- lower median and p95 CPU/latency on a representative workload;
- no statistically meaningful increase in error rate.

## L2 — Rust extraction core

### Scope
Do not rewrite the whole extractor.

Start with the most deterministic CPU-heavy layer:
- HTML tokenization;
- JSON/JSON-LD parsing;
- structured-field extraction;
- canonical normalization.

Keep strategy selection, source policy, retries, and evidence policy in Python.

### Interface
Use a narrow versioned ABI:
- input: bounded document + extraction contract;
- output: canonical observation envelope;
- errors: stable typed error codes;
- provenance: source URL, method, parser version, content hash.

Initial implementation options:
- Rust library consumed by a test harness;
- Rust/Wasm module for Worker-compatible parsing only if benchmarked.

### Promotion threshold
Rust must improve the relevant parser slice without changing output semantics. Memory use and tail latency matter more than microbenchmark peak throughput.

## L3 — Search provider adapter migration

Implement a common adapter:

SearchProvider
- capabilities()
- eligibility()
- quota()
- estimate_cost()
- search()
- health()
- cooldown()
- evidence_metadata()

Each provider has independent policy metadata.

Do not make provider names part of application business logic.

## L4 — Go service trigger

Go is not a default replacement.

Introduce it only if profiling proves the system needs a long-lived high-concurrency network service outside the Worker boundary.

Suitable candidates:
- proxy/fan-out gateway;
- high-volume fetch scheduler;
- rate-limit coordinator.

If introduced, it must remain behind the same API contract used by Python.

## Benchmark matrix

Every migration candidate must run a matrix that varies:
- payload size;
- concurrency;
- cache hit/miss;
- success/timeout/429/403;
- malformed input;
- slow provider;
- duplicate request;
- cancellation;
- memory pressure;
- cold start/warm start;
- representative production traffic mix.

Run at least 20 orthogonal cases rather than 20 copies of one test.

## Evidence and rollback

Each migration run stores:
- source commit;
- candidate commit;
- language/runtime version;
- dependency lock hash;
- workload ID;
- input corpus version;
- output digest;
- latency percentiles;
- CPU time;
- RSS/heap;
- failure counts by class;
- authorization/security results;
- contract diff;
- promotion decision.

Promotion sequence:

sandbox -> regression -> shadow -> canary -> production

Rollback must be a single immutable revision change, not a source edit during an incident.

## Why the current project remains hybrid

Python wins on:
- existing research/AI ecosystem;
- rapid policy changes;
- data parsing and experimentation;
- existing codebase maturity.

TypeScript wins on:
- native Cloudflare edge APIs;
- web standards;
- streaming/fetch integration;
- static contract checking.

Rust wins on:
- memory-safe high-performance parsing;
- predictable CPU/memory behavior;
- zero-copy/systems-level components.

Go wins on:
- simple high-concurrency network services;
- straightforward deployment and operational model.

PHP does not currently add a useful capability.

Java/Kotlin are technically strong, especially for structured concurrency and JVM services, but do not solve an identified project bottleneck.

C/C++ remain specialist options only.

## Non-negotiable migration rule

Never accept "Rust is faster", "Go is lighter", or "Node is faster than Python" as a migration justification.

Accept a migration only when:

measured bottleneck
+ candidate improvement
+ contract equivalence
+ failure parity
+ security parity
+ operational fit
> migration complexity
