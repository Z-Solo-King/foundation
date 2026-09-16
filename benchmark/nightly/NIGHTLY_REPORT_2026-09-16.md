# Nightly Research Intelligence Engine Report — 2026-09-16

## Evidence boundary

This report distinguishes repository/source inspection from live execution. No Cloudflare production control, secret, billing setting, protected policy/security authority, or external production control was modified. No hidden chain-of-thought is collected or used.

## Current revisions verified

- Foundation `main`: `f9035bb390df9f0b2fb7d630a877be4a0683dc73` (2026-09-16 18:24:18 UTC).
- Operations `main`: `a2dcb069a680de2ad6490ac5e5092d14ca81eb03` (2026-09-16 16:54:34 UTC).
- Operations production-approved revision remains separate from current `main`; repository source must not be treated as production certification.

## Previous-night / current failure replay

### Reproduced or verified gaps

1. The nightly multi-agent workflow currently has **3 GitHub research jobs**, not 19 independent jobs. Their internal capacity values are 6 + 6 + 8 = **20 worker capacity**. Each lane currently validates 8 programs, for **24 programs total**.
2. Each lane has a 380-minute timeout. This is below the six-hour GitHub Actions ceiling but is too close to the ceiling for efficient nightly diagnostics.
3. The workflow pins a private Operations revision. Current Operations `main` is newer than the pinned research revision, so a current-main nightly run is not automatic until the pin is deliberately advanced through normal review.
4. The workflow has an explicit live preflight and refuses to silently convert missing LLM configuration into a successful dry run.
5. Incomplete/blocked runs are intentionally prevented from producing a complete-live project-improvement summary.
6. The project currently has a known GitHub Actions main-push zero-job startup blocker tracked by Foundation issue #246. Source inspection is therefore not sufficient to claim production workflow certification.
7. Guest Test UI behavior is explicitly test-only and cannot be promoted to production runtime evidence.
8. The backup workflow now contains real remote-restore verification logic, but repository source inspection is not evidence that the latest scheduled backup succeeded.

## 20-job capacity assessment

**Status: not safely expandable to 19+1 research jobs from the current private runner contract.** The current runner interface is lane-based and the workflow has 3 lanes with 8 programs each. Blindly changing the matrix to 19 lanes would duplicate or invalidate the runner's program contract rather than create 19 materially independent experiments. No such unsafe change was made.

The correct next implementation is an explicit experiment dispatcher whose program IDs, query family, corpus, agent budget, method cascade and resource budget are part of a versioned contract. Only then should a 19-research-job + 1-aggregator workflow be promoted.

## Query and benchmark coverage

The current query corpus contains 17 research queries spanning buying guides, best-product selection, deep hardware investigation, temporal reconciliation, review forensics, cross-source comparison, social evidence, Chinese communities, smartphones, PC builds, Hinglish, follow-ups, seller-vs-product separation, hardware revisions, warranty/service, trends and restricted-evidence discovery.

This is materially broader than a single generic prompt, but it does not itself prove that all queries were live-executed against all requested source families.

The public benchmark target corpus contains 20 India-oriented retailer/vendor URLs. Its current runner performs bounded HTTP retrieval with retries, timeout and response-size limits and classifies blocked, rate-limited, error and empty results. It parses HTML titles and JSON-LD/product hints. It does not yet constitute a full implementation of XHR/Fetch/Axios interception, browser execution, visual image evidence, or authenticated/restricted-source acquisition.

## Real current public research findings

### AI assistant ecosystem

- **Grok/xAI:** xAI's current X Search tool supports keyword search, semantic search, user search and thread fetch. xAI documents token types including input, reasoning, completion, image and cached prompt tokens. X Search pricing is scheduled to change on 2026-09-21 to $5 per 1,000 posts and $10 per 1,000 user profiles fetched. This makes tool-call economics a first-class metric rather than only token cost.
- **Gemini:** Google's current Gemini API pricing page lists Gemini 3.7 Flash with free-tier availability and paid token pricing; Google's Deep Research product explicitly covers planning, searching, reasoning, analysis and reporting and is available across web/mobile contexts depending on account/product eligibility.
- **DeepSeek:** current DeepSeek documentation states that the legacy V4 Flash name is served by V4.1 Flash, and that V4 Pro requests are being routed to V4.1 Flash after 2026-09-14 until V4.1 Pro is released. Current published Flash pricing is substantially below frontier API pricing, with cache-hit pricing materially below cache-miss pricing. This is strong evidence for testing cache-aware routing and time-window-aware scheduling, but not a justification to purchase paid usage under the strict-$0 project policy.
- **Perplexity:** current Agent API documentation exposes exact token counts in API responses and tiered RPM limits; this is directly useful for token/evidence economics instrumentation.
- **Brave Leo:** Brave documents free access, optional premium higher limits, web/document/PDF summarization, multilingual assistance, coding help, and local-device chat history. Brave states that Leo conversations are not retained for model training. This is a strong privacy-boundary reference for the project but not evidence that Leo is superior for research quality.
- **Claude:** Anthropic's current Sonnet 5 announcement states $2/M input and $10/M output as permanent introductory pricing and describes higher-effort levels and long-running coding/research usage. Sonnet 4.6 previously introduced a 1M-token context beta. Vendor performance claims remain vendor claims and require independent paired tests before promotion.
- **Meta AI:** Meta documents Meta AI as free for everyday use, with usage limits for compute-intensive features, multimodal capability, real-time web information and integration across Meta products. Meta's April 2026 Muse Spark announcement describes a focus on citations for recommendations/content. These capabilities are relevant to multimodal/social-source research but have not been independently benchmarked here.
- **ChatGPT:** OpenAI's current public pricing page advertises web search and limited deep research on the free tier. OpenAI's enterprise token rate card exposes deep-research token pricing. These are product/pricing facts, not evidence of comparative quality superiority.
- **GitHub Copilot:** current GitHub pricing lists Free, Pro, Pro+, and Max tiers, AI-credit accounting, agent mode, cloud agent, code review, CLI, MCP integration and access to multiple third-party/frontier models. Copilot is therefore a relevant coding workflow comparator, not an independent research-quality oracle.

