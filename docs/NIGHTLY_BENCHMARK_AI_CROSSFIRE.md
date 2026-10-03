# Nightly benchmark AI cross-fire — 2026-10-03

## Purpose

The canonical autonomous benchmark remains deterministic and authoritative. This workflow adds a separate six-model AI cross-fire that observes the benchmark receipt and produces advisory diagnostics.

## Execution

GitHub Actions resolves the latest successful autonomous benchmark receipt and sends a bounded evidence envelope to the canonical public front door at `https://heroic-ai.pages.dev/api/v1/benchmark/ai-crossfire`. The authenticated Operations runtime then fans the request out across six current Workers AI models in parallel through the native AI binding:

- `@cf/zai-org/glm-4.7-flash`
- `@cf/google/gemma-4-26b-a4b-it`
- `@cf/nvidia/nemotron-3-120b-a12b`
- `@cf/openai/gpt-oss-20b`
- `@cf/openai/gpt-oss-120b`
- `@cf/qwen/qwen3.8-27b`

This removes the GitHub-to-Cloudflare API-token dependency from the benchmark path. GitHub supplies only its existing application authentication token and bounded evidence. Cloudflare performs the model execution locally under the Workers AI binding.

Each model lane uses deterministic temperature, a 192-token output limit, and thinking disabled. The runtime returns one bounded aggregate containing all six lane receipts.

## Coverage and quality gates

The aggregate requires exactly six distinct model receipts. It fails closed when any lane is missing, duplicated, transport-failed, or schema-invalid. Transport success and advisory schema compliance are recorded independently.

GitHub Actions also verifies `model_count_expected == 6`, `model_count_observed == 6`, six successful transports, six schema-compliant advisories, `coverage_complete == true`, and `quality_complete == true`.

## Evidence boundary

Only the deterministic final benchmark receipt is sent to the AI lanes. The cross-fire does not execute downloaded artifacts, mutate GitHub, mutate Cloudflare configuration, modify credentials or policy, dispatch workflows, or certify production/research completion.

Every aggregate carries an evidence SHA-256 and the authority marker `advisory_only_no_acceptance_or_mutation_authority`.

## Live validation

A six-way parallel Cloudflare connector test executed 54 calls: six models × three task contracts × three repeats. All 54 transports succeeded and all 54 exact-output quality checks passed, using 209.575 reported Neurons.

A focused nine-call GPT-OSS 120B rerun also passed 9/9.

The subsequent GitHub-hosted execution reached all six lane jobs and correctly preserved all six receipts, but the repository's existing `CLOUDFLARE_API_TOKEN` returned HTTP 401. That failure is intentionally eliminated by routing the production benchmark through the native Workers AI endpoint above.

## Cost and authority

Cloudflare currently documents a 10,000-Neuron daily Free allocation for Workers AI, with usage above that requiring a Paid plan. The cross-fire remains bounded and records reported Neurons. The AI advisory layer never becomes acceptance authority.

## Relationship to the canonical benchmark

The project-native benchmark remains the authoritative deterministic system. AI cross-fire is a diagnostic/advisory layer over its receipts and does not replace its 24-program execution or evidence gates.
