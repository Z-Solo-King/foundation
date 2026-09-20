# Hybrid Search and Runtime Policy — 2026-09-20

Foundation is public-safe deterministic infrastructure. It may expose typed capability contracts and edge adapters, but protected provider governance, resource budgets, evidence acceptance and private orchestration remain in Operations.

## Search contract

Search is a capability, not a single vendor.

Provider classes:
- direct search APIs;
- self-hosted metasearch;
- regional search;
- page extraction;
- crawl/extraction escalation.

The public contract should describe normalized search requests/responses and capability metadata. Provider API keys, quotas, private health state and admission policy remain in Operations.

Recommended provider families now tracked by Operations:
Brave, Tavily, Serper, Exa, You.com, Kagi, SearXNG, DuckDuckGo fallback, Bocha, Jina Reader, Firecrawl.

Retired or sunsetting dependencies must remain explicitly represented so routing can fail closed instead of silently falling back to obsolete APIs.

## Runtime/language policy

Cloudflare Workers is a polyglot platform supporting JavaScript, TypeScript, Python and Rust, with WebAssembly support for other languages. TypeScript is a first-class Worker language. Python Workers run via Pyodide/WebAssembly. Rust is available through workers-rs/Wasm. urlCloudflare language supporthttps://developers.cloudflare.com/workers/languages/

Use:
- TypeScript for new public edge/search-fanout/connector code when the task is mostly asynchronous I/O.
- Python for deterministic public contracts and algorithms already owned here.
- Rust/Wasm only for profiled CPU-bound hot paths where the measured improvement justifies binary/startup complexity.
- Go for optional long-running batch/connector workers outside the protected Worker policy boundary.
- PHP only for an existing PHP hosting/framework integration requirement, not as a blanket performance rewrite.

Python Workers have access to Cloudflare APIs through the Python FFI, so a wholesale rewrite is not justified merely because Python is different from TypeScript. urlCloudflare Python FFIhttps://developers.cloudflare.com/workers/languages/python/ffi/

## Migration gate

No language migration is promoted without:
1. deterministic compatibility fixtures;
2. representative load;
3. latency/throughput/memory measurements;
4. equal or stronger cancellation/failure semantics;
5. regression comparison against the current implementation;
6. preserved ownership boundaries.

The standard sequence is:
prototype -> benchmark -> shadow -> canary -> promote.

## Architecture invariant

Hybrid routing is expected.

Do not create a second mapper, policy owner, resource ledger, evidence authority, evaluator, deployment owner, or private search state inside Foundation.
