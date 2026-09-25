# ChatGPT + AI Agent Benchmark Integration — 2026-09-25

This addendum connects the ChatGPT multi-lane execution playbook to the project's governed agent tree and AI/agent benchmark.

## Execution tree

`Main -> Explorer / Worker / Researcher`

`Advisor -> on-call review gate`

Main owns planning, aggregation, and final verification. Explorer is read-only discovery. Worker performs one scoped implementation slice. Researcher collects documentation and external evidence. Advisor challenges major plans, repeated failures, and completion claims.

## Benchmark discipline

Run identical task/tool policy across model/provider/agent combinations. Preserve task, fixture, tool-policy version, exact repository revision, language lens, evidence tier, and artifact digest. Prefer at least three repeated observations before treating a stochastic difference as stable.

## Audit-derived diversity

Use six lanes:
A planning/architecture;
B code/implementation;
C testing/verification;
D research/evidence;
E security/reliability/recovery;
F migration/tooling portability.

Within active lanes vary language, component, evidence mode, and risk class. Do not count duplicate work as diversity.

## Failure learning loop

`observe -> classify -> reproduce -> fix/record blocker -> benchmark -> regression`

Use the existing audit methods: differential/reference comparison, metamorphic checks, adversarial cases, schedule/concurrency exploration, fault injection, late-output handling, resource-bound tests, schema drift, artifact parity, stale-pin/contradiction scans, and evidence-freshness checks.

## Evidence boundary

Benchmark scores are observations. They cannot close runtime/control-plane issues or transfer security, policy, resource, evaluation, recovery, or deployment authority. A merged PR and a green CI run are still distinct from runtime and production evidence.
