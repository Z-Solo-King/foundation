# Hybrid Language + Search Strategy — 2026-09-20

## Core decision

The Research Intelligence Engine should be deliberately polyglot and capability-driven.

We are NOT replacing Python because another language is universally faster. A migration is justified only when a component has a measurable workload mismatch with its current runtime.

| Component | Current | Target | Decision |
|---|---|---|---|
| Public Cloudflare Worker edge/API | Python | TypeScript | First migration |
| Research planning and evidence policy | Python | Python | Keep |
| Private control plane | Python | Python initially | Keep |
| Extractor orchestration | Python | Python initially | Keep; benchmark first |
| Deterministic parser/normalizer hot paths | Python/C extensions | Rust | Pilot |
| Browser acquisition/benchmark runner | Python | TypeScript/Node | Pilot |
| High-concurrency load/benchmark runner | Python | Go | Pilot |
| PHP | none | PHP | No migration |
| Java/C# | none | Java/C# | Defer |
| Elixir | none | Elixir | Defer |
| Zig | none | Zig | Defer |

## Why Python remains

Cloudflare Python Workers are first-class, execute through Pyodide/WebAssembly, support Workers bindings and have deployment-time memory snapshots that reduce cold-start work. However, threading and multiprocessing are unavailable in Python Workers and Python package support depends on PyEmscripten/Pyodide availability. Therefore Python is still the right choice for research semantics, LLM integrations, evidence policy and rapidly changing business logic, but it is not automatically the best choice for edge plumbing or CPU-heavy kernels.

## Why TypeScript first

Cloudflare Workers treats TypeScript as first-class and generates types from the Workers runtime. Recent compatibility dates also enable the current Node.js compatibility surface. TypeScript therefore removes much of the current Python-to-JavaScript FFI surface in the public Worker and fits Request, Response, fetch, streams and Service Bindings naturally.

Important distinction: TypeScript is compiled to JavaScript. Moving Python to TypeScript is not a claim that TypeScript is intrinsically faster than JavaScript or Node.js. The advantage is runtime alignment, type safety and Cloudflare-native APIs.

## Why Rust for selected hot paths

Rust provides memory safety without a garbage collector and Cloudflare supports Rust Workers through workers-rs and WebAssembly. The first candidates are URL normalization, request fingerprinting, duplicate suppression, deterministic parsing and bounded transformation kernels.

The Rust version must first be a shadow implementation. It has to produce byte/semantic-equivalent output on the real golden corpus before production cutover.

## Why Go for benchmark infrastructure

Go provides lightweight goroutines multiplexed over OS threads and is designed for high-concurrency I/O. This makes Go useful for benchmark/load drivers that need many concurrent HTTP operations without turning the production research core into another language.

## Why PHP is not a fit

PHP has mature web tooling and OPcache/JIT, but the project is Cloudflare Worker and edge-first. Cloudflare lists JavaScript, TypeScript, Python Workers and Rust as first-class Worker languages; other languages generally arrive through WebAssembly. PHP would add a new deployment/runtime family without solving a current architectural problem.

## Other languages

Java virtual threads are excellent for high-concurrency blocking I/O, but they provide scalability rather than making each operation intrinsically faster.

Modern .NET has strong JIT, stack allocation, NativeAOT and runtime optimization. C# is technically capable but redundant with the chosen Go/Rust roles here.

Elixir and the BEAM remain attractive for supervision-heavy distributed systems, but introducing a BEAM deployment is not justified while the architecture is deliberately Cloudflare-first.

Zig offers explicit control and low hidden overhead, but the current project has no workload that justifies adding another relatively specialized toolchain.

## Search architecture

The Operations search catalog already covers a broad hybrid set: Brave, Tavily, Serper, Exa, SerpAPI, Jina Reader/Search, Firecrawl, DuckDuckGo fallback, SearXNG, You.com, Kagi, Bocha, Parallel, OpenAI web search and Gemini grounding. Bing is marked retired and Google Custom Search JSON is marked sunsetting.

The correct design is capability routing, not provider proliferation.

Default routing:

1. Source-native or official search when an allowed native surface exists.
2. Brave for general independent discovery.
3. Tavily for agent/RAG-oriented retrieval.
4. Exa for semantic discovery and deep research.
5. Serper for structured Google SERP requirements.
6. Jina Reader for page-to-document retrieval.
7. Firecrawl for crawl/search-plus-extraction where permitted.
8. SearXNG for self-hosted metasearch fallback.
9. DuckDuckGo only as a keyless fallback; 403/429/CAPTCHA becomes defer, never bypass.
10. Bocha for Chinese-web discovery when allowed.
11. OpenAI or Gemini web grounding only after runtime billing and quota eligibility is verified.

The search router must record provider, query, timestamp, status, response headers, source URL and evidence tier. Discovery never becomes extraction permission. Provider scores never become truth scores.

## Search invariants

Static provider metadata is descriptive only. Runtime HTTP status, response headers, account state and source policy are authoritative.

The system must distinguish:
- blocked;
- rate-limited;
- quota exhausted;
- transport failure;
- temporary provider failure;
- healthy;
- intermittent.

The router should learn these states from runtime observations and adapt the next route.

## Migration method

Every migration follows:

Python baseline
  -> golden corpus and contract tests
  -> shadow implementation
  -> semantic equivalence
  -> performance and memory benchmark
  -> failure injection
  -> shadow/canary
  -> promotion receipt
  -> production cutover
  -> rollback path retained

No production component is deleted before its replacement passes the same contract and failure matrix.

## First migration lanes

1. TypeScript public Worker shadow implementation.
2. Rust URL identity and deduplication pilot.
3. TypeScript Playwright/browser benchmark runner.
4. Go high-concurrency benchmark runner.
5. Python remains canonical for research policy, evidence reasoning and private control-plane contracts.

## Acceptance metrics

A migration is accepted only if it improves at least one real-project metric:
- p50/p95 latency;
- CPU time;
- memory peak;
- throughput;
- startup/steady-state cost;
- failure rate;
- dependency availability;
- operational complexity.

A faster microbenchmark that increases memory, failure rate, security risk or deployment complexity is not an improvement.
