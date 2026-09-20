# Hybrid Language and Runtime Architecture
Last updated: 2026-09-20

Decision: this project is intentionally polyglot. A component changes language only when the target language gives a measurable advantage in platform fit, throughput or tail latency, memory, concurrency, safety, ecosystem access, portability, or deployment simplicity.

## Repository map
Operations is approximately 411 Python files and is dominated by Python Workers, extractor/mapper logic, provider routing, streaming, idempotency, resource governance and research control logic.
Foundation is approximately 271 Python files, 28 workflow files, 15 JavaScript frontend modules, 5 MJS modules and 10 SQL files.

## Workload-to-language decisions

| Workload | Current | Candidate | Decision |
| --- | --- | --- | --- |
| Cloudflare public Worker edge/router | Python | TypeScript | Migrate first |
| Cloudflare private Worker edge/router | Python | TypeScript | Migrate after public edge |
| Frontend state/UI | JavaScript | TypeScript | Migrate for type safety, not speed |
| Browser automation/acquisition | Python wrapper | TypeScript/Node | Strong candidate |
| Search-provider adapters | Python | TypeScript/Node | Strong candidate |
| Standalone high-concurrency HTTP acquisition | Python | Go | Benchmark candidate |
| DNS/DoH/native network hot paths | Python | Rust | Benchmark candidate |
| HTML parsing/normalization hot kernels | Python/lxml | Rust | Benchmark candidate |
| Product mapper | Python | Python | Keep until profiling proves CPU dominance |
| Evidence graph/claims/lineage | Python | Python | Keep |
| Research planning/adjudication | Python | Python | Keep |
| Provider cost/quota policy | Python | Python | Keep until contracts stabilize |
| Queue/idempotency/terminalization | Python | Python initially | Keep until semantics are frozen |
| Resource governance/maintenance | Python | Python | Keep |
| Benchmark scorecard/oracle | Python | Python | Keep |
| GitHub API automation | YAML + Python/shell | selective TypeScript | Migrate only complex clients |
| PHP | none | PHP | No current fit |
| Java/Kotlin | none | JVM | No current fit |
| C#/.NET | none | .NET | No current fit |
| Zig | none | Zig | Research only |
| C/C++ | none | C/C++ | No current fit |

## Why Python stays
Python is not being removed because it is generically slower. Most research, evidence, policy and provider work is dominated by network, database, model and correctness concerns. Python remains the better engineering tradeoff where its ecosystem and iteration speed matter more than raw CPU.

## Why TypeScript is first
Cloudflare documents TypeScript as a first-class Workers language with generated runtime types and native Web APIs. This is a platform-fit migration. TypeScript erases to JavaScript, so the primary benefits are typing, contract safety and less Python/Pyodide/FFI code at the edge rather than a generic performance claim.

## Why Rust is selective
Rust is reserved for proven CPU or memory hot paths such as HTML normalization, deterministic transformation kernels and possibly DNS/DoH. Rust adds memory safety and native/Wasm options without turning the whole research engine into a systems-language project.

## Why Go is selective
Go is a strong fit for standalone high-concurrency HTTP acquisition and benchmark workers because its goroutines, channels, bounded worker pools and standard HTTP transport map directly to that workload. It is not the first choice for Cloudflare Worker edge code because TypeScript has stronger native platform integration.

## Why PHP is not used
PHP has JIT support and can perform well in server workloads, but this repository has no PHP deployment or ecosystem advantage. Introducing PHP would add a runtime without addressing an identified bottleneck.

## Other languages
Java virtual threads are excellent for high-throughput blocking I/O, but there is no JVM target in the current architecture. Kotlin coroutines are strong for concurrency but add the same JVM ecosystem cost. C#/.NET Native AOT can reduce startup and memory footprint for standalone services, but adds another ecosystem. Zig gives low-level control but Rust already covers the justified systems-language use cases. C/C++ are reserved for cases where an existing native library has a decisive advantage.

## Migration sequence
1. TypeScript public Worker edge and request boundary.
2. TypeScript private Worker edge, SSE boundary and Service Binding/RPC contracts.
3. TypeScript frontend modules.
4. TypeScript browser and search adapters.
5. Benchmark Python versus Go for standalone HTTP fan-out.
6. Benchmark Python versus Rust for HTML normalization and DNS/DoH.
7. Migrate only measured winners.
8. Keep Python research/evidence/policy logic unless profiling or platform constraints prove a need to move it.

## Mandatory promotion gates
Every migration must prove contract parity, authorization/security parity, strict-zero-cost parity, evidence/provenance parity, deterministic replay, p50/p95/p99 latency, memory/RSS, error rate, startup/cold-start behavior, and rollback compatibility. New implementations must run in shadow mode before canary promotion.

## Search-provider architecture
Search adapters should be replaceable capabilities behind the existing policy and quota gate. Candidate families include Brave, Exa, Tavily, Serper, DuckDuckGo-derived sources, Firecrawl and future providers. The router should choose based on eligibility, health, quota, latency, evidence quality and task fit rather than hard-coded preference.

## Cross-language platform finding
Cloudflare now supports Python-to-JavaScript/TypeScript Worker RPC through Service Bindings. That makes an incremental architecture possible: move edge/runtime-sensitive code to TypeScript while leaving research semantics in Python until a measured migration is justified.

## References
https://developers.cloudflare.com/workers/languages/
https://developers.cloudflare.com/workers/languages/typescript/
https://developers.cloudflare.com/workers/languages/python/
https://developers.cloudflare.com/workers/languages/rust/
https://developers.cloudflare.com/changelog/post/2026-08-03-python-javascript-rpc/
https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/
https://doc.rust-lang.org/book/
https://go.dev/doc/effective_go
https://www.typescriptlang.org/docs/handbook/typescript-from-scratch
https://docs.python.org/3/library/asyncio-task.html
https://www.php.net/manual/en/opcache.configuration.php
https://docs.oracle.com/en/java/javase/26/core/virtual-threads.html
https://learn.microsoft.com/aspnet/core/fundamentals/native-aot
https://docs.deno.com/runtime/fundamentals/typescript/

Final rule: TypeScript at platform/web edges, Python for research/evidence/policy semantics, Rust for measured CPU/native kernels, and Go for measured standalone high-concurrency acquisition. Everything else remains evidence-driven.