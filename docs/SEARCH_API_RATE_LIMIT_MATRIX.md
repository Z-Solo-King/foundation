# Search API / Rate-Limit Matrix — September 2026

## Purpose

This is the project source-of-truth for web-search API planning. Static pricing/quota data is **not** treated as proof of runtime availability. The search router must use the provider's live response status and rate-limit headers when available.

Checked: **2026-09-20**

## First-party verified

| Provider | Current free / low-cost offer | Capacity / limit reference | Runtime handling |
| --- | --- | --- | --- |
| Brave Search | $5 free credits every month on each plan; Search is $5/1,000 requests | Search capacity: 50 req/s | Read `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Policy`; defer on 429/remaining=0 |
| Tavily | 1,000 API credits/month, no card | Development 100 RPM; Production 1,000 RPM; Research create 20 RPM; Crawl 100 RPM | Honor 429 and `Retry-After`; credit consumption differs by endpoint |
| Serper | 2,500 free queries | Starter reference: 50 QPS | Treat live response/account state as authoritative |
| Exa | $20 signup credits + $10/month | Starter 10 QPS; Developer up to 25 QPS | Treat runtime response/account state as authoritative |
| SerpAPI | Free: 250 searches/month | Free 50/hour; Starter 200/hour | Separate monthly quota from hourly throughput |
| Jina Reader | 20 RPM without key; 500 RPM free API key | RPM + TPM; per IP/API key | Use live limit/rate responses; key changes the accounting identity |
| Jina Search | Current service page shows 100 RPM with free API key | Premium reference 1,000 RPM | Search and Reader are separate endpoint families |
| Firecrawl | 1,000 credits/month, no card | Free plan: 2 concurrent requests; low rate limits | Treat concurrency/429/Retry-After as runtime authority |
| Google Custom Search JSON API | Existing customers only: 100/day free; then $5/1k | Existing customers only; max 10k/day | Do not route new customers; service discontinuation Jan 1, 2027 |
| Bing Search API | **Retired** Aug 11, 2025 | Not available | Never route; migration target is Grounding with Bing |

Sources:

- Brave: https://brave.com/search/api/ and https://api-dashboard.search.brave.com/documentation/guides/rate-limiting
- Tavily: https://docs.tavily.com/documentation/api-credits and https://docs.tavily.com/documentation/rate-limits
- Serper: https://serper.dev/
- Exa: https://exa.ai/pricing
- SerpAPI: https://serpapi.com/pricing
- Jina: https://jina.ai/reader/
- Firecrawl: https://www.firecrawl.dev/crawl
- Google: https://developers.google.com/custom-search/v1/overview
- Bing: https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement

## Grounding / model-native search

Model-native grounding should be a separate routing class from standalone SERP/search APIs.

Google's current Gemini pricing documentation lists **5,000 free Google Search grounding requests/month**, then **$14 per 1,000 requests** on the paid tier. A user request can result in multiple underlying searches, so request count is not necessarily one-to-one with model prompts.

OpenAI's current rate card lists **$10 per 1,000 web-search runs**, with search-content tokens billed separately at model rates.

Sources:

- Google Gemini: https://ai.google.dev/gemini-api/docs/pricing
- OpenAI: https://help.openai.com/en/articles/20001415

## What the router must do

### 1. Static catalog is advisory

A monthly free quota, published QPS, or pricing page must never by itself grant provider eligibility.

### 2. Runtime response is authoritative

Capture, when present:

- HTTP status;
- `Retry-After`;
- `X-RateLimit-Limit` / `RateLimit-Limit`;
- `X-RateLimit-Remaining` / `RateLimit-Remaining`;
- `X-RateLimit-Reset` / `RateLimit-Reset`;
- provider-specific rate-limit policy headers;
- endpoint family;
- timestamp;
- provider/account identity without exposing credentials.

### 3. Fallback semantics

- **Healthy + known remaining capacity:** eligible now.
- **429 / Retry-After:** defer until the provider says retry is appropriate.
- **remaining=0:** defer until reset when known.
- **401:** credential/auth failure; do not retry blindly.
- **403:** classify separately because it may mean account policy, region, bot/access control, or authorization—not automatically “quota”.
- **5xx:** bounded retry with deadline.
- **Retired/sunsetting provider:** reject from new routing.
- **Unknown live state:** allowed only when policy permits; lower confidence than an observed healthy provider.

### 4. API-level questions must use fresh research

Queries containing terms such as:

- rate limit
- quota
- requests per second/minute
- API pricing
- search API
- free tier

must route to fresh research rather than model knowledge.

## Community claims that are intentionally not source-of-truth

The project should **not** hard-code community claims such as:

- exact DuckDuckGo safe RPM;
- Bocha free-tier/QPS values;
- unofficial provider acquisition/pricing rumors;
- claims that a provider is “best” without a dated benchmark and defined population;
- vendor limits inferred from one user's account.

These can be stored as candidate observations, but runtime routing must rely on authoritative provider responses and first-party documentation where available.

## Architecture change

Operations now owns:

- `private/search_rate_limit.py` — normalized API-level telemetry;
- `private/search_provider_catalog.py` — first-party reference catalog;
- `private/search_route_policy.py` — live-capacity-aware admission/fallback policy.

The rule is:

> **Search-provider quotas are learned from the API response path; pricing pages are planning metadata, not runtime truth.**
