# Heroic AI — Third-Party Repository Deep Coverage — 2026-10-01

## Scope and method

This document is the durable deep-review record for the 19 repositories supplied for Heroic AI architecture research. The fresh pass checked each repository's current default branch through GitHub, repository tree/top-level structure, primary README/docs, major runtime/source directories, tests/CI or skills where present, and relevant licensing signals. Public web research was cross-checked for current capabilities and important licensing changes.

Covered means the useful architectural or operational capability was identified and mapped to an existing Heroic surface or documented as a candidate. It does not mean every historical commit or every source line was copied. External repositories are references, not runtime authorities.

Foundation remains the public-safe deterministic contract/deployment authority. Operations remains the private chatbot/provider/resource/acquisition/extraction/research authority.

## 1. SearchJumper

Observed: configurable search-engine rules, URL templates and transforms, keyword filters, selection/image/link/find-in-page actions, right-click/menu/shortcut flows, React UI and JSON schema.
Heroic mapping: provider/search routing and public search parsing.
Gap: no dedicated SearchDefinition DSL/validator is promoted.
Action: candidate declarative search-definition layer; do not copy GPL implementation.
Source: https://github.com/hoothin/SearchJumper
License: GPL-3.0.

## 2. Agent-Reach

Observed: 16-platform channel registry, ordered primary/fallback backends, real backend health checks, doctor JSON, install/config separation, platform references, skills, MCP integration and credential/security tests.
Heroic mapping: source access profiles, route health and browser/public-source policy.
Gap: no single doctor report that summarizes every acquisition backend.
Action: candidate source-backend doctor using existing route/profile state; no implicit install or credential discovery.
Source: https://github.com/Panniantong/Agent-Reach
License: MIT.

## 3. Patchright Enhanced

Observed: TypeScript browser wrapper, browser/start/config/session/type/util layers and session-oriented runtime.
Heroic mapping: BrowserAcquisitionClient, browser session pool and browser benchmark.
Gap: its implementation is not required.
Action: lifecycle/config patterns only; no bypass or unreviewed source reuse.
Source: https://github.com/whaleyxbt/patchright-enhanced
License status: no root LICENSE observed in the inspected tree.

## 4. Scrapling

Observed: adaptive element tracking and relocation, flexible selectors, fetchers/spiders, multi-session HTTP/browser routing, concurrency and per-domain throttling, AutoThrottle and 429 handling, pause/resume, streaming, cache/replay, robots, DNS-over-HTTPS, XHR/fetch capture, remote CDP, exports, MCP server, agent skill and RAG-oriented Markdown.
Heroic mapping: adaptive extractor, browser XHR capture, SPA/public-endpoint discovery, robots/sitemaps, cache validators, Markdown fallback and browser/session management.
Gap: no single unified AutoThrottle/streaming/monitor facade.
Action: extend only where measured and policy-safe.
Source: https://github.com/D4Vinci/Scrapling
License: reuse requires independent license verification; architecture patterns are preferred.

## 5. ComfyUI

Observed: graph/node execution, execution queues, API/OpenAPI, custom nodes/plugins, model-path/config management, execution/resource controls and extensive tests.
Heroic mapping: capability graph, resource governance and future generation job configuration.
Gap: no need for a visual node runtime in the chatbot.
Action: workflow/resource pattern only; no GPLv3 source import.
Source: https://github.com/Comfy-Org/ComfyUI
License: GPL-3.0.

## 6. Wan2.1

Observed: text-to-video, image-to-video, reusable inference pipelines, configuration-driven generation and resource-oriented deployment guidance.
Heroic mapping: future video capability/resource profiles.
Gap: heavyweight local model runtime is outside the current GitHub/Cloudflare low-cost control plane.
Action: retain reproducibility, offload and resource-profile patterns.
Source: https://github.com/Wan-Video/Wan2.1
License: repository and model terms must be checked separately per asset.

## 7. HunyuanVideo

Observed: large-scale video generation, image/video conditioning, single-GPU and multi-GPU paths, xDiT and FP8 efficiency work.
Heroic mapping: future model/resource profiles.
Gap: licensing and deployment restrictions prevent assuming production eligibility.
Action: research only until dedicated legal/product review.
Source: https://github.com/Tencent-Hunyuan/HunyuanVideo
License risk: Tencent Hunyuan Community License includes territory and distribution conditions and prohibits using Tencent Hunyuan outputs to improve another AI model; the current license also states the agreement does not apply in the EU, UK and South Korea.

