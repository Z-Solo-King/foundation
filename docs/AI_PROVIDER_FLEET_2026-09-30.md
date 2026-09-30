# AI Provider Fleet — Foundation Public Contract — 2026-09-30

This public-safe document defines the current external AI API fleet available to project automation.

## Active external APIs

- OpenRouter Free
- Groq
- Gemini
- NVIDIA NIM
- Cohere
- Hugging Face Inference Providers
- SiliconFlow

Cloudflare Workers AI is a native runtime binding and is not counted as an external API provider.

Mistral is not part of the project provider fleet.

## Cross-task contract

Every AI-assisted task should use the governed task-family abstraction rather than selecting a vendor directly.

Supported task families:

- chatbot
- research
- search_synthesis
- extraction_assist
- audit_assist
- scan_triage
- action_plan
- workflow_assist
- cloudflare_diagnostic

AI output is advisory for research, retrieval synthesis, extraction assistance, auditing, scanning, action planning, workflow assistance and Cloudflare diagnostics. Deterministic evidence, authorization, mutation and deployment boundaries remain authoritative.

## Zero-cost policy

The project is configured to fail closed for cost:

- maximum daily AI cost: $0
- paid fallback: disabled
- unknown pricing: disabled
- automatic recharge: disabled
- automatic upgrade: disabled
- runtime availability must be observed before use

The seven active external providers have independent limits and availability. The system must not invent a combined free quota.

## Provider endpoints

The canonical OpenAI-compatible endpoints are recorded in the private Operations task-fabric source of truth. This public document intentionally does not contain credentials or private runtime bindings.

## Cross-repository authority

Foundation owns public contracts and workflows. Operations owns private provider policy and the canonical runtime task fabric. Public and private documents must point to the same seven-provider contract and must not create competing provider authorities.

Reviewed: 2026-09-30.