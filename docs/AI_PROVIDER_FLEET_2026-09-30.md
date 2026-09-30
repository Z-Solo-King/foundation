# AI Provider Fleet — Foundation Public Contract — 2026-09-30

This public-safe document defines the provider families supported by the project-side AI task fabric. It does not expose credentials, private bindings or live quota claims.

## Supported external API families

- OpenRouter Free
- Groq
- Gemini
- Cerebras
- NVIDIA NIM
- Cohere
- Hugging Face Inference Providers
- SiliconFlow

Cloudflare Workers AI is a native runtime binding and is not counted as an external API family.

The eight-family list is the cross-repository contract. A supported family is not automatically configured or eligible in every environment.

### Foundation environment note

Foundation's documented environment currently has SiliconFlow activated. Cerebras is supported by the shared contract but remains unconfigured there until its credential/account conditions are explicitly supplied. The remaining provider families are subject to their own runtime credential, model, quota, privacy and zero-cost checks.

Mistral remains a conditional candidate outside the strict-$0 active external fleet.

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

AI output is advisory for research, retrieval synthesis, extraction assistance, auditing, scanning, action planning, workflow assistance and Cloudflare diagnostics. Deterministic evidence, authorization, mutation, identity, mapping, quality and deployment boundaries remain authoritative.

## Zero-cost policy

The project is configured to fail closed for cost:

- maximum daily AI cost: $0
- paid fallback: disabled
- unknown pricing: disabled
- automatic recharge: disabled
- automatic upgrade: disabled
- runtime availability must be observed before use

Each provider has independent model/account/plan limits. The system must never infer or invent a combined free quota.

## Provider transport and semantics

The common external transport is OpenAI-compatible chat completion where the provider supports that interface. Compatibility is a transport contract, not proof of semantic equivalence. Provider-specific system/developer-role, tool-calling, structured-output, context-window, streaming and error semantics must be covered by differential tests before a route is treated as interchangeable.

Private Operations remains the source of truth for provider endpoints, runtime eligibility and credential configuration. Foundation intentionally does not duplicate those private details.

## Cross-repository authority

Foundation owns public-safe contracts and workflows. Operations owns private provider policy and the canonical runtime task fabric. The shared eight-family contract is documented here and privately; runtime state, freshness, quota, billing/cost and model availability remain execution-time authority.

## AI / extractor boundary

The extraction_assist task family is candidate assistance only. It may generate parser/mapping hypotheses or bounded retrieval suggestions, but it cannot establish source truth, fabricate evidence, override extractor security/resource policy, choose identity, promote mapper authority or mutate protected runtime state.

The Operations extractor capability registry and evolution bridge remain the canonical runtime-side integration points.

Reviewed: 2026-09-30.