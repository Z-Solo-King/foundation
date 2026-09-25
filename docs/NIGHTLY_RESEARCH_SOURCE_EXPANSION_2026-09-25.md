# Nightly AI Research Source Expansion — 2026-09-25

## Purpose
This document records additional research material supplied for the 20-job nightly ecosystem research and project-native benchmark. These materials are design hypotheses and benchmark candidates, not automatic production architecture.

## Design patterns

### Persistent research memory / second brain
Separate raw evidence, structured wiki knowledge, generated outputs, context primitives, and identity/system memory. Research raw immutability, rebuildable derived knowledge, output provenance, cross-session retrieval, and an explicit learning edge from accepted results into future task briefs.
Targets: Foundation #1157, #157, #58.

### Token-efficient harness
Measure static prompt tokens, dynamic tokens, tool-definition share, cache hits, tool loading, file-backed results, compaction loss, subagent overhead, routing overhead, and cost per successful task. Prefer deterministic code for mechanical transformations.
Targets: Foundation #1157, #157; Operations #603, #597, #385.

### Typed decisions and mixture-of-schemas
Test whether structurally different agent states benefit from different typed decision schemas. Candidate benchmark regimes: ordinary routing, evidence conflict, recovery, migration/candidate selection, and high-risk authorization boundaries. Trading-specific thresholds are not imported into Heroic AI.
Targets: Foundation #1157; Operations #603, #385, #340.

### Regime-gated decision cascade
Benchmark a deterministic state classifier that decides whether a typed decision, expensive generative research, or code-only path is appropriate. Online state must not use hindsight-smoothed labels. Model outputs remain proposals inside allowed options.
Targets: Foundation #1157, #157; Operations #603, #340, #385.

### Loops versus graphs
Benchmark bounded produce-check-correct-repeat loops inside nodes and split/fan-out/merge/gate graphs between nodes. Test real dependency edges, isolated worker contexts, unit-level returns, bounded retries, correction edges, and long-term learning edges.
Targets: Foundation #1157, #58; Operations #385, #597, #699.

### Multi-agent orchestrator
Compare the existing Main/Explorer/Worker/Researcher/Advisor topology against specialized-agent patterns. Measure isolation, handoff loss, duplicate work, synchronization cost, recovery, and final task quality rather than assuming more agents are better.
Targets: Foundation #1157, #58.

### Resource governance / Kubernetes analogy
Use requests, limits, QoS, namespace defaults, aggregate quotas, overcommit, contention, reservation/settlement, reclaim, and quota-drift as benchmark dimensions for the existing resource-governance work.
Targets: Operations #145, #340, #385, #197.

## Reference repository corpus

AI / agents:
- https://github.com/Shubhamsaboo/awesome-llm-apps
- https://github.com/NipunaRanasinghe/awesome-ai-agents
- https://github.com/modelcontextprotocol/quickstart-resources
- https://github.com/rafska/Awesome-local-LLM
- https://github.com/typesafe-ai/skills
- https://github.com/typesafe-ai/typesafe-sdk-js
- https://github.com/typesafe-ai/typesafe-sdk-python
- https://github.com/PieroSierra/SecondBrain

Languages / migration:
- https://github.com/akullpp/awesome-java
- https://github.com/iluwatar/java-design-patterns
- https://github.com/TheAlgorithms/Java
- https://github.com/vinta/awesome-python
- https://github.com/TheAlgorithms/Python
- https://github.com/practical-tutorials/project-based-learning
- https://github.com/fastapi/full-stack-fastapi-template

System design / distributed systems:
- https://github.com/donnemartin/system-design-primer
- https://github.com/ByteByteGoHq/system-design-101
- https://github.com/ashishps1/awesome-system-design-resources

## Research rules
- Popularity, stars, README claims, vendor benchmarks, social posts, and attached diagrams are discovery evidence, not production authority.
- Verify current source state, version, license, maintenance, and failure behavior before using a repository as a migration or implementation reference.
- Compare official and community Jev integrations separately.
- Record confidence and eventual outcomes as paired observations when using typed decisions.
- Keep benchmark evidence separate from runtime/L4 evidence.

## 20-job nightly changes
The 20 jobs now have three curated seed repositories each in addition to live GitHub repository/issues/PR search and Reddit/X attempts. This prevents a successful GitHub search request returning zero repository rows from being treated as repository coverage.

New emphasis: graph decomposition, bounded correction, persistent research memory, token/cache efficiency, typed decision schemas, regime-gated routing, multi-language SDKs and migrations, resource governance, CI/artifact provenance, and security/fail-closed boundaries.

## Evidence boundary
External ecosystem observations remain research-signal evidence. They can propose deterministic benchmark candidates and experiments but cannot by themselves change production architecture, grant permissions, certify runtime behavior, or close an issue.

Promotion: research signal → deterministic benchmark candidate → independent reproduction → regression fixture → repeated benchmark → runtime evidence where required.
