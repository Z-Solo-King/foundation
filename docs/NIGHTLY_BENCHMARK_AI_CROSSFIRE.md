# Nightly benchmark AI cross-fire — 2026-10-03

## Purpose

The canonical autonomous benchmark remains deterministic and authoritative. This workflow adds a separate six-model AI cross-fire that observes the benchmark receipt and produces advisory diagnostics.

## Execution

GitHub Actions runs the cross-fire from the `workflow_run` completion event of the canonical `autonomous benchmark` workflow, using that exact successful run ID and final artifact, and sends a bounded evidence envelope to the canonical public front door at `https://heroic-ai.pages.dev/api/v1/benchmark/ai-crossfire`.

The authenticated Operations runtime fans the request out across six currently qualified instruction-oriented Workers AI models in parallel through the native AI binding:

- `@cf/meta/llama-4-scout-17b-16e-instruct`
- `@cf/mistralai/mistral-small-3.1-24b-instruct`
- `@cf/ibm-granite/granite-4.0-h-micro`
- `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- `@cf/meta/llama-3.2-3b-instruct`
- `@cf/mistral/mistral-7b-instruct-v0.2-lora`

The workflow sends no Cloudflare API token. GitHub supplies only the existing application authentication token and bounded benchmark evidence. Cloudflare performs model execution internally through the native Workers AI binding.

Each model lane uses temperature 0, seed 17, JSON mode, and a 128-token output limit. The request adapter avoids model-specific chat-template options and retries one invalid/incomplete lane once with an equally bounded recovery request. Operations returns one bounded aggregate containing all six lane receipts.

## Provenance and deployment-pin protection

Nightly execution is chained to a successful scheduled `autonomous benchmark` run on the `main` branch rather than searching for the newest successful run. Manual run IDs are independently revalidated as completed successful main-branch benchmark runs. The final artifact must match the exact triggering run ID and benchmark head SHA.

Foundation reads the production Operations SHA from `docs/OPERATIONS_PIN_MANIFEST.json` and includes it in the cross-fire request. Operations reports its deployed `RELEASE_OPERATIONS_REF`, and GitHub fails closed if the live runtime pin differs from the expected production pin.

## Coverage and quality gates

The aggregate requires exactly six distinct model receipts. It fails closed when a lane is missing, duplicated, transport-failed, or schema-invalid.

GitHub verifies:

- expected and observed model count are both 6;
- all 6 transports succeeded;
- all 6 advisories comply with the exact schema;
- `coverage_complete == true`;
- `quality_complete == true`;
- the deployed Operations revision matches the Foundation production pin manifest.

## Evidence boundary

Only the deterministic final benchmark receipt is sent to the AI lanes. The cross-fire does not execute downloaded artifacts, mutate GitHub, mutate Cloudflare configuration, modify credentials or policy, dispatch workflows, or certify production/research completion.

Every aggregate carries an evidence SHA-256 and the authority marker `advisory_only_no_acceptance_or_mutation_authority`.

## Live validation

A live qualification sweep against the current Workers AI account found that the original reasoning-heavy fleet could return HTTP 200 while still violating the bounded advisory output contract. The final six-lane instruction-oriented fleet was then stress-tested against the same benchmark-evidence shape: 18/18 transport success, 18/18 valid JSON outputs, and 18/18 normal stop completions. A bounded one-retry recovery is now implemented for any future invalid/incomplete lane.

## Production pin reconciliation

The live Operations Worker was re-checked through the Cloudflare control plane. Its deployed `RELEASE_OPERATIONS_REF` is `11f592116d9ef57b6189bf8bf0ff0e95ec3d410f`, which is now the Foundation immutable production pin. Operations `main` remains a moving branch and is not treated as production authority.

## Cost and authority

Cloudflare currently documents a 10,000-Neuron daily Workers AI Free allocation. The cross-fire is bounded and records reported Neuron usage. AI agreement never becomes correctness, production-health, or research-completion authority.

## Relationship to the canonical benchmark

The project-native deterministic benchmark remains authoritative. AI cross-fire is a diagnostic/advisory layer over its receipt and does not replace the 24-program nightly research execution or its acceptance gates.
