# Research Intelligence Engine — Continuity Index

Status: September 13, 2026

This file exists so a future chat/session can recover the project state without reconstructing it from conversation history.

## Canonical architecture

- Foundation (`Z-Solo-King/foundation`): public-safe contracts, deterministic evidence/intelligence primitives, planner, public Worker, public CI.
- Operations (`Z-Solo-King/operations`): private chatbot/control plane, protected policy, credentials, provider/resource governance, evaluation/promotion, deployment.
- Historical extractor/mapper material: engineering lineage and compatibility evidence only unless explicitly promoted later.

## Constitutional invariants

1. Security/privacy/source-access policy wins.
2. Provider/platform policy wins over optimization.
3. Strict $0 is a hard economic gate; unknown billing/quota fails closed.
4. Provenance/integrity wins over convenience.
5. AI interpretation never becomes evidence authority alone.
6. Unknown, inaccessible, partial, stale, contradictory, inferred, blocked and error are distinct.
7. One behavior has one canonical owner.
8. Public-worker output is untrusted until schema/provenance/hash/replay/evaluation acceptance.
9. Source count is not independence.
10. Learning is observational, reversible and non-destructive.

## Current planner-design priority

**Feature/design completeness first; deep implementation second.**

Canonical planner documents:

- `docs/PLANNER_KNOWLEDGE_LEDGER_2026-09-13.md`
- `docs/PLANNER_FEATURE_BACKLOG_2026-09-13.md`
- `docs/PLANNER_ARCHIVE_REAUDIT_ADDENDUM_2026-09-13.md`

The planner must represent Task -> Claims -> Fact/Field requirements -> Evidence requirements -> Source-family targets -> Representation candidates -> Method candidates -> Resource reservations -> Conditional DAG -> Stop/escalation rules -> Expected observations -> Gap/recovery rules -> Replay fingerprint -> Evaluation criteria.

## Historical engineering lessons preserved

The personal extractor/mapper line contains useful behavior patterns: host profiles, representation discovery, bounded pagination, total-count reconciliation, completeness checks, repeated-page detection, per-host pacing/concurrency, failure classification, cooldown/quarantine, deterministic identifier-first mapping, variant separation, price/stock neutrality for identity, candidate blocking, recall telemetry, conflict detection, abstention, calibrated thresholds, reusable indexes, replay/backfill, and whole-pipeline benchmarks.

These patterns are generalized into contracts and planner requirements; the old implementations must not become a competing architecture.

## Universal-learning requirements preserved

- capability registry with version/health/policy/resource/failure history
- capability discovery when capability is missing
- sandbox -> regression -> benchmark -> shadow -> canary -> promote/rollback
- bounded cross-strategy evaluation
- continuous regression after code/routing/extractor/mapper changes
- file/code/data/media planning under the same Task/Observation/Evidence/Artifact/Evaluation contracts
- image/frame/table/PDF/audio/video evidence modes with provenance
- research snapshots and incremental refresh/diff
- temporal claim/document versions
- source-family lineage and poisoning defenses

## Stored source material

A persistent Library continuity folder was created at:

`/Research_Intelligence_Engine/Continuity/2026-09-13/`

It contains the seven uploaded AI-review text files and the uploaded universal-learning final plan. This preserves the user-supplied source material independently of the current chat.

## Deployment continuity

Historical live verification established that `/health` and `/readiness` can be green while the deployed Worker is stale. A 404 on the newly added infrastructure verification route is therefore deployment drift, not proof of source failure. Production completion requires current deployment, valid Cloudflare credentials/account configuration, live infrastructure verification, D1 verification and B2 round-trip evidence. Never infer production green from source tests alone.

## GitHub continuity

Foundation PR #21 is the current hardening/planner-knowledge branch. Public CI remains the preferred heavy test surface. Private GitHub Actions must not become a production compute dependency.

## Future-session rule

Before changing architecture or adding a planner feature, read this file plus the three planner documents above. Search the repository for an existing owner before creating a new implementation. Update the continuity ledger when a new durable architectural fact is discovered.
