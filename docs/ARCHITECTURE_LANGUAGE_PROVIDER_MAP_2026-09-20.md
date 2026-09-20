# Research Intelligence Engine — Language & Provider Architecture Map
Date: 2026-09-20

## Executive decision

Do not rewrite Python wholesale.

The project should become a hybrid runtime in which each subsystem uses the language/runtime that best matches its constraints, while all subsystems preserve the existing canonical contracts, provenance, idempotency, authorization, zero-cost policy, and promotion gates.

## Target language allocation

| Subsystem | Current | Target / candidate | Decision | Why |
|---|---|---|---|---|
| Public Cloudflare Worker edge/router | Python Worker / Pyodide | TypeScript | Migrate first | Cloudflare Workers is natively V8/web-standard JS; TypeScript is first-class and fully typed. Python executes through Pyodide. |
| Public Worker hot parser/validator | Python | TypeScript first; Rust/Wasm only for measured hot loops | TS first | Worker Request/Response/Streams/Web Crypto/HTMLRewriter are native APIs. |
| Private chatbot / research orchestration | Python | Python | Keep | Policy-heavy, AI SDK rich, already tested, no proven bottleneck. |
| Evidence selection / truth-policy logic | Python | Python | Keep | Deterministic logic; correctness dominates runtime. |
| Provider admission / quota / billing policy | Python | Python | Keep initially | Auditability and policy correctness dominate. |
| Search-provider adapters | Python private side + TS edge adapters | Hybrid | Use per execution boundary | Provider policy remains centralized; edge-compatible calls can stay native to Worker. |
| HTTP acquisition / fetch fan-out | Python | Rust or Go after profiling | Benchmark first | Strong candidate if CPU, memory, or concurrency becomes the bottleneck. |
| HTML / structured-data extraction | Python | Rust candidate | Benchmark first | Best candidate for memory-safe, CPU-efficient parsing. |
| Browser acquisition | Python/Playwright | TS/Playwright or Python/Playwright | Do not rewrite yet | Browser time is dominated by Chromium/network behavior. |
| Durable idempotency / replay / terminalization | Python | Rust/Go only if contention is measured | Keep now | D1 semantics and correctness matter more than raw runtime speed. |
| Resource governance / maintenance | Python | Python | Keep | Mostly state/policy orchestration. |
| Standalone network service | N/A | Go | Candidate | Good fit for long-lived, highly concurrent network service if one becomes necessary. |
| Specialized native/Wasm parser | N/A | Rust | Candidate | Memory safety, predictable performance, small explicit boundary. |
| PHP | N/A | PHP | Do not introduce | No workload or ecosystem fit that justifies another runtime. |
| Java/Kotlin | N/A | Kotlin/Java | Do not introduce initially | Strong concurrency tools, but no current problem justifies JVM migration. |
| C/C++ | N/A | C/C++ | Do not introduce initially | Useful for specialized native dependencies, but unnecessary maintenance/safety cost. |

## Why not replace Python everywhere?

A language migration is justified only when the candidate improves a measured system bottleneck after migration cost is included.

For this project, much of the latency is external I/O, provider/network waiting, browser execution, model services, or Cloudflare bindings. Rewriting policy code simply because another language benchmarks faster in a microbenchmark would add complexity without proving system-level value.

The first migration is therefore the public Worker edge/router. Cloudflare documents TypeScript as first-class on Workers, while Python Workers execute through Pyodide. The Worker runtime itself is based on V8 and web-standard APIs.

Private Python remains the default until a component-specific benchmark proves otherwise.

## Search/provider architecture

The architecture should treat search as a replaceable capability, not one hard-coded provider.

