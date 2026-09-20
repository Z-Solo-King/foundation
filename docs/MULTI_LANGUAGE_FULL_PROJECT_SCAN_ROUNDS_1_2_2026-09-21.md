# Multi-language full-project scan — rounds 1 and 2

Date: 2026-09-21
Repositories: Z-Solo-King/foundation and Z-Solo-King/operations

## Coverage basis
- Foundation main tree: 468 tracked blobs
- Operations main tree: 613 tracked blobs
- Combined inventory: 1,081 tracked blobs
- Python intentionally excluded from migration-lens scoring: 274 Foundation + 425 Operations blobs
- Non-Python tracked inventory at final coverage pass: 384 blobs total (current-tree inventory). Of these, 383 were UTF-8 text blobs semantically read by the machine coverage pass; one binary DOCX was inventoried but could not be decoded through GitHub's text file endpoint.

The scan treats Python as the existing reference authority. Cross-language findings do not create a second policy or semantic authority.

## Round 1 — Rust / TypeScript / Go / Java

### Rust lens
- Strong fit for deterministic parser and normalizer kernels.
- URL identity preserves credential-bearing URL userinfo and should reject or strip it before identity/hash generation.
- robots/sitemap parsing accepts positive infinity as crawl-delay; non-finite values should fail closed.
- Link-header parsing is deterministic but parity-oriented rather than full grammar compliant.
- Native candidates need explicit allocation, panic/abort and numeric-finiteness evidence.

### TypeScript lens
- Search adapters have no distinct CANCELLED failure class; caller cancellation becomes TIMEOUT.
- Adapter response.text() has no response-size ceiling before materialization.
- Search normalization has no hard post-normalization result-count/byte cap.
- SSE framing builds the complete payload and checks size only afterward.
- SSE maps every non-COMPLETE terminal state to partial.
- Frontend stream handling lacks explicit backend error/cancel events.
- Conversation history has per-message truncation but no aggregate byte/token budget.
- Router research matching uses a broad pathname includes rule instead of a segment-aware route boundary.

### Go lens
- Go fanout normal HTTP-error receipts are encoded concurrently without the synchronization used elsewhere.
- Worker count is not validated; zero or negative workers can deadlock the producer.
- Fanout uses client timeouts but no caller-scoped context propagation.
- Success responses are closed without draining the body first.
- Receipt order is nondeterministic and has no input sequence number.
- The benchmark's bounded worker model is useful but remains pilot-only.

### Java lens
- Open string/map state surfaces can be tightened using immutable versioned models.
- Future service boundaries should require executor caps, cancellation, deadlines and immutable request/receipt models.
- Java is a design-pressure lens, not a current migration target.

## Round 1 learning applied to round 2
1. Separate CANCELLED from TIMEOUT.
2. Apply byte/count/depth budgets before materialization.
3. Treat identity-bearing input as sensitive data.
4. Require structured concurrency and shutdown semantics.
5. Use closed terminal-state models instead of free-form strings.
6. Keep policy/provenance/resource authority centralized.

## Round 2 — C++ / C# / Kotlin / Zig

### C++ lens
- Treat full-body SSE construction as an ownership/lifetime problem; bounded streaming writers are safer.
- Concurrent result emission needs an explicit serialization boundary.
- Native candidate APIs should use explicit ownership transfer and bounded buffers.

### C# lens
- Stream protocol should use a closed terminal-event model: Start, Delta, Usage, Completed, Partial, Cancelled, Error.
- Canonical request context should carry cancellation explicitly.
- Request and response envelopes should be immutable/versioned.

### Kotlin lens
- Research/chat states are better modeled as a closed state machine with legal transitions.
- Queue/background work should follow structured cancellation.
- Unknown terminal events must never silently degrade into partial.

### Zig lens
- Candidate parsers/serializers should expose explicit allocation and output budgets.
- Optional/malformed/non-finite values should be explicit error states.
- Compile-time configuration is a useful design principle for central limits such as body size, events, pages and queue depth.

## Cross-language candidate matrix

| Surface | Lens | Status |
| --- | --- | --- |
| URL canonicalization | Rust | Continue differential pilot; reject credential-bearing URLs and non-finite policy values |
| Deterministic parser kernels | Rust | Continue profiling/parity |
| Public edge routing | TypeScript | Continue shadow; tighten path matching |
| SSE serialization | TypeScript + C# + Kotlin | Continue shadow; explicit terminal-event union |
| Search adapters | TypeScript | Continue shadow; add cancellation/resource/credential transport gates |
| Browser acquisition | TypeScript | Continue shadow; keep origin/size/cancellation policy centralized |
| Fanout gateway | Go | Benchmark-only until context, worker validation, body lifecycle and deterministic ordering are fixed |
| Orchestration/state authority | Java/C#/Kotlin lens | Keep Python authority; use typed schema ideas without migration |
| Native parser kernels | C++/Zig lens | Future only; high-risk native rules apply |

## Policy and logic improvements
- Make CANCELLED distinct from TIMEOUT.
- Require every streaming transport to declare a terminal-state algebra.
- Require every transport/parser to declare maximum bytes, results, depth and retry budget before materialization.
- Reject or redact credential-bearing identifiers at normalization boundaries.
- Require concurrent lanes to declare cancellation, queue, worker, ordering and shutdown semantics.
- Require segment-aware route matching.
- Require candidate serializers to preserve explicit error classes.

## Feature and architecture ideas
1. Generate language-neutral versioned contract types from one canonical schema.
2. Add a deterministic Outcome model with CANCELLED, TIMEOUT, BLOCKED, RATE_LIMITED, ERROR, PARTIAL and COMPLETE.
3. Add a common BudgetEnvelope for bytes, items, pages, queue depth, retries, elapsed time and allocation.
4. Add sequence numbers to concurrent receipts for deterministic replay comparison.
5. Add a CapabilityMatrix connecting owner, policy domains, evidence modes, language lens and promotion rung.
6. Add generated contract checks so candidate languages cannot invent independent serialization taxonomies.

## Existing issues receiving these findings
- Foundation #452
- Foundation #157
- Operations #597
- Operations #603
- Operations #352
- Operations #340

No candidate receives production authority from the scan. Promotion remains reference -> candidate -> differential -> shadow -> canary -> authority.


## Final machine coverage pass

The final pass re-read all 384 current-tree non-Python blobs by path. 383 UTF-8 text blobs were content-read; the single binary DOCX remained inventory-only because the connector cannot decode binary content. No non-Python text path was skipped. The machine pass established path/content coverage; semantic review and findings focused on polyglot implementation surfaces plus policy, workflow, architecture, issue and migration-contract material. Python remained intentionally outside migration scoring.
