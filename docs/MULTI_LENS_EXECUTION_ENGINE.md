# Multi-Lens Execution & Audit Engine

**Status:** Proposed canonical execution standard  
**Date:** 2026-09-30

## Purpose

The project already uses cross-language scans, cross-repository checks, parallel lanes, provider comparison, browser-engine validation, and extractor-method diversification. This standard turns those techniques into a reusable execution engine.

> One target, many independent lenses, shared evidence, adaptive scheduling.

A lens is an independent way to inspect or execute the same target. Lenses must produce machine-readable evidence and must not silently become policy authority.

## 1. Lens families

| Family | Example lenses | Primary value |
|---|---|---|
| Language | Python, JavaScript, TypeScript, Rust, Go, PHP, shell | Finds language-specific blind spots and migration opportunities |
| Runtime | Worker runtime, Node, browser, edge, local | Detects environment-specific behavior |
| Browser | Chromium, Gecko/Firefox, WebKit, CDP, DOM, network/resource layer | Separates browser-engine failures from site/extractor failures |
| Extraction | HTML, XHR/fetch, API, REST, GraphQL, Store API, admin-ajax, sitemap, feed, browser-rendered | Increases acquisition coverage without overusing expensive browsers |
| Search | lexical, semantic, repository-native, web search, targeted code search, historical search | Improves evidence discovery and reduces repeated broad scans |
| AI provider | model A/B/C, provider A/B/C, deterministic/non-deterministic | Measures latency, quality, failure rate, quota and portability |
| GitHub | code, issues, PRs, comments, workflows, actions, releases, branches | Finds implementation and governance inconsistencies |
| Cloud | Worker, D1, KV, R2, Queues, Durable Objects, Browser Run, AI Gateway | Finds edge/runtime/configuration mismatches |
| Workflow | matrix, fan-out/fan-in, reusable workflow, cache, concurrency, artifact | Improves execution throughput and reproducibility |
| Evidence | static, dynamic, historical, runtime receipt, external corroboration | Prevents weak evidence from being treated as proof |
| Time | current, historical, regression, replay, longitudinal | Distinguishes regression from long-standing behavior |
| Failure | negative-path, timeout, quota, malformed input, provider outage, browser mismatch | Finds failure modes before happy-path optimization |
| Boundary | public/private, authenticated/unauthenticated, trust boundary, secret boundary | Prevents accidental authority or security boundary crossing |

## 2. New high-value audit patterns

### Cross-lens triangulation
Run different lenses against the same claim. A result is stronger when independent lenses agree.

### Cross-runtime replay
Execute the same bounded test in different runtimes. Compare output, timing, resource use and failure semantics.

### Cross-provider differential
Send the same normalized task to multiple AI/search providers. Compare structured fields rather than subjective prose alone.

### Cross-browser differential
Use the same acquisition contract against Chromium, Gecko and WebKit. Record engine-specific failures separately.

### Cross-method extraction ladder
Prefer cheap deterministic methods first, then escalate:
1. direct HTTP/static HTML
2. known API/feed endpoints
3. XHR/fetch/resource discovery
4. lightweight browser
5. full browser interaction

Never escalate merely because a method is available; escalate when prior evidence is insufficient.

### Cross-history regression replay
Re-run known failure cases after changes. A current green run does not invalidate historical failures.

### Cross-boundary audit
Test the same capability at each trust boundary: public surface, Worker, private operation, provider, storage and browser.

### Negative-space audit
Search for what should exist but does not: missing receipts, missing tests, missing bindings, missing fallbacks, missing provenance, missing cleanup, missing timeout handling.

### Metamorphic audit
Transform an input while preserving its expected semantic result. Examples: URL normalization, query-order changes, equivalent API representations and browser viewport changes.

### Mutation audit
Deliberately perturb configuration/code/data in a bounded test fixture and verify that the expected guard detects the mutation.

## 3. Adaptive lane scheduler

Every candidate lane receives:

- coverage_gain
- historical_yield
- confidence_gain
- failure_detection_probability
- execution_cost
- latency_cost
- quota_cost
- duplication_penalty
- freshness_need

The implementation uses a bounded weighted evidence value:

benefit = 0.23*coverage + 0.18*failure_detection + 0.14*confidence + 0.12*freshness + 0.18*novelty + 0.15*learning_quality

priority = benefit / (1 + budget_penalty + family_overlap_penalty)

Untested lanes receive a bounded exploration bonus. Required lanes, dependency closure, exclusive groups and declared budgets are hard scheduling constraints. A feasible=false plan must be surfaced rather than silently dropping required work.

This is a scheduling heuristic, not a correctness authority.

### Scheduling rules

