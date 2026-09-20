# Polyglot Architecture & Migration Strategy — 2026-09-20

## Decision
Do not replace Python wholesale. Use a polyglot architecture by workload with stable contracts and measured migration.

Python remains the reference implementation for research/evaluation-heavy logic. TypeScript is the preferred first migration for Cloudflare Worker and web-provider boundary code. Rust is the candidate for CPU-heavy parsing/normalization after profiling. Go is the candidate for high-concurrency GitHub batch workers. Node.js is treated as a runtime for TypeScript, not a separate language strategy.

## Why change anything from Python?
Python is not being replaced because it is inherently unstable. Cloudflare now provides first-class Python Workers, but Python Workers execute through Pyodide/WebAssembly and have runtime differences including nonfunctional threading and multiprocessing in Workers. TypeScript is first-class on the native Workers runtime with generated Worker API types.
Therefore migration requires a measured workload advantage, not language fashion.

## Workload map
| Workload | Current | Preferred | Decision |
|---|---|---|---|
| Cloudflare public/private Worker HTTP boundary | Python | TypeScript | First migration target |
| Search-provider HTTP adapters | Python metadata | TypeScript | First adapter implementation target |
| Playwright/browser execution | Python | TypeScript/Node.js | Migrate after contract parity |
| Research orchestration | Python | Python | Keep |
| Research adjudication/evidence policy | Python | Python | Keep |
| Token accounting/evaluation | Python | Python | Keep |
| HTML parsing/normalization hot path | Python+lxml | Rust candidate | Only after profiler proves CPU bottleneck |
| High-concurrency GitHub batch workers | Python | Go candidate | Only after throughput bottleneck is measured |
| GitHub Actions reusable automation | YAML/Python | TypeScript/Node where useful | Selective |
| PHP | None | Do not adopt | No current workload fit |
| Java/Kotlin | None | Do not adopt | JVM overhead/benefit mismatch for current system |
| C++ | None | Do not adopt | Unnecessary complexity without native-library need |
| Zig | None | Experimental only | Not justified for core services |

## Migration gates
1. Freeze contract/schema and golden vectors.
2. Implement candidate behind the same contract.
3. Differential-test candidate against Python reference.
4. Measure p50/p95 latency, CPU, memory, startup, throughput and failure semantics.
5. Verify security/provenance/idempotency/replay parity.
6. Shadow/canary before promotion.
7. Keep immediate rollback to Python until stability is proven.

## Search architecture
The current Operations catalog already includes Brave, Tavily, Serper, Exa, SerpAPI, Jina Reader/Search, Firecrawl, DuckDuckGo, SearXNG, You.com, Kagi, Bocha, Parallel, OpenAI web search and Gemini Google Search. Bing Search API is explicitly retired and legacy Google CSE is marked sunsetting.
Important: catalog presence is not adapter presence. The next implementation step is first-class provider transports behind one normalized search contract.

## Provider role split
- General: Brave, Tavily, Serper.
- Deep/semantic research: Exa, Parallel, Tavily.
- Chinese web: Bocha, SearXNG, Tavily.
- Page retrieval: Jina Reader, Firecrawl.
- Zero-cost/private fallback: SearXNG, bounded DuckDuckGo.
- Model-native grounding: Gemini, OpenAI when account policy permits.

## Current benchmark strategy
Use parallel jobs only when each job answers a different question. The project now has a site-extraction matrix plus an orthogonal 20-scenario runtime matrix. Never spend 20 jobs repeating the same happy path.

## 2026-09-20 implementation status

- L1 now has a Phase B TypeScript shadow at `polyglot/edge-worker/`.
- The shadow covers the current public route matrix, authentication header extraction, authenticated JSON cache policy, SSE response headers, bounded response sizing, and deterministic chat SSE framing.
- The TypeScript shadow is contract-only: it does not own authentication secrets, D1 admission, resource governance, private service bindings, research persistence, or production deployment.
- Foundation GitHub Actions now runs the L1 shadow typecheck/tests alongside the Rust/Go/L3 pilot lanes.
- Production routing remains Python. Promotion still requires differential fixtures, negative/error-path parity, and measured latency/CPU/memory evidence.
