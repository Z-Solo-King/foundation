# Multi-agent nightly research

Heroic AI is the product. This workflow is the bounded overnight maintenance and learning capability behind it.

## Ownership boundary

The **private multi-agent implementation is owned by `Z-Solo-King/operations`** under `private/multi_agent/`.

Foundation intentionally retains only:

- the public research workflow and truthful artifact contracts;
- the public deterministic baseline comparison module;
- the 24-program coverage assertions at the workflow-contract level;
- the GitHub Actions orchestration that fetches the approved private revision.

Foundation no longer carries the private multi-agent model definitions, provider adapter, scheduler/orchestrator, nightly program definitions, private runner, or project-research synthesizer.

## Capacity model

The nightly research system runs three independent lanes in parallel. Each lane contains eight research programs, giving 24 distinct program slots per night.

Each program has ten logical roles: research lead, source discovery, primary evidence, secondary research, adversarial research, temporal analysis, technical analysis, community/regional research, reconciliation, and evaluation. Logical roles are capacity units, not one GitHub Actions job per role.

Lane capacities are 6, 6 and 8 active agents. The aggregate cap is 20 active agent tasks. This stays within the intended runner envelope without turning every logical agent into a separate job.

The matrix and orchestration implementation are private. Public Foundation CI verifies only the external workflow contract and the pinned private revision.

## GitHub Actions layout

The scheduled workflow starts at **01:00 IST** (`19:30 UTC` on the previous day) and starts all three lanes in parallel. Each lane validates exactly eight program IDs (`laneN-slot0` through `laneN-slot7`). A final summary combines the three lane artifacts and rejects the run unless all 24 programs are present.

Before executing research, each Foundation lane uses the purpose-specific GitHub App installation credential to obtain a short-lived read token and checks out the exact immutable Operations revision recorded in `.github/workflows/nightly-multi-agent-research-v3.yml`.

The private Operations repository does **not** need a GitHub Actions workflow for this path. The execution happens on the public Foundation runner using the private source checkout. No private Operations Actions quota is consumed by the nightly engine.

The scheduled workflow fails closed when live executor configuration is missing. It does not silently substitute a deterministic dry-run.

Private source checkouts and temporary App credentials are removed with `if: always()` cleanup. Private source is never uploaded as a workflow artifact.

## AI boundary

The provider adapter now lives in private Operations. It is invoked only when the scheduled workflow receives an explicit endpoint, API key and model through GitHub Actions secrets. It does not claim that an LLM browsed a source; retrieval must be injected explicitly and remain subject to existing source-policy and cost gates.

## Research flow

`3 parallel lanes -> 8 programs/lane -> 24 programs/night -> bounded logical agents -> evidence -> reconciliation/evaluation -> improvement findings -> follow-up queue`

The target output includes benchmark regressions, ecosystem/platform knowledge, new techniques, alternatives, regression-test candidates, and cost/token-efficiency observations.

## Baseline and evidence boundary

`benchmark/multi_agent/baseline.py` remains public because it only compares already-produced nightly summaries. It does not own the private research engine.

Project-improvement findings produced by the private summarizer remain candidate evidence until the deterministic acquisition/evidence qualification path accepts them. They do not become authoritative policy, security, billing, or publication authority merely because the nightly run completed.

For the exact schedule, artifact contract, coverage assertions and acceptance gates, see `docs/NIGHTLY_RESEARCH_RUNBOOK.md` and `.github/workflows/nightly-multi-agent-research-v3.yml`.