## 8. FLUX

Observed: text-to-image, Fill, Canny, Depth, Redux, Kontext, Krea, TensorRT support, API usage tracking and model-specific licensing.
Heroic mapping: future image generation/editing capability profiles and license-aware model routing.
Gap: code, weights and commercial API terms are different policy surfaces.
Action: create model registry entries only after exact model-license validation.
Source: https://github.com/black-forest-labs/flux
License note: FLUX.1 schnell is Apache-2.0; several development/editing/conditioning models use the FLUX.1-dev non-commercial license.

## 9. AudioCraft

Observed: MusicGen, AudioGen, EnCodec, Multi Band Diffusion, MAGNeT, AudioSeal, MusicGen Style and JASCO, with modular training/inference and configuration.
Heroic mapping: future audio model registry, watermark/provenance and task/model separation.
Gap: weights have different terms from the code.
Action: code license and weight license must be independent policy entries.
Source: https://github.com/facebookresearch/audiocraft
License: MIT code; CC-BY-NC 4.0 weights.

## 10. ACE-Step

Observed: music foundation model, fast generation, memory optimization, CPU offload and overlapped decode, audio-to-audio, singing/accompaniment, voice cloning/editing, multilingual support and ComfyUI integration.
Heroic mapping: future low-resource audio capability profiles and resource envelopes.
Gap: no current production audio runtime.
Action: retain low-resource and reproducibility patterns; verify exact model checkpoint terms before deployment.
Source: https://github.com/ace-step/ACE-Step
License: current project documentation indicates MIT; checkpoint terms must be separately validated.

## 11. Chatterbox

Observed: Multilingual V3, Turbo, Nano, 23-plus language support, voice cloning, single-language packs, expressive tags and PerTh watermarking.
Heroic mapping: future TTS capability registry, low-latency model selection and audio provenance.
Gap: watermark-aware generation is not a promoted production capability.
Action: future audio generation must preserve watermark/provenance metadata.
Source: https://github.com/resemble-ai/chatterbox
License: MIT repository; model-specific terms still tracked separately.

## 12. Open-Sora

Observed: 11B Open-Sora 2.0, T2V/I2V, prompt refinement, motion score, reproducible seed, offload, 1/8-GPU execution and explicit resource/evaluation measurements.
Heroic mapping: reproducibility contracts, video job resource profiles and evaluation.
Gap: heavyweight GPU runtime does not fit current low-cost Workers runtime.
Action: keep configuration/resource/evaluation patterns.
Source: https://github.com/hpcaitech/Open-Sora
License: Apache-2.0 with separate dependency/model notices.

## 13. Stable Audio Tools

Observed: training/inference separation, JSON model/runtime/dataset configs, uv reproducibility, Flash Attention, DDP/DeepSpeed and explicit precision/GPU/data-loader controls.
Heroic mapping: future model profiles and reproducible job configuration.
Gap: no heavyweight audio runtime is active in the chatbot.
Action: use configuration and reproducibility patterns only.
Source: https://github.com/Stability-AI/stable-audio-tools
License: MIT.

## 14. Wan2GP

Observed: low-VRAM execution, quantization variants, CPU offload, KV cache, JIT checkpoint loading, job queue, headless/API use, workspaces, cancellation and offline agent workflows.
Heroic mapping: resource profiles, lazy model loading and job lifecycle.
Gap: its Community License restricts paid hosted/API/SaaS/OEM exposure of the WanGP software itself.
Action: architecture reference only until licensing is cleared.
Source: https://github.com/deepbeepmeep/Wan2GP
License: WanGP Community License 2.0.

## 15. Firecrawl

Observed: scrape, search, interact, map and crawl surfaces; CLI; MCP; skills; workflow skills; self-hosting.
Heroic mapping: task decomposition, scrape-versus-search-versus-interact routing and skills/workflow architecture.
Gap: strict-zero-cost and copyleft constraints rule out an automatic hosted dependency.
Action: architecture reference only; no source import.
Source: https://github.com/firecrawl/firecrawl
License: AGPL-3.0 for the main repository.

## 16. Crawl4AI

