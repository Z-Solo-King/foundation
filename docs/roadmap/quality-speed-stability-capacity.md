# Quality, Speed, Stability & Useful-Output Roadmap

Status: planning contract. Implementation and production acceptance remain separate gates.

## Goals
- Maximize useful completed work, not raw request/token throughput.
- Keep correctness, evidence, completeness and safety as hard constraints on performance optimization.
- Make latency explainable and regressions measurable.
- Preserve the L1/L2/L3/L4 evidence boundary.

## Foundation workstreams

### 1. Answer completeness
Track requested, completed, missing, failed, unsupported and evidence-backed scope.

### 2. Claim-to-evidence verification
Map each material claim to evidence, source passage, provenance, timestamp/freshness and verification state. Detect unsupported, partial, stale and mismatched citations.

### 3. Evidence quality
Evaluate authority, freshness, directness, corroboration, extraction reliability, completeness, contradiction state and citation precision independently.

### 4. Contradiction handling
Preserve conflicting observations and determine whether differences arise from variant, region, timestamp, revision, method or genuine contradiction before synthesis.

### 5. Performance observability
Measure queue, routing, authentication, cache, retrieval, parsing, research, model, persistence, serialization and streaming stages. Track TTFB, time-to-evidence, time-to-final and p50/p90/p95/p99.

### 6. Useful-completion efficiency
Benchmark quality-qualified completed work per resource unit. Report correctness, completeness, evidence coverage, freshness, latency, cost and reliability independently rather than hiding regressions behind one score.

### 7. Continuous adversarial evaluation
Maintain deterministic and approved real-source/oracle workloads for stale evidence, contradictions, incomplete retrieval, citation mismatch, malicious source content, prompt injection, large result sets, concurrency, dependency failure, replay and cancellation.

### 8. Reproducible execution identity
Version schemas, policies, router/planner, retriever, mapper/extractor/adapters, provider/model identity and evidence/source fingerprints so equivalent runs can be compared.

## Hard rules
1. Faster is not acceptable if correctness/evidence/completeness materially regresses.
2. Cheaper is not acceptable if quality gates are bypassed.
3. Citation presence does not prove citation correctness.
4. Incomplete work must be represented as incomplete.
5. Stale evidence must not appear current.
6. No opaque aggregate score may hide a critical dimension regression.
7. Repository evidence cannot be represented as private-runtime or production evidence.
8. Every benchmark records workload, population, environment and baseline.

## Related issues
- #385 Research answer completeness and claim-to-evidence verification contract
- #386 Contradiction resolution and evidence-quality evaluation framework
- #387 Latency decomposition, useful-completion efficiency and performance regression gates
- #388 Continuous adversarial evaluation and release-quality regression gates
- #389 Versioned execution provenance manifest and reproducible answer identity
