# Language Migration Runbook — 2026-09-20

Revision: reconciliation pass after reviewing `foundation` and `operations` (docs, code, open PRs) on 2026-09-20.

## Principle

Use the best language for the specific workload, not the language with the best generic benchmark.

The migration program is incremental and parallel. At no point should a rewrite become the sole production implementation before contract equivalence and failure-path parity are proven.

## Current status (2026-09-20)

| Lane | State in repos | Evidence |
|---|---|---|
| L1 Worker edge | Phase B contract shadow: typed route matrix, auth extraction, cache policy, bounded JSON sizing and deterministic SSE framing. No private authority or production routing has moved. | `polyglot/edge-worker/`, Foundation hybrid-language pilot CI |
| L2 Rust core | Pilots only, outside production authority. HTML kernel contract test checks substrings, not exact parity with the Python extractor. No profile-based justification found in the docs or pilots reviewed. | operations PR #570, #565 |
| L3 Search adapters | Four TypeScript shadow adapters in `operations/polyglot/search-adapters`: Brave, Jina Search, Jina Reader, SearXNG. Repository contract hardening and Foundation-owned CI are merged. Default timeout, policy handoff, response-header allowlisting and deterministic failure coverage are enforced; recorded/live parity is still pending. | `adapters.ts`, `adapters.test.ts`, Operations #576 plus Foundation #811 |
| L4 Go | Benchmark pilot only. No service. No independent deployment need has been shown. | operations PR #564, #570 |
| L5–L7 | Python, unchanged. | — |

## Decisions that resolve conflicts between plan documents

1. **First promoted production slice remains L3 (search adapters).** L1 can advance in parallel as a contract-only shadow because it does not own protected policy/state. No production language switch occurs until the L1 fixture gates and L3 provider gates are independently satisfied.
2. **Browser/Playwright (L5).** Existing Python browser acquisition stays in Python. New browser orchestration may be written in TypeScript. No existing Python Playwright code is migrated until browser latency attribution shows the language is relevant.
3. **Go (L4).** Benchmark pilot only. It becomes a service only under the L4 trigger below.
4. **PHP.** Boundary-only WordPress adapter. No PHP in the core.
5. **Zero-cost is a hard gate for every search provider** (see L3). This was already enforced in the Python policy and the TypeScript pilot in PR #570, and must apply to the shipped adapters as well.

## Parallel migration lanes

| Lane | Scope | Candidate | First gate |
|---|---|---|---|
| L1 | Public Worker edge/router | TypeScript | Exact HTTP/auth/SSE contract |
| L2 | Extractor parser hot path | Rust | Profile proves parser bottleneck, then CPU + RSS + correctness benchmark |
| L3 | Search adapters | TypeScript | Provider contract + zero-cost authorization + quota/billing policy |
| L4 | High-concurrency standalone service | Go | Only if external service need is proven |
| L5 | Browser acquisition | Existing code stays Python; new work may use TypeScript | No migration of existing code until browser latency attribution proves language is relevant |
| L6 | Policy/evidence/LLM orchestration | Keep Python | No migration without measured bottleneck |
| L7 | Durable state/idempotency | Keep Python initially | No migration until D1/transaction contention is measured |

Lanes can run in parallel only when they touch different ownership boundaries. Shared contract changes must land first.

Current shared-contract dependency #571 is merged. L1 SSE fixtures are now generated against the landed terminal semantics; runtime cancellation evidence remains a separate gate.

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

### Canonical L1 shadow path
- `polyglot/edge-worker/` is now the sole maintained L1 contract-shadow path.
- Historical `edge_ts/` / `shadow/edge-ts/` references in older planning text are superseded; production Wrangler/Worker routing remains unchanged.

### Shadow methodology
1. Keep the TypeScript contract shadow beside the Python Worker in `polyglot/edge-worker/`.
2. Generate contract fixtures from current production receipts.
3. Add synthetic negative fixtures that production traffic will not contain: missing/invalid credentials, wrong role, malformed bodies, oversized bodies, client cancel mid-stream, upstream timeout.
4. Run both implementations against the same fixture corpus.
5. Compare normalized response envelopes, headers, status codes, SSE event sequences, and failure classes.
6. Load-test identical requests.
7. Canary only routes with zero semantic diff.

### Promotion threshold
- 100% contract fixture equivalence, including the synthetic negative fixtures;
- 0 authorization regressions;
- 0 SSE semantic regressions;
- lower median, p95 and p99 CPU/latency on a representative workload;
- no increase in error rate beyond a margin and minimum sample size that are declared in the run record before the run starts.