Observed: MemoryAdaptiveDispatcher, SemaphoreDispatcher, RateLimiter, CrawlerMonitor, streaming and selectable scraping strategies.
Heroic mapping: bounded frontier, resource budgets and future acquisition monitoring.
Gap: no unified memory-aware dispatcher/monitor public API.
Action: candidate AcquisitionResourceController built on existing hard budgets.
Source: https://github.com/unclecode/crawl4ai
License: Apache-2.0 with an additional current attribution requirement.

## 17. Crawlee

Observed: RequestQueue, SessionPool, ProxyConfiguration, Dataset, KeyValueStore, Router, Snapshotter/SystemStatus, retries, hooks/lifecycle, HTTP/browser crawling and browser-engine abstraction.
Heroic mapping: PriorityFairFrontier, BrowserSessionPool, retries and route/session lifecycle.
Gap: Heroic intentionally avoids adding a second persistent crawler datastore; transient queue state stays in memory and durable mission state remains in existing authorized stores.
Action: continue pattern reuse without importing Crawlee.
Source: https://github.com/apify/crawlee
License: Apache-2.0.

## 18. Scrapy

Observed: scheduler, downloader middleware, spider middleware, item pipelines, feed exports, extensions and detailed signals/lifecycle telemetry.
Heroic mapping: acquisition planner, extractor capability registry, output layer and bounded diagnostics.
Gap: no single Scrapy-style lifecycle signal bus for extractor receipts.
Action: candidate lightweight acquisition/extraction event receipts without creating a second scheduler authority.
Source: https://github.com/scrapy/scrapy
License: BSD-3-Clause.

## 19. Browser Use

Observed: Browser Use agent, BrowserSession lifecycle, custom Tools, structured output, skills, CLI, local/cloud browser support, profiles/recordings/data policies, multiple model wrappers and screenshots/vision.
Heroic mapping: bounded browser acquisition, session pool, tool contract and benchmark.
Gap: hosted Browser Use services are not acceptable as a default strict-zero-cost dependency.
Action: retain session/tool/structured-output patterns; exclude hosted stealth/CAPTCHA service assumptions.
Source: https://github.com/browser-use/browser-use
License: MIT for the current open-source repository.

## Cross-repository coverage already present in Heroic

The current Operations extractor registry already covers many capabilities that are easy to miss when reading only the third-party summary: browser XHR capture, public endpoint discovery, SPA/XHR discovery, public search parsing, RSS/Atom and JSON feed parsing, Markdown fallback, Next.js extraction, historical public URL recovery, image OCR, change checkpoints, JSON/JSONL/CSV/XLSX/SQLite output, and platform adapters for Shopify, WooCommerce, WordPress, Wix, BigCommerce, Magento, PrestaShop, Squarespace and DotPe.

The fresh gap audit therefore did not create duplicate implementations for those capabilities.

## New implementation completed from this audit

The one actionable runtime gap found was batch scheduling: PriorityFairFrontier existed but extract_and_map_many did not use it. It is now applied as deterministic admission scheduling for unique public HTTP(S) batch targets while preserving historical input order, duplicate semantics and per-target run_one resource/recovery authority.

Focused validation: 3/3 batch-scheduler tests passed. The existing third-party runtime integration suite remains 9/9.

## Remaining candidate layers

1. SearchJumper-style declarative search-definition registry.
2. Agent-Reach-style source/backend doctor report.
3. Unified memory-aware acquisition controller/monitor.
4. Lightweight extractor lifecycle/event receipt bus.
5. Direct WebDocument/EvidenceContext use in answer assembly when external evidence is present.
6. License-aware model capability registry carrying resource, provenance/watermark and deployment restrictions.

These are controlled candidates, not automatic production authority.

## Safety and licensing rule

Do not treat repository code, model weights, checkpoints, datasets, hosted APIs, trademarks or generated outputs as one license surface. Copyleft source, restricted model/weight terms, hosted-service fees and attribution obligations are tracked separately.

## Production and feed boundary

The third-party research and batch-scheduler implementation did not change the immutable Cloudflare production Operations pin. WooCommerce/Google Merchant feed recovery remains a separate lane and was not modified by this work.

## Continuation rule

Future maintenance chats should refresh all 19 repository default branches and current Foundation/Operations/Cloudflare state before changing architecture. Read this document before repeating the same third-party research.
