# Nightly benchmark AI cross-fire — 2026-10-03

## Purpose

The canonical autonomous benchmark remains deterministic and authoritative. This workflow adds a separate six-model AI cross-fire that observes the benchmark receipt and produces advisory diagnostics.

## Execution

GitHub Actions runs the cross-fire from the `workflow_run` completion event of the canonical `autonomous benchmark` workflow, using that exact successful run ID and its final artifact. Manual dispatch may supply an explicit completed benchmark run ID. The workflow validates the artifact run ID and repository revision before sending a bounded evidence envelope to the canonical public front door at `https://heroic-ai.pages.dev/api/v1/benchmark/ai-crossfire`.

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

Nightly execution is chained to a successful scheduled `autonomous benchmark` run on the `main` branch rather than searching for the newest successful run. Manual run IDs are independently revalidated as completed successful main-branch benchmark runs. The final artifact must carry the exact triggering run ID and benchmark head SHA.

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

A live model-fleet qualification was rerun against the current Workers AI account. The original fleet produced transport success but exposed output-contract failures in GPT-OSS and GLM lanes. Four replacement candidates were then tested three times each; all 12 runs produced stop-completed, parseable JSON. The implementation now uses six current stable lanes and a bounded recovery attempt for any invalid/incomplete response.

The protected GitHub workflow additionally validates exact benchmark run identity, artifact revision, finalization status, and the immutable Operations production pin before invoking AI.

## Production pin reconciliation

The live Operations Worker was re-checked through the Cloudflare control plane. Its deployed `RELEASE_OPERATIONS_REF` is `11f592116d9ef57b6189bf8bf0ff0e95ec3d410f`, which is now the Foundation immutable production pin. Operations `main` remains a moving branch and is not treated as production authority.

The cross-fire therefore fails closed on a real pin mismatch rather than silently accepting a stale repository manifest.

## Cost and authority

Cloudflare currently documents a 10,000-Neuron daily Workers AI Free allocation. The cross-fire is bounded and records reported Neuron usage. AI agreement never becomes correctness, production-health, or research-completion authority.

## Relationship to the canonical benchmark

The project-native deterministic benchmark remains authoritative. AI cross-fire is a diagnostic/advisory layer over its receipt and does not replace the 24-program nightly research execution or its acceptance gates.