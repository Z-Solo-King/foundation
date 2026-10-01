# Source Decomposition Baseline — 2026-10-01

## Rule

Production/runtime code and workflow definitions are decomposed when they become difficult to reason about as a single responsibility. Critical thresholds are >50,000 bytes or >1,000 lines; attention thresholds are >25,000 bytes or >500 lines. Historical archives and evidence datasets are not split merely to satisfy size metrics.

## Current critical code/workflow surfaces

| Repository | File | Approx. size | Lines | Action |
|---|---|---:|---:|---|
| Foundation | `.github/workflows/hybrid-language-pilots.yml` | 63.9 KB | 1,571 | split by language/capability lane, preserve Foundation as sole hosted authority |
| Foundation | `scripts/production_release.sh` | 59.5 KB | 961 | split release phases/helpers, retain one canonical entrypoint |
| Foundation | `tools/woocommerce_v175_plugin_fingerprint_22.py` | 55.8 KB | 1,303 | split domain modules; compatibility facade |
| Foundation | `.github/workflows/nightly-multi-agent-research-v3.yml` | 52.9 KB | 1,013 | split preflight/execution/materialization/diagnosis |
| Foundation | `tests/test_public_admission_store.py` | 39.0 KB | 1,235 | split tests by admission/quotas/concurrency/persistence |
| Operations | `private/control_plane_diagnostics.py` | 53.6 KB | 1,090 | split diagnostics by persistence/chatbot/provider/infrastructure/evaluation |
| Operations | `private/runtime_language_policy.py` | ~50.1 KB | 1,008 | split now into fit/artifact/AI-maintainability modules |
| Operations | `tools/exhaustive_audit.py` | 45.5 KB | 861 | split audit lanes/common helpers |
| Operations | `private/chatbot/live_answer.py` | 34.5 KB | 728 | split acquisition/evidence/composition/fallback |
| Operations | `tools/open_issue_polyglot_scan.py` | 27.8 KB | 565 | attention; split query, scan, reconciliation |
| Operations | `tools/run_mapper_runtime_evidence.py` | 27.5 KB | 376 | attention; split evidence collection/validation/report |
| Operations | `private/feed_recovery/woocommerce_google_feed_rescue_fast.mjs` | 27.5 KB | 567 | attention; split recovery strategies |
| Operations | `private/durable_resource_ledger.py` | 26.5 KB | 509 | attention; split reservation/accounting/reconcile |
| Operations | `tools/woocommerce_32_plugin_feed_hunt.mjs` | 21.5 KB | 186 | attention by bytes; split only if domains stabilize |

## Already decomposed in this pass

`operations/private/runtime_language_policy.py` is now a compatibility facade. Its implementation is divided into `language_fit_policy.py`, `migration_artifact_policy.py`, and `ai_maintainability_policy.py`. The original import path remains stable.

The split is responsibility-aligned: runtime selection, migration artifact metadata, and AI-maintainability are different dimensions and should not share one 1,000-line implementation file.

## Coupling rule

A split module may not become a new authority merely because it becomes a new file. The public facade, integration contract, existing policy registries, and promotion authorities remain canonical.

## Next decomposition wave

The next wave should address the Foundation workflow/release monoliths and Operations control-plane/audit monoliths. Each split must preserve imports, workflow authority, receipts, policy checks, and rollback behavior; no blind line-moving refactor is accepted without static/runtime evidence.


## 2026-10-01 decomposition update
The control-plane diagnostics monolith was split: the facade remains the stable route/import surface while the large infrastructure verification orchestration moved to Operations `private/control_plane_infrastructure.py`. The extracted module is below the critical source-size thresholds. The split is dependency-injected so facade-level test seams remain usable.