### VCS / DevOps platform evidence

- GitHub Actions standard GitHub-hosted runners are free for public repositories; private repositories have plan-dependent minute/storage allowances. Current GitHub documentation confirms Actions supports matrices, hosted/self-hosted runners and concurrency controls.
- GitLab Free currently lists 5 users per top-level group, 400 compute minutes/month and SCM/CI/CD/security features. Premium lists 10,000 compute minutes/month and Ultimate 50,000.
- Bitbucket Pipelines currently lists 50 free minutes/month and up to 10 concurrent steps on Free; Standard/Premium provide larger minute pools and additional governance. Bitbucket is tightly integrated with Jira.
- Azure DevOps currently provides one free Microsoft-hosted parallel job with 1,800 minutes/month plus one free self-hosted parallel job with unlimited minutes; public open-source projects have a more generous Azure Pipelines allowance.
- Open-source LLM gateway research identified current examples of semantic routing, health-aware failover and token/latency metrics. These ideas are candidates for Operations' provider-runtime layer, but no alternate deployment/control-plane authority should be introduced.

## Acquisition / evidence integrity conclusions

The current architecture correctly treats source claims as observations until qualification. New research must preserve:

`source -> retrieval method -> observation -> identity/variant mapping -> evidence receipt -> independence/contradiction check -> synthesis`

Copied or syndicated claims must not receive independent-source credit merely because URLs differ. Seller/delivery complaints must not be attributed to product defects without classification evidence. Old revisions must not be merged with current variants. Prompt-injected page content must remain untrusted content, never an instruction to the agent.

Recent research literature reinforces the value of explicit evidence lineage. LineageRAG reports demand-conditioned evidence lineages with source grounding; RepoTrace demonstrates browser-assisted provenance capture for GitHub research datasets; graph-vector and evidence-graph systems provide useful patterns for linking claims to sources and revisions. These are improvement candidates, not automatically validated project architecture.

## Token/context/resource economics

The repository now has explicit structures for input/output/cached/thinking-token accounting, tool-call counts, duplicate work and context peaks. The remaining runtime gap is actual provider telemetry for every supported provider. Estimated token counts must remain labeled as estimates.

A useful nightly metric set is:

- quality score / 1k input+output tokens;
- qualified evidence items / tool call;
- independent evidence gain / web request;
- duplicate-call rate;
- blocked-call rate;
- context peak and compaction count;
- wall-clock seconds per qualified answer;
- useful parallelism vs total parallelism;
- incremental quality from 1 -> 2 -> 4 -> 8 -> 10 agents.

No paid-provider measurement should be claimed as strict-$0 project execution unless the execution route is genuinely free and current eligibility is independently verified.

## Scaling conclusion

The project should not assume 10 agents are better than 4. The correct paired experiment is the same fixed task/corpus at 1, 2, 4, 8 and 10 agents, with identical stopping and evidence qualification. Promotion requires repeated held-out trials and an effect-size/confidence interval, not one successful run.

## UI/chatbot conclusion

Repository contracts cover authenticated chat, SSE streaming, deterministic context compaction, idempotency and Guest Test. Visible UI behavior remains a separate acceptance layer. In particular, source inspection cannot prove reconnect, refresh continuity, mobile layout, keyboard accessibility, concurrent queue/FIFO behavior or long-running lifecycle behavior.

## Verified improvement candidates

1. Advance the nightly Operations pin only through an explicit reviewed change after validating the current-main research contract.
2. Introduce a versioned experiment dispatcher instead of abusing lane IDs to simulate 19 independent experiments.
3. Make experiment identity include corpus/query family/agent budget/method strategy/resource budget so duplicated work is detectable.
4. Preserve exact provider usage metadata whenever available and label estimates otherwise.
5. Add source-family independence scoring and common-origin detection before evidence aggregation.
6. Add revision-aware product identity fixtures and seller-vs-product complaint fixtures to the held-out benchmark.
7. Add browser/UI lifecycle tests as a distinct evidence class instead of treating frontend source inspection as runtime evidence.
8. Keep all model/chat learning signals candidate-only and incapable of modifying protected authority.

## Blocked / not claimed

- No current 19+1 live experiment execution was fabricated.
- No production Cloudflare success was inferred.
- No B2 restore success was inferred from workflow source alone.
- No current production chatbot end-to-end proof was inferred from Guest Test.
- No model superiority claim was promoted from vendor benchmarks or anecdotes.
- No paid-provider execution was performed merely to manufacture cost/quality data.

## Next-night highest-information experiments

1. Execute a versioned 19-program dispatcher against the same fixed corpora with agent budgets 1/2/4/6/7/8/10 distributed across paired tasks.
2. Run held-out contradiction/revision/poisoning fixtures.
3. Capture real provider token metadata where the configured executor exposes it.
4. Run a deterministic HTTP acquisition matrix against the 20 current India-oriented targets and classify HTML/JSON-LD/empty/blocked/rate-limited/error outcomes.
5. Add one browser-permitted source fixture for lazy images and embedded state without bypassing access controls.
6. Compare the current main Operations revision against the pinned research revision before promotion.
7. Run the UI guest-test contract plus visible browser lifecycle tests when a browser-capable CI path is available.
