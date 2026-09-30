# Multi-Lens Execution Patterns

Date: 2026-09-30

This catalog extends the multi-lens engine with execution patterns that improve coverage without blindly multiplying work.

## Core patterns

| Pattern | What changes | Useful for |
|---|---|---|
| Cross-language | Same invariant inspected through different language/runtime paradigms | migrations, portability |
| Cross-runtime | Same fixture across Worker, Node, CI, browser, local | runtime drift |
| Cross-browser | Same contract across Chromium, Gecko and WebKit | browser/extraction defects |
| Cross-provider | Same normalized task across AI/search providers | resilience, quality, portability |
| Cross-protocol | Same capability through REST, GraphQL, XHR/fetch, CDP, direct HTTP | adapter consistency |
| Cross-version | Same test across revisions/releases/pins | regression and compatibility |
| Cross-boundary | Same operation across public/private/authenticated boundaries | trust and authority |
| Cross-data-shape | Equivalent payload representations | parser/schema robustness |
| Cross-cache-state | Cold, warm, stale and cache-miss paths | cache correctness and speed |
| Cross-history | Replay current and historical failure corpus | recurrence control |
| Cross-region | Different execution regions/POPs where runtime behavior can vary | edge routing and locality |
| Cross-tool | Equivalent task through independent tools | tool-specific blind spots |

## Differential and oracle patterns

**Differential testing:** compare a reference implementation against a candidate implementation and classify behavioral deltas.

**Metamorphic testing:** transform an input while preserving the expected semantic result, then compare normalized outputs.

**Invariant testing:** check properties that must always remain true, independent of the implementation.

**Mutation testing:** inject bounded faults into fixtures/configuration and verify that tests detect them.

**Adversarial testing:** deliberately exercise malformed inputs, boundary values, cancellation, timeouts, partial responses and conflicting evidence.

**Golden replay:** retain known-good and known-bad fixtures with immutable versions for deterministic replay.

## Execution-efficiency patterns

### Delta scan
Scan only the changed surface plus its dependency/consumer graph first. Expand to a repository-wide scan only when the dependency boundary is uncertain.

### Stratified sampling
For large site/provider/device inventories, partition by risk, implementation family, geography, traffic or historical failure class. Sample each stratum before broadening.

### Pairwise coverage
When a test matrix has many dimensions, cover every important pair of factor values before attempting the full Cartesian product. Use full coverage for acceptance-critical combinations.

### Adaptive escalation
Start with cheap deterministic acquisition and escalate to browser/provider execution only when evidence remains insufficient.

### Speculative/hedged execution
For latency-sensitive requests, begin a fallback only after a bounded latency threshold is exceeded. Never hedge unbounded or quota-sensitive work.

### Request coalescing
Collapse identical in-flight requests into one execution and fan the result out to waiting consumers.

### Evidence caching
Cache immutable evidence by content/revision digest. Apply explicit freshness TTLs to negative results and mutable external state.

### Backpressure
Bound concurrent browser sessions, provider calls, queue depth, response body size, retries and memory. Prefer bounded completion over unlimited fan-out.

### Circuit breaking
Temporarily remove a repeatedly unhealthy external provider from scheduling while retaining explicit failure evidence. Re-admit it only after a controlled health probe.

### Adaptive timeout
Estimate timeout thresholds from observed latency distributions rather than using one global timeout for every provider/browser path.

## Failure-isolation patterns

### Fault-domain isolation
Separate failures into code, test harness, toolchain, provider, network, browser, workflow, runtime and policy classes.

### Dependency blast-radius audit
When a shared component changes, enumerate direct and transitive consumers before deciding the minimum verification surface.

### Binary-search / delta-debugging
When a large fixture or change produces a failure, automatically reduce it toward the smallest reproducing case.

### Failure signature clustering
Group equivalent failures by normalized signature so one root cause is not opened as many duplicate issues.

## Evidence and observability

### Trace correlation
Assign one run identifier plus lane identifiers and propagate them through workflow, Worker, browser, provider and evidence receipts. OpenTelemetry context propagation is designed for carrying context across process/service boundaries; sensitive data must not be placed into untrusted baggage. Reference: https://opentelemetry.io/docs/concepts/signals/baggage/

### Evidence quorum
For high-value claims, require either one authoritative source or multiple independent corroborating evidence classes. Never use raw majority voting to resolve contradictions.

### Contradiction-first review
When independent lanes disagree, stop automatic promotion and inspect the exact revisions, evidence and acceptance contract.

### Freshness classification
Every result is marked current, historical, replayed or unknown. Historical evidence must never silently become current evidence.

### Provenance chaining
Every summary points back to exact input, revision, lane, artifact and source digests.

## AI-specific patterns

### Provider ensemble by capability
Choose providers by capability fit rather than one permanent “best” provider.

### Independent verifier lane
Use a separate model/provider or deterministic validator for important structured outputs.

### Output normalization
Compare structured fields, not only generated prose.

### Prompt perturbation
Change wording while keeping the task semantically constant to identify fragile model-dependent behavior.

### Model fallback ladder
Use bounded fallback across providers/models after explicit failure, timeout or admission conditions.

### Cost-aware admission
Treat quota, token cost and latency as scheduler inputs, while keeping acceptance criteria independent.

## Browser-specific patterns

### Engine differential
Chromium/Gecko/WebKit.

### Protocol differential
Playwright/Puppeteer/CDP where supported.

### Render-state differential
HTML-only, JavaScript-rendered, post-network-idle and post-interaction states.

### Device/viewport differential
Desktop/mobile/tablet or selected viewport classes when layout affects extraction.

### Session-state differential
Fresh context versus controlled persistent state. Do not replay secrets or clearance cookies into an acceptance lane.

Cloudflare Browser Run currently supports Browser Sessions using Playwright/Puppeteer/CDP and Quick Actions for stateless browser tasks. References:
- https://developers.cloudflare.com/browser-run/
- https://developers.cloudflare.com/browser-run/playwright/
- https://developers.cloudflare.com/browser-run/cdp/

## GitHub Actions patterns

Use matrix fan-out for independent lanes and a final fan-in job for synthesis. GitHub Actions supports matrix execution and max-parallel; use explicit concurrency bounds instead of assuming unlimited runner capacity.

Reference: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## Cloudflare durable-execution patterns

For work that must survive retries, pauses or long external dependencies, place orchestration in a durable workflow boundary and keep the individual evidence-producing steps idempotent.

Reference: https://developers.cloudflare.com/workflows/

## Anti-patterns to prohibit

- Cartesian-product explosion without coverage justification.
- Re-running the same files under several labels and calling that diversity.
- Starting expensive browsers before cheap deterministic checks.
- Retrying a failing provider forever.
- Treating one AI model as an authority.
- Treating a browser observation as acceptance evidence without payload validation.
- Letting the learner remove mandatory lanes.
- Mutating production while collecting audit evidence.
- Using undocumented policy hidden only in agent prompts.
- Calling a historical result current.

## Recommended composition

**Fast:** delta + exact search + known regressions.

**Standard:** delta + ownership + runtime + one independent corroborator + regression.

**Deep:** cross-language + cross-runtime + cross-browser + cross-provider + extraction + GitHub/workflow + Cloudflare + history.

**Migration:** reference + candidate + differential + adversarial + resource + shadow + canary + rollback rehearsal.

**Extraction:** HTTP/API -> XHR/resource -> browser -> payload validation -> provenance.

The engine should choose the smallest sufficient composition, then widen only when evidence gaps, contradictions, risk or freshness requirements justify it.
