# Nightly benchmark AI cross-fire — 2026-10-03

## Purpose

The canonical autonomous benchmark remains deterministic and authoritative. This workflow adds a separate six-lane AI cross-fire that observes the benchmark receipt and produces advisory diagnostics.

## Execution

Six current Workers AI models receive the same bounded evidence payload in parallel, with one lane per model and a maximum parallelism of six:

- `@cf/zai-org/glm-4.7-flash`
- `@cf/google/gemma-4-26b-a4b-it`
- `@cf/nvidia/nemotron-3-120b-a12b`
- `@cf/openai/gpt-oss-20b`
- `@cf/openai/gpt-oss-120b`
- `@cf/qwen/qwen3.8-27b`

Each lane uses the current Workers AI REST contract: the model is in the URL and the model input is sent directly in the request body. Thinking is explicitly disabled for deterministic advisory output, with a 192-token output bound.

Each lane writes exactly one receipt. Artifact download keeps the six artifacts separate so identically named `receipt.json` files cannot overwrite one another. The aggregate requires six distinct model receipts and six schema-compliant successful transports; missing or duplicate evidence fails closed.

## Credential boundary

The workflow prefers `CLOUDFLARE_AI_API_TOKEN` and falls back to `CLOUDFLARE_API_TOKEN`. A dedicated Workers AI token is preferred because Cloudflare's current REST documentation requires a Workers AI-capable API token. Authentication failures are recorded explicitly and cannot be misclassified as model failures or successful lanes.

## Evidence boundary

Only the deterministic final benchmark receipt is sent to the AI lanes. The workflow does not execute downloaded artifacts, check out untrusted artifact code, dispatch another workflow, mutate GitHub, mutate Cloudflare, modify credentials or policy, or certify production/research completion.

Every receipt contains a SHA-256 digest of the bounded AI input and an explicit advisory-only authority marker. Transport success and schema compliance are separate acceptance dimensions.

## Live validation

A live six-model Cloudflare cross-fire was executed through the authorized Cloudflare account connector using six-way parallel model lanes, three tasks, and three repeats per model: 54 calls total. All 54 transports succeeded and all 54 exact-output quality checks passed, using 209.575 reported Neurons.

A focused nine-call rerun of the GPT-OSS 120B lane also passed 9/9 after the full matrix, confirming the earlier one-off formatting miss was not persistent under six-way model parallelism and deterministic settings.

## CI defects found and corrected

The previous workflow used an unquoted Python heredoc, allowing shell command substitution inside the Python expression. It also used `merge-multiple: true`, which collapsed six artifacts containing the same `receipt.json` path into one receipt. Finally, it called the legacy generic `/ai/run` wrapper instead of the current model-path Workers AI REST endpoint. All three workflow correctness defects are corrected.

The existing repository `CLOUDFLARE_API_TOKEN` was observed in the prior live GitHub run to return HTTP 401. The implementation cannot manufacture or replace that secret. The dedicated Workers AI secret fallback separates the AI permission boundary from the general deployment credential while preserving fail-closed behavior.

## Cost and authority

The cross-fire remains advisory and does not replace deterministic acceptance gates. Current Workers AI pricing documents a 10,000-Neuron daily Free allocation; the run stays bounded well below that in ordinary operation. AI agreement never becomes correctness, production health, or research-completion authority.