1. Start with the cheapest high-yield lenses.
2. Run independent lanes concurrently when they do not mutate shared state.
3. Deduplicate equivalent evidence before launching another expensive lane.
4. Escalate only when the current evidence has an explicit insufficiency reason.
5. Stop a lane when its acceptance criterion is satisfied.
6. Continue a lane when it is producing novel evidence.
7. Record every skipped lane and why it was skipped.
8. Learn from completed receipts: update historical yield, latency and failure probability.
9. Never let historical success suppress a security/acceptance-critical lane.
10. Keep policy/authority separate from diagnostic observations.

## 4. Parallel execution topology

Use a fan-out/fan-in structure:

Target -> normalize -> select lenses -> parallel lanes -> evidence normalization -> dedupe -> contradiction check -> acceptance gate -> receipt

Recommended independent lane groups:

- L1: static/code
- L2: language/runtime
- L3: browser
- L4: network/extraction
- L5: provider/AI
- L6: GitHub/workflow
- L7: Cloudflare/runtime
- L8: historical/regression

The number of lanes is elastic. Six is a useful default; eight is appropriate for high-risk or cross-system audits.

## 5. Evidence contract

Every lane should emit:

- target identity
- lens identity/version
- immutable revision/input
- environment/runtime
- start/end time
- status
- observations
- artifacts/receipt references
- confidence
- limitations
- whether the result is authoritative, corroborative or diagnostic

A diagnostic browser result must not silently become feed acceptance. A provider response must not silently become policy. A historical result must not be presented as current.

## 6. Search-speed strategy

Speed should come from reducing unnecessary work, not from reducing coverage.

Use:

- repository-native exact search before broad scans
- targeted semantic search before full repository traversal
- file/path narrowing before content expansion
- cached immutable artifacts
- parallel independent queries
- result deduplication
- negative-result caching with freshness windows
- early stopping after acceptance criteria are met
- escalation only on evidence gaps
- provider/browser fallback only after bounded timeout
- historical knowledge to prioritize likely-yielding lenses

Measure time-to-first-useful-evidence, not only total runtime.

## 7. Browser and Cloudflare placement

Browser testing should be split into three dimensions:

1. Engine: Chromium / Gecko / WebKit.
2. Control protocol: Playwright / Puppeteer / CDP.
3. Execution location: GitHub runner / Cloudflare Browser Run / other approved runtime.

A failure should identify all three dimensions. Do not label WebKit evidence as Safari evidence; Safari-specific validation is a separate macOS/WebDriver concern.

Cloudflare Browser Run can provide browser execution, scraping and CDP access; use it as an execution lens, not as an automatic authority source.

AI Gateway/provider routing can similarly be treated as a provider lens: compare latency, error rate, retries, fallback behavior, cost and output quality from receipts.

## 8. AI/provider fleet

For the same normalized task, providers can be used in roles:

- primary executor
- independent verifier
- adversarial reviewer
- summarizer
- structured extractor
- fallback executor

Do not ask every provider to perform every task. Use task/provider capability history to select the smallest sufficient fleet.

## 9. Self-learning loop

After each completed run:

receipt -> normalize metrics -> compare expected/baseline -> update lens history -> update scheduler priors -> select next run

Learn only from verified observations. Do not learn from unvalidated model opinions.

Track per lens:

- success rate
- novel-finding rate
- false-positive rate
- median/p95 latency
- cost/quota consumption
- evidence acceptance rate
- regression detection rate
- failure classes
- last verified revision

The learner may change priority, never acceptance policy.

## 10. Safety/quality gates

No optimization may:

- bypass authentication or anti-bot controls
- turn a diagnostic path into an acceptance path
- weaken evidence requirements
- hide a failed lane
- silently retry indefinitely
- spend unbounded provider/browser quota
- mutate production state during an audit
- treat one provider or language as universally authoritative

## 11. Recommended audit recipes

### Fast triage
Static + targeted search + known regression cases.

### Standard change audit
Static + runtime + affected integration + historical regression + one independent verification lane.

### Deep audit
Six to eight parallel lanes including language, runtime, browser, extraction, provider, GitHub/CI, Cloudflare and historical regression.

### Migration audit
All source files covered by at least one primary lens; critical execution paths covered by multiple non-Python lenses; behavioral parity tested before replacement.

### Extraction audit
Cheap deterministic methods first; network/resource discovery second; browser-engine differential third; payload/provenance validation last.

### Production incident audit
Current runtime + logs/receipts + historical replay + provider differential + boundary audit.

## 12. Implementation order

1. Normalize existing audit receipts into one schema.
2. Add a lens registry with cost/capability/history metadata.
3. Add adaptive lane selection.
4. Add fan-out/fan-in orchestration.
5. Add evidence deduplication and contradiction detection.
6. Add browser-engine matrix.
7. Add provider differential matrix.
8. Add historical regression replay.
9. Persist lens performance history.
10. Periodically recalibrate scheduling from verified receipts.

This is deliberately additive: existing audit systems remain valid and become lenses under the common execution model.
