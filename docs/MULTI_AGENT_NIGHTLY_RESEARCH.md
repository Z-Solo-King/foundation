# Multi-agent nightly research

Heroic AI is the product. This workflow is the bounded overnight maintenance and learning capability behind it.

## Capacity model

The nightly research system runs three independent lanes in parallel. Each lane contains eight research programs, giving 24 distinct program slots per night.

Each program has ten logical roles: research lead, source discovery, primary evidence, secondary evidence, adversarial research, temporal analysis, technical analysis, community/regional research, reconciliation, and evaluation. Logical roles are capacity units, not one GitHub Actions job per role.

Lane capacities are 6, 6 and 8 active agents. The aggregate cap is 20 active agent tasks. This stays within the intended runner envelope without turning every logical agent into a separate job.

## GitHub Actions layout

The scheduled workflow starts at **01:00 IST** (`19:30 UTC` on the previous day) and starts all three lanes in parallel. Each lane validates exactly eight program IDs (`laneN-slot0` through `laneN-slot7`). A final summary combines the three lane artifacts and rejects the run unless all 24 programs are present.

Each lane has a bounded job timeout so the run is intended to finish before the **09:00 IST** maintenance-window boundary. There is no serial 01:00-05:00 / 05:00-09:00 dependency; the former scheduler could extend past the window.

The scheduled workflow fails closed when live executor configuration is missing. It does not silently substitute a deterministic dry-run.

## AI boundary

`benchmark/multi_agent/llm.py` provides a provider-neutral live executor adapter. It is only invoked when the scheduled workflow receives an explicit endpoint, API key and model through GitHub Actions secrets. The adapter does not claim that an LLM browsed a source; retrieval must be injected explicitly and remain subject to existing source-policy and cost gates.

## Research flow

`3 parallel lanes -> 8 programs/lane -> 24 programs/night -> bounded logical agents -> evidence -> reconciliation/evaluation -> improvement findings -> follow-up queue`

The target output includes benchmark regressions, ecosystem/platform knowledge, new techniques, alternatives, regression-test candidates, and cost/token-efficiency observations.

For the exact schedule, artifact contract, coverage assertions and acceptance gates, see `docs/NIGHTLY_RESEARCH_RUNBOOK.md` and `.github/workflows/nightly-multi-agent-research.yml`.
