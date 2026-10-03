# Nightly benchmark AI cross-fire — 2026-10-03

## Purpose

The canonical autonomous benchmark remains deterministic and authoritative. This workflow adds a separate six-model AI cross-fire that observes the benchmark receipt and produces advisory diagnostics.

## Execution

GitHub Actions checks out the current Foundation revision, resolves the latest successful autonomous benchmark run on `main`, and sends a bounded evidence envelope to the canonical public front door at `https://heroic-ai.pages.dev/api/v1/benchmark/ai-crossfire`.

The authenticated Operations runtime fans the request out across six current Workers AI models in parallel through the native AI binding:

- `@cf/zai-org/glm-4.7-flash`
- `@cf/google/gemma-4-26b-a4b-it`
- `@cf/nvidia/nemotron-3-120b-a12b`
- `@cf/openai/gpt-oss-20b`
- `@cf/openai/gpt-oss-120b`
- `@cf/qwen/qwen3.8-27b`

The workflow sends no Cloudflare API token. GitHub supplies only the existing application authentication token and bounded benchmark evidence. Cloudflare performs model execution internally through the native Workers AI binding.

Each model lane uses deterministic temperature, a 192-token output limit, and thinking disabled. Operations returns one bounded aggregate containing all six lane receipts.

## Provenance and deployment-pin protection

Automatic benchmark selection is restricted to successful `autonomous-benchmark` runs on the `main` branch. Manual run IDs are independently revalidated as completed successful main-branch benchmark runs.

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

A six-way parallel Cloudflare connector cross-fire executed 54 calls: six models × three task contracts × three repeats. All 54 transports succeeded and all 54 exact-output quality checks passed, using 209.575 reported Neurons.

A focused nine-call GPT-OSS 120B rerun also passed 9/9.

A real GitHub Actions cross-repo regression then minted the read-only Operations App token, checked out the private Operations branch, installed its Workers runtime dependencies, and completed the cross-fire regression test successfully in run `37104924105`.

## Known production promotion boundary

The new Operations endpoint is not considered live until Operations PR #1566 is promoted through the repository's controlled production release and pin process. The live production Operations worker remains on its current immutable pin until that promotion is executed.

## Cost and authority

Cloudflare currently documents a 10,000-Neuron daily Workers AI Free allocation. The cross-fire is bounded and records reported Neuron usage. AI agreement never becomes correctness, production-health, or research-completion authority.

## Relationship to the canonical benchmark

The project-native deterministic benchmark remains authoritative. AI cross-fire is a diagnostic/advisory layer over its receipt and does not replace the 24-program nightly research execution or its acceptance gates.