| Provider | Role | Status | Intended use |
|---|---|---|---|
| SearXNG | self-hosted metasearch | Add | No-key aggregation through an owned/approved instance. |
| DuckDuckGo | keyless fallback | Add | Cached/low-volume fallback only due rate-limit/CAPTCHA risk. |
| Jina Reader | URL retrieval/normalization | Add | Convert known result URLs into clean research content. |
| Tavily | agent-oriented search | Add | High-value search when free credits/quota are available. |
| Exa | semantic/web research | Add | Research/discovery and semantic retrieval. |
| Brave Search | independent index | Add | Index diversity and independent evidence path. |
| Serper | Google SERP | Add | Cheap raw SERP path where policy permits. |
| SerpAPI | structured SERP | Add | Secondary SERP parsing/verification lane. |
| Bocha | Chinese/localized search | Add | Chinese-language retrieval with explicit policy/quota handling. |
| Perplexity Sonar | model-native search/citations | Candidate | Use when model synthesis and citation retrieval can be combined economically. |
| Gemini + Google Search grounding | model-native grounding | Candidate | Use where Gemini routing already exists and billing policy permits. |
| OpenAI Responses web search | model-native grounding | Candidate | Use when OpenAI routing already exists and cost policy permits. |
| Firecrawl | deep extraction | Candidate | Page crawl/extraction, not primary discovery. |
| Linkup / Parallel | premium research | Candidate | Only where a measurable quality requirement justifies cost. |

### Provider contract

Every provider adapter must expose:
- eligibility;
- billing state;
- quota remaining;
- rate-limit state;
- expected cost;
- source-policy requirements;
- failure class;
- cooldown/retry policy;
- evidence-quality metrics.

The router chooses the next eligible capability, not the next provider name.

### Recommended zero-cost-first ladder

owned SearXNG -> cached DuckDuckGo -> Jina Reader -> eligible free search API -> paid provider only when explicitly authorized

Provider diversity increases evidence diversity; it does not prove truth.

## Nightly research changes

Recent nightly artifacts showed several recurring target classes:

- stable HTTP 429: exponential backoff + quarantine;
- stable HTTP 403: source-specific blocked state, no repeated aggressive retries;
- transport/URL failures: distinct class requiring network/URL diagnosis;
- intermittent sources: controlled recheck, not permanent quarantine;
- healthy source: repeated successful observations, not one success.

The benchmark should therefore persist a target-health class and recommended action.

## Migration rule

Every language migration follows:

baseline
-> shadow implementation
-> contract comparison
-> performance benchmark
-> fault-injection benchmark
-> security/authorization benchmark
-> canary
-> production
-> automatic rollback on regression

A language change without a measured baseline is not accepted as a performance improvement.

## Research references

Cloudflare runtime:
- https://developers.cloudflare.com/workers/languages/
- https://developers.cloudflare.com/workers/languages/typescript/
- https://developers.cloudflare.com/workers/languages/python/
- https://developers.cloudflare.com/workers/languages/python/how-python-workers-work/
- https://developers.cloudflare.com/workers/languages/rust/
- https://developers.cloudflare.com/workers/runtime-apis/webassembly/

Languages:
- https://doc.rust-lang.org/book/ch16-00-concurrency.html
- https://tokio.rs/tokio/tutorial
- https://go.dev/doc/faq
- https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop
- https://www.typescriptlang.org/docs/handbook/typescript-from-scratch
- https://www.php.net/manual/en/book.opcache.php
- https://openjdk.org/jeps/444
- https://kotlinlang.org/docs/coroutines-overview.html

Search:
- https://docs.searxng.org/
- https://www.tavily.com/pricing
- https://exa.ai/pricing
- https://brave.com/search/api/
- https://jina.ai/en-US/reader/
- https://serpapi.com/pricing
- https://ai.google.dev/gemini-api/docs/google-search

## Implementation phases

### Phase A — TypeScript edge shadow
Implement a TypeScript Worker matching the exact public Worker contract. Run it in shadow against the Python Worker.

### Phase B — Rust parser prototype
Extract only the profiled CPU-heavy extractor/parser path behind the existing contract.

### Phase C — Search adapters
Implement provider modules with one capability/eligibility/quota contract.

### Phase D — Promotion
Promote only components that beat the frozen Python baseline on the relevant latency, memory, CPU, reliability and defect slices.
