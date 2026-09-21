# Cross-Paradigm Scan and Learning Protocol

**Status:** normative family maintenance method

This protocol turns broad language scans and nightly research into reusable engineering improvements. It applies to bug fixing, feature work, security review, policy review, migration, performance work, and acceptance planning.

## 1. Coverage before conclusions
1. Build a current-tree inventory from the exact target revision.
2. Record total blobs, source-language counts, generated/vendor exclusions, and unscanned binary files.
3. Split coverage into non-overlapping deterministic ranges or component ownership lanes.
4. Include Python even when another language is the scan lens.
5. Use repository-wide symbol/pattern search plus targeted semantic reads; never claim byte-for-byte reread when that was not performed.
6. Re-resolve stale paths from the current codemap before inspection.

Coverage is evidence about where we looked, not evidence that a finding is correct.

## 2. Cross-paradigm lenses
Use at least four materially different lenses per wave when practical:
- typed/sum-type language: state algebra, invariants, exhaustive transitions;
- concurrent/service language: ownership, cancellation, bounded fan-out, response lifecycle;
- functional language: purity, immutability, deterministic decisions, explicit errors;
- systems language: allocation, integer/finiteness bounds, ownership, panic/abort behavior;
- actor/runtime language: supervision, restart, shutdown and failure ownership;
- scripting/dynamic language: configuration parsing, runtime capability detection, coercion and diagnostic visibility.

A language finding is a candidate lens, never an authority transfer.

## 3. Finding normalization
Normalize each finding into:
`component -> behavior -> risk -> evidence -> canonical owner -> regression -> issue -> promotion impact`

Classify the problem before editing:
`contract | correctness | security | policy | resource | observability | recovery | migration | tooling | acceptance`

Prefer cross-cutting invariants discovered by multiple lenses over isolated style recommendations.

## 4. Learning extraction
Every meaningful scan wave must answer:
- Which existing rule prevented this defect?
- Which rule was missing, ambiguous, or unenforced?
- Which regression test would have caught it earlier?
- Which agent/tooling assumption made discovery harder?
- Which repository structure made ownership unclear?
- Which acceptance rung is affected?
- Can the lesson be converted into a deterministic policy, test helper, benchmark fixture, codemap rule, or AGENTS instruction?

The default output is not another prose note. It is one or more durable controls.

## 5. Migration discipline
For any language candidate:
`reference -> contract fixture -> candidate -> differential -> malformed/adversarial -> performance -> shadow -> canary -> authority`

Python remains the protected semantic/policy/persistence/provenance/replay/rollback authority until the full promotion gate passes.

Promotion evidence must separately prove functional, security, policy/zero-cost, provenance, error/terminal-state, cancellation/deadline and bounded-resource parity; deterministic replay; conversion/serialization cost; relevant p50/p95/p99 and memory evidence; rollback; and retirement conditions.

A passing benchmark does not authorize promotion.

## 6. Nightly-research learning
Nightly artifacts must distinguish:
`not executed | blocked before execution | lane failure | dry-run | live research`

Independent blockers must remain individually visible. An aggregate failure state must never erase the migration-review, research-preflight, lane-execution, artifact-validation, or final-gate cause.

Dry-run output is coverage/test evidence, not empirical research evidence.

## 7. Queue learning
Use a rolling scheduler:
`discover -> classify -> reserve non-overlapping lane -> mutate -> validate -> update issue -> rescan`

Keep 3–4 independent lanes available. When one lane blocks, work-steal an independent lane. After every 3–5 meaningful mutations, refresh the affected issue/PR slices and then rescan the broader queue.

Issue count is not the objective. The queue is complete only when every remaining item is actionable elsewhere, externally/runtime gated, duplicate/superseded, or explicitly deferred.

## 8. Evidence honesty
Use the family ladder:
`repository contract -> deterministic test -> CI -> integration -> runtime -> production`

Never upgrade one rung into another by wording, screenshots, simulation, or historical receipts.

Every acceptance record should preserve:
`revision | authority | execution identity | checks | environment | result | remaining evidence`

## 9. Agent portability
Keep behavior discoverable without chat history:
`family contract -> codemap -> canonical module -> consumers -> owner tests -> boundary tests -> benchmark/receipt`

Prefer versioned contracts, deterministic fixtures, bounded context, exact-path reads, stable command lines, and model-neutral instructions. A language or coding-model migration must not require changing the underlying business contract.

## 10. Closure loop
Every scan finding should end in one of:
`fixed + regression | policy rule added | benchmark/fixture added | migration candidate tracked | runtime gate documented | rejected with reason`

Do not leave a finding only in a chat transcript.
