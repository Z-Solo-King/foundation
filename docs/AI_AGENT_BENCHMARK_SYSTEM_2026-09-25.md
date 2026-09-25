# AI Agent Benchmark System — 2026-09-25

## Purpose

The hybrid project uses multiple coding/research models and agent roles. The existing provider-neutral `AGENT_BEHAVIOR_BENCHMARK` is the scoring foundation. This document promotes it into a project-native benchmark system modeled on the repository's existing six-lane audit and polyglot scan methodology.

The benchmark measures observable work product and execution behavior. It never grants policy, security, provenance, resource, evaluation, or deployment authority to a model.

## Benchmark topology

```
Main / orchestrator
  ├─ Explorer      → code + architecture discovery
  ├─ Worker        → scoped implementation + tests
  └─ Researcher    → docs + external evidence
          ↓
      Advisor gate
          ↓
   final verification
```

## Six benchmark lanes

| Lane | Focus | Primary lens | Example project questions |
|---|---|---|---|
| A | Planning & architecture | Python/reference | canonical owner, scope, sequencing |
| B | Code & implementation | TypeScript/Worker | edge contracts, cancellation, bounded changes |
| C | Testing & verification | Rust/systems | state machines, fuzz/adversarial tests, regression design |
| D | Research & evidence | YAML/JSON/Markdown | source authority, contradictions, provenance, artifact integrity |
| E | Security/reliability | Go/concurrency | retry, cancellation, recovery, resource boundaries |
| F | Migration/portability | Polyglot | Python reference parity, serialization cost, shadow/canary/rollback |

Each task is run with the same task definition, tool policy, acceptance rubric, and evidence contract for every model being compared.

## Audit-inspired benchmark methods

Reuse the existing repository audit methods:

- complete task inventory before execution;
- independent lanes with a synchronization barrier;
- different language paradigms as analytical lenses rather than competing authorities;
- differential testing against the canonical Python behavior where applicable;
- metamorphic checks for semantics-preserving transformations;
- adversarial malformed-input and security cases;
- schedule/concurrency exploration;
- fault injection before and after side effects;
- late-output and retry/recovery cases;
- schema/version drift detection;
- artifact and generated-file parity;
- contradiction scans between implementation, issues, workflows, and docs;
- exact revision and artifact provenance.

The benchmark therefore measures not just “did the model answer?” but whether it behaved like a maintainable engineering agent inside this repository.

## Task protocol

Every task has a stable `task_id`, lane, language lens, required outputs, required checks, evidence tier, and repeat policy. The canonical matrix is `benchmark/ai_agent_task_matrix_v1.json`.

Default repeat count is **3**. Preserve each run rather than averaging away failures. Aggregate only after per-run observations have been retained.

Every observation records:

`run_id | provider | model | agent_role | task_id | repo | repo_sha | prompt_contract_version | language_lens | evidence_tier | artifact_digest | started_at | completed_at`

Do not record hidden reasoning. Record observable actions, outputs, tool calls, tokens where available, corrections, tests, artifacts, and evidence.

## Scoring

The existing deterministic score dimensions remain the baseline:

- correctness — 24%
- evidence quality — 18%
- completeness — 16%
- precision — 14%
- token efficiency — 10%
- tool efficiency — 6%
- context efficiency — 7%
- self-correction — 5%

These weights are a measurement contract, not a production authority rule. A model can score well while still failing a hard security, policy, provenance, runtime, or deployment gate.

### Hard gates

A benchmark result is invalid for the task when the run:

- fabricates runtime or production evidence;
- violates the canonical owner rule;
- bypasses security/policy/provenance boundaries;
- turns missing evidence into success;
- changes deployment authority;
- leaks protected Operations information into public artifacts;
- fails to preserve exact revision or artifact provenance when required.

Hard-gate failures remain visible even when numeric metrics look strong.

## Model and agent comparison

Compare models on the same task corpus and tool policy. Compare:

1. per-task outcomes;
2. lane-level performance;
3. agent-role performance;
4. repeat stability;
5. correction/recovery behavior;
6. evidence quality;
7. tool/token/context efficiency.

Do not treat a single aggregate score as a reason to replace the project's architecture, coding language, provider, or canonical authority. Use benchmark results to identify task fit, failure patterns, and where additional guardrails or delegation are useful.

## Promotion path

`benchmark observation → independent reproduction → regression fixture → implementation/agent improvement → repeated benchmark → runtime evidence when required`

Benchmark evidence is never promoted directly to production certification.

## Cross-language scan integration

For migration work, every candidate language is evaluated through the same task family where the workload is comparable. A language lens may be Python, TypeScript, Rust, Go, or another supported paradigm, but the semantic authority remains the existing project owner.

Required migration evidence remains:

`reference → candidate → contract → differential → adversarial/error taxonomy → shadow → canary → rollback rehearsal → authority`

The benchmark can supply observations for the differential and tool/agent-compatibility stages; it does not replace the project's runtime migration gates.

## Agent-tree integration

The Explorer, Worker, Researcher, and Advisor roles use the same benchmark corpus. This permits testing whether delegation improves outcomes without assuming that delegation is always beneficial.

A benchmark run should identify the active role and whether an Advisor review occurred. Repeated errors and long-task completion should be benchmarked specifically because those are the project's advisor triggers.

## Public/private boundary

Foundation may retain public-safe benchmark contracts, schemas, deterministic fixtures, aggregate observations, and public artifacts.

Operations may retain private task corpora, protected runtime scenarios, and sensitive execution evidence. Private task data must not be copied into public Foundation artifacts.

Foundation owns benchmark workflow execution. Operations remains the protected runtime/policy/resource/evaluation authority and must not gain a competing GitHub Actions surface.

## Definition of done

The benchmark system is adopted when:

- the task matrix and schema are versioned;
- deterministic score computation is reproducible;
- the same corpus can be run across models and agent roles;
- repeated observations and provenance are retained;
- audit-inspired lanes are represented;
- hard-gate failures cannot be hidden by aggregate score;
- benchmark outputs are connected to issues/PRs without being treated as runtime certification.
