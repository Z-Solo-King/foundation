# Search Provider Execution Matrix — 2026-09-20

## Current implementation
Operations has a provider catalog, capability registry, runtime rate-limit telemetry and intent-aware route policy. The catalog is broader than the set of currently implemented first-class transports.

| Provider | Role | Priority |
|---|---|---|
| Brave | General web discovery | P0 |
| Tavily | Agent/RAG research | P0 |
| SearXNG | Metasearch/zero-cost/private fallback | P0 |
| Bocha | Chinese web | P0 |
| Jina Reader | Page retrieval | P0 |
| Serper | Google SERP | P1 |
| Exa | Semantic discovery | P1 |
| Parallel | Deep research/search | P1 |
| Gemini Google Search | Model grounding | P1 |
| OpenAI web search | Model grounding | P1 |
| Firecrawl | Search + extraction | P2 |
| You.com | General search | P2 |
| SerpAPI | SERP | P2 |
| DuckDuckGo | Bounded fallback | P2 |
| Kagi | Premium search | P3 |
| Bing Search API | Retired | REMOVE |
| Legacy Google CSE | Sunsetting | REMOVE/legacy |

## Adapter contract
Every real adapter must implement: request normalization, search result normalization, provenance, rate-limit observation, latency, retry-after, raw-response digest and deterministic normalization version.

## Routing rules
Use provider capability and intent first, then live runtime state. Static quota/reference data is advisory only. A provider must never be admitted solely because the catalog says it has free capacity.

Provider diversity improves discovery, not truth. Evidence quality still depends on primary-source preference, source independence, freshness, entailment, conflict checks and provenance.
