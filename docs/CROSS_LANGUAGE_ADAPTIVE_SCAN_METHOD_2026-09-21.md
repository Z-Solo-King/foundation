# Adaptive Cross-Language Scan Method — 2026-09-21

## Purpose
This is the reusable scan-and-learning protocol for the Foundation + Operations family. It exists so every future audit improves both the codebase and the audit method.

## 1. Coverage
Start from a live recursive tree, not stale documentation.
Record repository and exact main SHA; total blobs and language/file-type counts; binary/unreadable exceptions; and deterministic path ranges for parallel lanes.
A wave is inventory-complete only when every current-tree path belongs to exactly one lane. Semantic confidence is reported separately; inventory coverage must never be confused with byte-for-byte rereading.
Python is mandatory in every wave because it remains the semantic/reference authority.

## 2. Parallel lenses
Use 3-4 non-overlapping lanes where possible. Give each lane a different programming-paradigm lens such as systems/ownership, typed functional/state algebra, actor/concurrency/supervision, and managed/runtime/stream/dataflow.
Do not let language choice determine the conclusion. The lens is a way to expose invariants, not an instruction to rewrite code.

## 3. Search method
Each lens performs: repository-wide invariant/pattern search; exact owner-module inspection; consumer and boundary inspection; test/PR/issue alignment; and adversarial edge-case review.
Use exact-path reads for confirmation and bounded searches for discovery. Reuse broad scans only after meaningful mutations or when the live tree changed materially.

## 4. Finding normalization
Map every candidate finding to one or more common categories: correctness/state algebra; security/trust boundary; resource/size/deadline/fan-out; configuration/diagnostics; concurrency/recovery/idempotency; evidence/provenance; migration/portability; maintainability/structure.
Reject findings that are merely stylistic unless they expose a concrete invariant, ownership, failure-mode or maintenance risk.

## 5. Nightly research learning
Nightly artifacts are evidence about the research pipeline itself. Preserve lane-level state, execution/preflight blockers, exact run and Operations revision, migration-review result, artifact publication state, baseline compatibility, and explicit evidence tier.
dry_run, blocked_before_execution, lane_failure, and live_research_executed are distinct states. A dry-run is never live research evidence. A single run may have multiple independent blockers.

## 6. Issue conversion
Create or modify an issue only when the finding has a canonical owner, a reproducible defect or explicit acceptance gap, a bounded proposed change, and a clear evidence rung.
Tag each issue with type and evidence status. Group issues only when they share the same authority and file surface. Do not collapse distinct acceptance requirements merely because one diagnostic can exercise both.

## 7. Migration gate
Candidate languages follow: reference -> candidate -> contract -> differential -> adversarial/error taxonomy -> shadow -> canary -> rollback rehearsal -> authority.
A candidate must show functional, security, policy, provenance, cancellation/deadline, resource, serialization and operational parity. Benchmark gains that disappear after conversion, FFI or runtime overhead do not justify promotion.

## 8. Strategy learning
After each wave, update reusable engineering rules, migration/portability guidance, issue/PR grouping rules, scan false-positive patterns, acceptance/evidence rules, and AI-agent handoff instructions.
This makes the repository progressively easier for humans and different coding agents to maintain.

## 9. Completion criterion
A scan wave is complete only when all current paths are assigned; all high-signal findings are classified; concrete defects have a canonical issue/PR or are explicitly rejected with rationale; migration candidates have a measured evidence plan; runtime-only blockers are preserved; and the method changes discovered in the wave are written back into canonical maintenance rules.