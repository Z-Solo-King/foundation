# Multi-agent nightly research

## Capacity model

The nightly research system is intentionally split into three independent research lanes.
Each lane contains eight one-hour research programs, giving 24 distinct program slots per night.
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

The program-level cap is 6 simultaneously active agents per lane. The coordinator also has a global cap of 18 active agent tasks. This allows three research programs to run concurrently without turning each logical agent into a separate GitHub Actions job.

## GitHub Actions layout

GitHub's current standard hosted-runner concurrency for the Free plan is 20 concurrent jobs, while an individual job can run for up to 6 hours. Standard hosted runners are free in public repositories. The nightly workflow therefore uses six jobs total: three lanes for 01:00-05:00 IST followed by three dependent jobs for 05:00-09:00 IST.

This is deliberately different from a 30-runner design: the 30-agent figure is a logical-agent capacity target, not a GitHub runner count.

## AI boundary

`benchmark/multi_agent/llm.py` provides a provider-neutral OpenAI-compatible chat adapter. It is only used when these environment variables are present:

- `RESEARCH_LLM_ENDPOINT`
- `RESEARCH_LLM_API_KEY`
- `RESEARCH_LLM_MODEL`

No production secrets are created or modified by this repository change. Without those variables, the scheduler uses its deterministic orchestration executor so CI can validate the multi-agent contract without making paid or unverified model calls.

The adapter does not claim that an LLM has browsed a source. Actual web/search/retrieval adapters must be injected explicitly and must obey the research engine's existing source policy and cost gates.

## Nightly research flow

`3 lanes -> 8 programs/lane -> 24 programs/night -> 10 logical agents/program -> 8 evidence agents in parallel -> reconciler + evaluator -> findings -> follow-up questions -> next-night research queue`

The target output is not only an answer. Every program should yield benchmark regressions, new ecosystem/platform knowledge, new techniques, alternatives, new regression-test candidates, and cost/token-efficiency observations.
