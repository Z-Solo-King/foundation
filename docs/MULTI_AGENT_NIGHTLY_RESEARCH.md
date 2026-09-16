# Multi-agent nightly research

## Capacity model

The nightly research system runs three independent research lanes in parallel. Each lane contains eight one-hour research programs, giving 24 distinct program slots per night.

Each program has exactly 10 logical agent roles:

1. research lead
2. source discovery
3. primary evidence
4. secondary evidence
5. adversarial research
6. temporal analysis
7. technical analysis
8. community/regional research
9. reconciliation
10. evaluation

The first eight agents form the evidence phase. Reconciliation and evaluation consume the combined evidence and produce gaps/follow-up questions.

The program-level cap is 6 simultaneously active agents for lanes 0 and 1, and 8 for lane 2. The nightly aggregate cap is 20 active agent tasks (`6 + 6 + 8`). This keeps the workload inside the intended GitHub Actions concurrency envelope without turning every logical agent into a separate job.

## GitHub Actions layout

The scheduled workflow starts at **01:00 IST** (`19:30 UTC` on the previous day) and starts all three lanes in parallel. Each lane validates exactly eight program IDs (`laneN-slot0` through `laneN-slot7`). A final summary combines the three lane artifacts and requires all 24 programs before the run is accepted.

Each lane has a bounded job timeout so the complete run is intended to finish before the **09:00 IST** maintenance-window boundary. There is no serial 01:00-05:00 / 05:00-09:00 dependency anymore; the old two-phase scheduler was removed because it could extend beyond the window.

This is deliberately different from a 30-runner design: the logical-agent figure is a capacity target, not a GitHub runner count.

## AI boundary

`benchmark/multi_agent/llm.py` provides a provider-neutral OpenAI-compatible chat adapter. It is only used when the scheduled workflow receives an explicit live executor endpoint, API key and model through GitHub Actions secrets.

The scheduled workflow fails closed when those values are absent; it does not silently substitute a deterministic dry-run. The adapter does not claim that an LLM has browsed a source. Actual web/search/retrieval adapters must be injected explicitly and must obey the research engine's existing source policy and cost gates.

## Nightly research flow

`3 parallel lanes -> 8 programs/lane -> 24 programs/night -> 10 logical agents/program -> evidence phase -> reconciliation + evaluation -> findings -> follow-up questions -> next-night research queue`

The target output is not only an answer. Every program should yield benchmark regressions, new ecosystem/platform knowledge, new techniques, alternatives, new regression-test candidates, and cost/token-efficiency observations.

For the operational schedule, artifact contract, exact coverage checks and acceptance gates, see `docs/NIGHTLY_RESEARCH_RUNBOOK.md` and `.github/workflows/nightly-multi-agent-research.yml`.
