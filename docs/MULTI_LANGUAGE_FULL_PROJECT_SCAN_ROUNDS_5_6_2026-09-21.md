# Multi-language full-project scan — rounds 5 and 6

Date: 2026-09-21
Repositories: Z-Solo-King/foundation and Z-Solo-King/operations

## Coverage
- Initial round-5/6 live-tree inventory at scan start: Foundation 469 blobs; Operations 614 blobs; combined 1,083.
- Python was included in inventory and analysis.
- Operations has one binary DOCX; inventory-covered but not text-decoded by the connector.
- Batch 5 directional coverage: Scala = Foundation forward 0–234; Clojure = Foundation reverse 235–468; Dart = Operations forward 0–306; Nim = Operations reverse 307–613.
- Batch 6 directional coverage: OCaml = Foundation forward 0–234; Lua = Foundation reverse 235–468; Crystal = Operations forward 0–306; D = Operations reverse 307–613.
- Repository-wide code-search was used for each lens, followed by direct inspection of high-signal surfaces. This is 100% current-tree inventory/path coverage plus repository-wide pattern coverage; it is not claimed as four-way byte-for-byte rereading of every file.

## Lessons from nightly benchmark/artifact testing
- blocked_before_execution must remain a first-class state.
- Failure artifacts are evidence and must preserve run ID, revision, lane state and blocker.
- Dry-run/simulation is never live research evidence.
- Baseline compatibility and evidence tier must be explicit; NO_BASELINE is truthful.
- Stale private-repository pins can cause unrelated deterministic failures and must be freshness-checked.
- One nightly run can contain multiple independent blockers; diagnosis should preserve each blocker.

## Round 5 findings

### Scala — Foundation
- Research execution state remains a raw string in backend/execution/engine.py.
- Its local state algebra omits blocked, partial and cancelled even though wider contracts use them.
- backend/publication_gate.py has a typed PublicationOutcome but raw execution/claim/freshness strings.
- backend/execution/worker_boundary.py has immutable envelopes but raw WorkerResult.status.
- Recommendation: one canonical closed lifecycle/outcome algebra plus immutable versioned envelopes.

### Clojure — Foundation
- backend/execution/worker_boundary.py uses process-local mutable replay/active-task maps under RLock.
- Such state must remain explicitly non-authoritative; durable replay truth belongs to the persistence authority.
- Broad internal exceptions at API/auth boundaries can collapse structured failure classes into generic errors.
- Recommendation: return typed failure data internally, redact only at the public boundary, and mark process-local coordination explicitly non-authoritative.

### Dart — Operations
- private/chatbot/provider_stream.py has a strong closed stream-event algebra and sequence checks.
- It still accumulates all output fragments and joins the full output at finalization; event/delta limits exist, but there is no explicit aggregate output-byte budget.
- private/chatbot/live_answer.py silently drops malformed provider-runtime configuration entries.
- scripts/site_benchmark_daemon.py is an endless poll loop without an explicit supervisor/shutdown/heartbeat contract.
- Recommendation: explicit stream aggregate budget, parse-failure receipts, and daemon lifecycle ownership.

### Nim — Operations
- private/chatbot/durable_runner.py correctly bounds shards/workers/retries and uses atomic enqueue.
- Serialization/materialization can occur before all size limits are enforced; input-size limits are less explicit than metadata/output limits.
- Recommendation: input/output/parser budgets before unbounded materialization.

## Round 6 findings

### OCaml — Foundation
- backend/execution/engine.py::ResearchRun is the clearest sum-type candidate.
- Transition logic only allows planned -> running -> completed/failed, while wider contracts carry partial/blocked/cancelled.
- Recommendation: one exhaustive transition table to prevent divergent local state machines.

### Lua — Foundation
- backend/core/workers_runtime.py has distinct Workers SDK versus JS Fetch/FFI paths, but capability mode is inferred from imports rather than represented in a receipt.
- Dynamic runtime/provider configuration should preserve malformed/unknown entries as explicit diagnostics where they affect protected execution.
- Recommendation: explicit capability/runtime-mode receipt and sandbox/capability boundary.

### Crystal — Operations
- private/resource_ledger.py::ResourceLedgerSnapshot is a frozen dataclass containing mutable dictionaries. The container is frozen, but callers can still mutate the dictionaries.
- This is a concrete immutability leak.
- Recommendation: immutable mappings or defensive copies for exposed snapshots.

### D — Operations
- private/chatbot/provider_retry.py has strong bounded arithmetic/deadline semantics.
- private/chatbot/live_answer.py silently skips malformed provider-state records and invalid provider names.
- private/recovery_action.py is comparatively strong: closed enums, bounded recovery chains, budget validation and rollback requirements.
- Recommendation: convert malformed protected configuration into explicit configuration-error evidence rather than silently discarding it.

## New cross-cutting candidates
1. Canonical LifecycleState/Outcome contract shared by execution, publication, streaming, benchmark and recovery.
2. ImmutableSnapshot contract; prohibit raw mutable dict/list fields in externally visible frozen records.
3. ConfigurationParseReceipt containing accepted entries, rejected entries, reasons and configuration digest.
4. AggregateStreamBudget for total output bytes, events, elapsed time and tokens.
5. InputMaterializationBudget covering request size, JSON encoding, parser depth, item count and output materialization.
6. RuntimeCapabilityReceipt distinguishing Workers SDK vs JS Fetch/FFI execution mode.
7. MultiFailureNightlyDiagnosis preserving separate research-preflight, migration-review, artifact-validation and final-gate failures.

## Issue alignment
Foundation: #157, #58, #452.
Operations: #340, #352, #385, #603, #650, #145.

No language receives production authority from these scans. Promotion remains reference -> candidate -> differential -> shadow -> canary -> authority.

## Post-scan implementation reconciliation — 2026-09-21

- Foundation #915 closed the runtime capability-receipt gap identified by the Lua lens.
- Operations #650 closed the Go fanout pilot defect set with bounded worker count, caller cancellation, response draining and deterministic sequencing.
- Operations #655/#665 closed the nested-mutation leak in ResourceLedger snapshots.
- Operations #656/#661 moved malformed provider configuration handling into explicit, centralized diagnostics.
- Operations #657 closed the aggregate stream-output budget gap.
- Foundation #909/#910 remain the active lifecycle/materialization defects; implementation PR #921 addresses both.
- Nightly lessons remain normative: multi-blocker diagnosis, truthful execution states, explicit evidence tiers, stale-pin checks, and no dry-run-as-research.

No language received production authority from rounds 5-6. Future waves must preserve full inventory coverage, vary paradigms, explicitly include Python, normalize findings into common invariant categories, and record false-positive/methodology learning after every wave.

## Final reconciliation after implementation and documentation merges — 2026-09-21

Final live tree after all round-5/6 changes:
- Foundation: 472 blobs, 275 Python files.
- Operations: 620 blobs, 429 Python files.
- Combined: 1,092 blobs, 704 Python files.

Completed implementation outcomes:
- Foundation #909/#910 closed after merged #921 and green required checks.
- Operations #650, #655, #656, #657, #661 and #665 are closed with their concrete scan-derived fixes merged.
- Foundation #915 runtime capability-receipt gap is closed.
- The adaptive cross-language scan methodology is now durable in canonical agent/documentation guidance.

The original 1,083-path count remains the coverage baseline for the scan wave itself; the 1,092-path count is the post-merge live-tree state. Future scans must start from the new live inventory.
