# Agent Behavior Benchmark

This benchmark measures observable model/agent behavior without depending on a specific provider.

## What it measures

- **Correctness:** fraction of required claims that are correct.
- **Evidence quality:** supported claims relative to required/correct claims.
- **Completeness:** penalties for explicitly missed requirements.
- **Precision:** penalties for duplicate, irrelevant, and unsupported actions/claims.
- **Token efficiency:** useful verified signal per thousand input/output/thinking tokens.
- **Tool efficiency:** useful tool calls divided by tool calls.
- **Context efficiency:** bounded signal based on cache reuse, compaction count, and peak context versus total observed tokens.
- **Self-correction:** observed corrections relative to successful actions/corrections.

## Fair cross-model evaluation

Run the same task corpus, requirements, evidence rules, and tool policy against every model. Record observations, not hidden reasoning. Do not infer correctness from a model's confidence or verbosity.

A model run is an observation. It is not authoritative evidence for Foundation. Any discovered weakness must be reproduced against repository/runtime evidence before becoming a project issue or code change.

## Recommended comparison protocol

1. Run identical tasks for each model.
2. Capture token, action, source, correction, and context counters.
3. Score each run deterministically.
4. Aggregate by model and task.
5. Inspect model-specific misses and false positives.
6. Re-test candidate findings independently.
7. Convert only verified improvements into regression tests or implementation changes.

The benchmark intentionally does not encode provider-specific prompting tricks. Provider-specific strategies belong in separate experimental adapters so the public deterministic core remains provider-neutral.