## L2 — Rust extraction core

### Entry condition
No Rust work is promoted beyond pilot until a profile of the current extractor on the frozen HTML corpus shows which parser slice dominates CPU, memory or tail latency. The pilots in operations PR #570 and #565 are exploratory and stay outside production authority.

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
Rust must produce byte-identical canonical output to the Python extractor on the frozen corpus (not substring checks). It must improve the relevant parser slice without changing output semantics. Memory use and tail latency matter more than microbenchmark peak throughput.

## L3 — Search provider adapter migration

### Zero-cost gate (hard requirement)
No adapter may make a live provider call unless the canonical Python policy has authorized that provider as free-eligible, pricing-verified and no-overage. This applies to shadow runs and live samples, not only production.

- The authorization decision is produced by the Python policy (`private/search_route_policy.py`, `private/search_provider_execution.py`) and passed to the adapter. TypeScript adapters must not re-implement the rules, because a second policy engine violates the governance rule in the Decision Record.
- A provider at stage `cataloged` or `configured` cannot be called live.

### Common adapter contract

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

### Shadow methodology
1. Record/replay first. Capture provider responses once (headers, status, body, latency) and replay them against both implementations. Live search results are not deterministic, so exact parity can only be tested on recorded fixtures.
2. Live samples are bounded, small, and only for providers that pass the zero-cost gate.
3. Compare normalized results, failure class, rate-limit metadata, and provenance fields.

### Provider order
Implemented as shadow adapters: Jina Reader, Jina Search, Brave, SearXNG.

Not yet built, in order: Tavily, Serper, DuckDuckGo fallback, Firecrawl. Each needs zero-cost eligibility verified before its adapter is built or called. Exa is listed in the backlog but is not part of the first slice. Conditional model-grounding providers stay behind billing and zero-cost gates.

### L3 repository-side defects status
The initial review defects have been addressed in Operations #576 except the remaining external parity evidence gate. The adapter now performs policy-decision handoff, has a default timeout, typed auth failures, reader URL validation, response-header allowlisting, malformed-response handling and expanded deterministic tests. Remaining L3 work is recorded-response/live-sample parity and provider health/cooldown equivalence.

### Promotion threshold
- recorded-fixture parity on normalized results and failure classes;
- zero-cost gate enforced and tested for every provider;
- CI contract for the package merged (operations PR #573);
- provider health/cooldown behavior matches the Python policy.

## L4 — Go service trigger

Go is not a default replacement. The current Go code is a benchmark pilot only.

Introduce a Go service only if profiling proves the system needs a long-lived high-concurrency network service outside the Worker boundary.

Suitable candidates:
- proxy/fan-out gateway;
- high-volume fetch scheduler;
- rate-limit coordinator.

If introduced, it must remain behind the same API contract used by Python. The pilot must reuse the same target lists, timeouts and retry policy as the Python benchmark executor before any comparison is valid (the current pilot has no retry policy).

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
- latency percentiles (p50, p95, p99);
- CPU time;
- RSS/heap;
- failure counts by class;
- authorization/security results;
- zero-cost authorization results;
- contract diff;
- pre-declared error-rate margin and sample size;
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

PHP does not currently add a useful capability outside a boundary-only WordPress adapter.

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
+ zero-cost parity (search providers)
+ operational fit
> migration complexity

The first-slice choice (L3) must also record its own measured justification. Add the profile or latency/cost data that motivated it to the L3 evidence record.

### L1 public HTTP transport shadow

- `polyglot/edge-worker/src/public-http.ts` now mirrors the deterministic transport contract of `backend/sources/http.py`: URL canonicalization, redirect bounds, HTTPS downgrade protection, response-size bounds and redirect provenance.
- DNS-over-HTTPS resolution and public/private-address authority are deliberately not duplicated in TypeScript. The shadow consumes an explicit `PublicDestinationDecision`, preserving Python's existing DNS/SSRF authority.
- This is a contract shadow only; `backend/sources/http.py` remains the production acquisition implementation until differential fixtures and runtime/performance evidence justify any promotion.

### Frontend lifecycle TypeScript shadow — 2026-09-20

- `polyglot/frontend-state/` mirrors `frontend/lifecycle_state_machine.js` for vocabulary, backend normalization and fail-closed transition rules.
- The shadow intentionally excludes DOM/event wiring and persistence so the first promotion gate is pure state-machine parity.
- Existing JavaScript production UI remains authoritative until the TypeScript shadow passes the same contract tests plus browser-level differential tests.
