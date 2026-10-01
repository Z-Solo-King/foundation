# Heroic AI — Third-Party Repository Coverage — 2026-10-01

This is the durable project-level record for the 19 external repositories supplied for architecture research. Repository-wide review includes top-level structure, core implementation areas, docs/skills, tests/CI surfaces where present, and license/reuse risk.

Foundation remains the public-safe deterministic contract/deployment authority; Operations remains the private chatbot/provider/policy/resource/acquisition/extraction/research authority.

| Repository | Coverage focus | Decision |
|---|---|---|
| hoothin/SearchJumper | search definitions/schema, React UI, extension | Adopt configuration-driven search pattern; no GPL code |
| Panniantong/Agent-Reach | channels, ordered backends, doctor/skills/tests | Adopt backend health/fallback pattern |
| whaleyxbt/patchright-enhanced | browser/session/config/source | Benchmark only; no bypass promotion; licensing unclear |
| D4Vinci/Scrapling | adaptive parser/fetchers/spiders/tests/docs | **Implemented adaptive extraction slice in Operations** |
| Comfy-Org/ComfyUI | graph execution, queues, resources, plugins | Adopt workflow/resource pattern only |
| Wan-Video/Wan2.1 | inference/config/resource efficiency | Adopt resource-profile ideas only |
| Tencent-Hunyuan/HunyuanVideo | efficient inference, multi-GPU, FP8 | Adopt measured compute-efficiency principles only |
| black-forest-labs/flux | inference surface, model cards, licenses | Adopt code-vs-weight license inventory |
| facebookresearch/audiocraft | modular model/runtime package, tests | Adopt task/model configuration boundaries |
| ace-step/ACE-Step | infer/API/train separation | Adopt capability boundary pattern |
| resemble-ai/chatterbox | compact variants, examples, packaging | Adopt model/capability profile pattern |
| hpcaitech/Open-Sora | configs/scripts/experiments | Adopt reproducible configuration |
| Stability-AI/stable-audio-tools | JSON model/runtime configurations | Adopt versioned execution profiles |
| deepbeepmeep/Wan2GP | low-resource runtime, plugins, profiles | Adopt lazy activation/resource envelopes |
| firecrawl/firecrawl | scrape/crawl/map/browser/skills | Architecture reference only; AGPL main repository |
| unclecode/crawl4ai | adaptive crawler, dispatcher, extraction/cache/browser | Adopt bounded adaptive stopping/dispatch |
| apify/crawlee | scheduler/frontier/session pool/retries | Adopt policy-aware frontier/session concepts |
| scrapy/scrapy | engine/scheduler/downloader/middleware/pipeline | Adopt separation-of-concerns model |
| browser-use/browser-use | BrowserSession/CDP/watchdogs/tools | Adopt browser tool/session concepts as escalation |

## Implemented change

The first implementation slice is merged in Operations main.

- Operations PR #1421 merged as `0e3764fc5d3000f26f7bb806173c92b71ea0b49b`: bounded adaptive HTML product recovery.
- Operations PR #1422 merged as `ad67fb0af2e958c880f74a10a0d15c930b3dace1`: fixed the validated missing adaptive-extractor import.
- Operations PR #1423 merged as `daede840e353bf6b5d2cf295e33ac562295c562f`: connected adaptive recovery to the existing chatbot `EXTRACT_AND_MAP` contract and added a regression test.
- Foundation documentation was merged as `e9b67e37c997e7c51a5a20fb158930727302b120`.

The adaptive path is bounded, deterministic, multi-signal and fallback-only. It does not bypass access controls or alter the authority boundary.

**Deployment state:** Cloudflare production still runs the certified Operations pin `90fa37df10d63824acd3fe20b64cc91043af9627`. The third-party improvements are therefore GitHub-main implementation evidence, not production-runtime acceptance evidence.

## Durable follow-on plan

1. Source/backend health fabric using the existing Operations source-profile/revalidation authority.
2. Priority/fairness/retry scheduling on top of the existing bounded crawl frontier.
3. Bounded evidence-gain stopping for research/extraction.
4. Canonical bounded web-document intermediate representation before chatbot context assembly.
5. Cloudflare Browser Run session reuse benchmark with isolated contexts.
6. Feed/extractor coverage experiments remain separate from non-feed migration controls unless explicitly opened.

## Integration safety

All candidates require deterministic tests, functional/error/security/policy/provenance/cancellation/timeout parity, resource/latency/token measurements, shadow, canary, rollback, and live evidence. A benchmark, LLM suggestion, or external repository score cannot become production authority.

## Licensing guard

Code, model weights/checkpoints, hosted APIs, and trademarks are separate surfaces. SearchJumper is GPL-3.0; Firecrawl's main repository is AGPL-3.0; Browser Use is AGPL-3.0; Patchright Enhanced has no root LICENSE in the inspected tree. FLUX explicitly separates repository code from model licenses, with some models under non-commercial terms. These surfaces require review before copying or deployment.

## Chatbot requirement

The chatbot consumes improvements only through the existing capability, policy and provenance layers. Third-party READMEs are research inputs, not runtime authorities.

## Continuation

Future chats must read this document before repeating this repository research. The implementation state lives in GitHub and must be checked from current main/PRs rather than conversation memory.
