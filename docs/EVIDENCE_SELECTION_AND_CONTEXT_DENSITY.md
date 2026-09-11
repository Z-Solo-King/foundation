# Evidence Selection and Context Density

## Scope

Foundation owns public-safe evidence primitives. It does not own private provider policy, resource accounting, promotion, or protected execution. The deterministic selector added in `backend/evidence_selection.py` provides a reusable way to reduce repeated evidence before an AI-facing context envelope is built.

## Design

The selector uses explicit caller-supplied scores rather than pretending to know trust policy itself:

- `source_rank` represents the caller's already-established evidence role ordering;
- `relevance_score` represents task-specific usefulness;
- `claim_key` groups semantically equivalent claims;
- `estimated_tokens` allows callers with exact tokenizer knowledge to override the public neutral estimate.

It removes duplicate claim text, orders candidates deterministically, and stops at `max_items` or `max_tokens`.

## Why this pattern matters

Scrapy separates scheduling, downloading, middleware, and item pipelines instead of embedding site-specific work into one crawler component. LangGraph uses persistent checkpoints so long-running state can resume without replaying completed work. vLLM and Cloudflare emphasize prefix reuse/caching to avoid repeating common prompt computation. These systems share a useful architectural principle: separate planning/state from execution, make repeated work reusable, and make bounded resource use explicit.

## Safety

The selector never rewrites an observation, declares a source authoritative, or drops a claim because it is unusual. It only selects what fits a declared budget. The caller remains responsible for evidence authority and contradiction policy.

## External references

- Scrapy architecture: https://github.com/scrapy/scrapy/blob/master/docs/topics/architecture.rst
- LangGraph persistence: https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx
- vLLM automatic prefix caching: https://github.com/vllm-project/vllm/blob/main/docs/features/automatic_prefix_caching.md
- Cloudflare Workers AI prompt caching: https://developers.cloudflare.com/workers-ai/features/prompt-caching/
