# Backend Knowledge Exchange Contract

**Status:** normative  
**Owner:** Foundation family boundary  
**Consumers:** Foundation, Operations, chatbot/provider adapters, research/evaluation backends

## Goal

Different execution backends must learn from the same bounded observations without sharing credentials, private raw responses, protected topology, or competing policy authority.

The exchange has three layers:

1. **Private runtime observations — Operations only.** Exact provider responses, credentials, exact quota counters, circuit state and protected telemetry remain private.
2. **Sanitized provider knowledge — shared contract.** Provider/model/task, outcome, bounded latency class, coarse quota state, retry hint, timestamps and bounded reason may cross backend boundaries.
3. **Public-safe evidence — Foundation.** Only information safe for public CI, deterministic benchmarks and AI navigation is retained here.

## Canonical ownership

| Knowledge | Owner | Consumers |
|---|---|---|
| Provider selection policy | Operations | Operations chatbot/research |
| Exact provider quota/circuit state | Operations | Operations runtime |
| Provider observation normalization | Operations | chatbot, research, benchmark |
| Sanitized provider knowledge schema | Foundation boundary contract | Operations producer + Foundation consumers |
| Public benchmark/evidence representation | Foundation | both repositories and public CI |

A consumer must not create a second provider policy or quota authority from the shared knowledge.

## Exchange schema

`provider-knowledge/v1`

Required fields:
- `provider`
- `model`
- `task`
- `outcome`
- `latency_class`
- `quota_state`
- `retry_after_seconds`
- `observed_at`
- `expires_at`
- bounded `reason`

The schema deliberately excludes API keys, authorization headers, raw provider payloads, exact private quota counts, private endpoints, private account identifiers and protected topology.

## Backend rule

Every backend adapter should consume the same normalized knowledge envelope when it needs provider history. A provider-specific adapter may add private fields internally, but those fields must not become the cross-backend contract.

This gives Groq, Gemini, Cerebras, Cloudflare Workers AI and other adapters a common learning surface: a successful/failed observation can improve routing, retries, benchmark interpretation and future research without coupling those systems to a provider implementation.

## GitHub execution boundary

Cross-repository knowledge synchronization must execute from **Foundation-hosted public workflows** or another explicitly approved public runtime. A private Operations repository must not contain or become the execution host for GitHub Actions.

Foundation may use a narrowly scoped GitHub App token to read private Operations source/evidence when the workflow itself runs in Foundation. The token is an access mechanism, not a private Actions dependency.

Never solve a synchronization problem by:
- adding `.github/workflows` to Operations;
- dispatching a private-repository workflow;
- copying private source into Foundation;
- publishing secrets or raw provider responses;
- treating a private runtime receipt as public evidence without sanitization.

## Acceptance

A backend-knowledge change is valid only when:
1. the producer emits `provider-knowledge/v1`;
2. exact private quota/credential data stays private;
3. the consumer can distinguish `unknown`, `available` and `exhausted` without inventing quota;
4. freshness/expiry is preserved;
5. provider policy remains owned by Operations;
6. public Foundation CI can validate the schema without private credentials;
7. the relevant repository and boundary tests pass.

This contract complements `docs/FAMILY_CONTRACT.json` and `docs/FAMILY_SYNC_STANDARD.md`; it does not create a second ownership system.