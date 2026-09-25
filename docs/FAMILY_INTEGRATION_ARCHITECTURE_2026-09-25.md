# Family Integration Architecture — 2026-09-25

**Status:** CURRENT  
**Canonical machine-readable map:** `docs/FAMILY_INTEGRATION_GRAPH.json`  
**Purpose:** connect the whole Heroic AI family without creating duplicate authority.

## Integration spine

```text
USER
  ↓
Foundation UI
  ↓
Foundation public HTTP / Worker contract
  ↓
Operations private routing / policy
  ├──→ chatbot / provider stream / idempotency
  ├──→ research / acquisition / extractor / mapper
  └──→ resource admission / reservation / recovery
  ↓
evidence + provenance + result state
  ↓
Foundation benchmark + nightly research
  ↓
CI artifacts / issue evidence / current-state docs
  ↓
AI Analysis Map + Family Sync State
  ↺ research learning loop
```

## Why this exists

The supplied material repeatedly describes the same system property from different angles: the model, tools, memory, orchestration, code, UI, resources, security, configuration, observability and evaluation work best when each has a clear responsibility and every boundary carries typed, traceable state.

The family already has most of these pieces. This graph makes their relationships explicit so a change in one surface can be traced to the affected contracts, tests, benchmark probes, documentation and acceptance gates.

## Canonical ownership

| Surface | Owner | Primary contract |
|---|---|---|
| Public contracts / CI / deployment | Foundation | family/public contracts |
| AI navigation | Foundation | AI Analysis Map + repository maps |
| Research planning/evidence structures | Foundation | research contracts |
| Benchmark | Foundation | six-lane benchmark + observation envelopes |
| UI / client lifecycle | Foundation | frontend UI/lifecycle contracts |
| Acquisition / extraction / mapping | Operations | extractor-mapper contracts |
| Chatbot / provider streaming | Operations | private chatbot/provider contracts |
| Resource accounting | Operations | durable resource ledger |
| AI/model/tool policy | Operations | governance/capability contracts |
| Runtime recovery / verification | Operations | private runtime boundary |
| Runtime evidence | Split by boundary | runtime evidence ownership matrix |

## Material-derived benchmark ideas

### Memory
Use persistent raw evidence, structured knowledge and retrievable history as separate concepts. Do not let generated summaries overwrite ground truth. Test retrieval reuse and cross-session continuity.

### Token efficiency
Measure request assembly, static context, tool schemas, cache behavior, large tool outputs, compaction, subagents and routing. Optimize the harness rather than instructing a model to “use fewer tokens.”

### Typed decisions
Test narrow decision schemas where the answer space is explicit. The decider proposes a bounded action; deterministic code owns authorization, risk and execution.

### Loops and graphs
A loop verifies a bounded unit. A graph determines dependency shape. Remove artificial sequential edges and return only failed units for correction.

### Resource governance
Translate requests/limits/QoS/quota/overcommit into the existing reservation, settlement, reclaim and reconciliation contracts. Resource truth remains a single Operations authority.

### Security/configuration/observability
Keep identity, secrets, runtime restrictions, network policy, immutable configuration and telemetry as separate boundaries that connect through traceable execution identity.

### Model selection
Use task-fit observations, not a static model leaderboard. Compare quality, latency, token cost, tool efficiency and recovery on identical fixtures.

### Migration
Treat Java/Python/frontend/backend/system-design repositories as reference corpus only. A language becomes an actual migration candidate only after parity, performance, conversion, shadow/canary and rollback evidence.

## Promotion rule

```text
research signal
  → deterministic benchmark candidate
  → independent reproduction
  → regression fixture
  → repeated benchmark
  → runtime evidence where required
  → issue / docs / AI-map update
```

A social post, diagram, repository star count, README claim or vendor benchmark can suggest a test. It cannot certify runtime behavior or close a production acceptance gate.

## Non-goals

This architecture does not:
- create a second resource ledger;
- move Operations policy into Foundation;
- make the research-memory scaffold live by documentation alone;
- import financial/trading parameters into Heroic AI;
- treat frontend transport state as execution truth;
- replace the existing six-lane benchmark or evidence ladder.

## Maintenance

Every material change should answer four questions:

1. Which node owns the behavior?
2. Which edge/contract changes?
3. Which focused test and benchmark probe cover the change?
4. Which issue/document/evidence record must be synchronized?

The machine-readable graph is an AI navigation and cross-surface coordination aid, not a competing authority.
