# Research Intelligence Engine — Requirement Coverage Reconciliation

**Status:** CURRENT_AUDIT
**Owner:** Foundation family synchronization boundary
**Audit date:** 2026-09-17
**Repository baseline:** Foundation `main` `e91123ade520b4fe2017ffd4e9cd8433ed56fa07`
**Operations baseline observed by this audit:** `a36868df86575e3b8abd857035af657dc84e3f6a`
**Approved Operations production revision:** `cf28a28cb40de527aff1cd87f96e103669635f70`
**Nightly research revision currently pinned by Foundation workflow:** `b6a519742e57e7e68db64ab10535d76372bcbdb1`

## Purpose

This record is the current implementation reconciliation of the source-plan coverage matrix against the live GitHub repository trees. It does not replace the historical source-plan matrix; it corrects implementation/evidence interpretation where repository source inspection shows that a capability is a primitive, a partial integration, or an execution gate rather than a completed end-to-end feature.

**100% requirement coverage means every requirement has an explicit owner, implementation disposition, evidence level and remaining gate. It does not mean every requirement is already production-verified.**

## Uniform status

- `CURRENT` — implementation exists on the referenced merged revision and matches its documented owner.
- `INTEGRATION-GATED` — required primitives exist but the canonical cross-module path is not complete.
- `RUNTIME-GATED` — repository capability exists but L3/L4 execution evidence is still required.
- `EXTERNAL` — outside the GitHub repository boundary.
- `OBSOLETE` — superseded or explicitly prohibited.

## A. Constitution and ownership

**Status: CURRENT.**

Foundation and Operations remain the only active repositories. The former extractor/mapper repository is historical. Canonical ownership is split between Foundation public contracts/deterministic evidence primitives and Operations private control/runtime.

## B. Research contract and planning

**Status: CURRENT / INTEGRATION-GATED.**

`ResearchContract`, query/source-family planning, field routing and protected resource reservation primitives exist. Foundation's public research submission still creates a run and accepts permitted source URLs; it does not itself execute the complete research pipeline.

## C. Acquisition and extraction

**Status: CURRENT / INTEGRATION-GATED.**

Operations has bounded public acquisition, redirect/retry/body limits, generic structured-data extraction and deterministic identity gating. The identity gate is wired into the generic mapping path. End-to-end research orchestration still needs to connect acquisition/output into the complete evidence and publication lifecycle.

## D. Evidence and verification

**Status: CURRENT / INTEGRATION-GATED.**

The evidence graph schema, certificates, lineage, contradiction handling, freshness semantics and verification primitives exist. The current public research ingestion path persists sources/document versions/observations but does not yet traverse evidence spans → claims → verification → synthesis as one complete production research execution path.

## E. Evaluation and promotion

**Status: CURRENT / RUNTIME-GATED.**

Evaluation receipts, baseline comparison, adjudication, protected shadow/canary/promotion/rollback primitives exist. The remaining gap is wiring them to a real production-shaped research run and retaining current L3/L4 evidence.

## F. Artifacts, snapshots and recovery

**Status: CURRENT / INTEGRATION-GATED / RUNTIME-GATED.**

Replay/checkpoint and persistence primitives exist. The current `ArtifactManifest` is a minimal immutable hash/provenance record; the full plan's richer tool/model/input/contract/retention lineage is not yet represented as one canonical manifest contract. B2 and disaster-recovery certification remain runtime gates.

## G. Capability intelligence and self-improvement

**Status: CURRENT / RUNTIME-GATED.**

Capability catalog, source/limitation observations, lifecycle stages and promotion policy exist. Broad autonomous capability acquisition and production mutation remain intentionally bounded. Runtime qualification remains evidence-gated.

## H. Multimodal capability surface

**Status: CATALOG-CURRENT / EXECUTION-PARTIAL.**

Capability descriptors exist for files, documents, PDF, spreadsheets, images, archives, media and generation. The catalog is not equivalent to an active production adapter. Non-active descriptors remain roadmap/candidate records.

## I. Community and multilingual ecosystems

**Status: POLICY-CURRENT / RUNTIME-GATED.**

The project has explicit policy/contracts for Reddit, GitHub, YouTube, marketplaces and Chinese/community source families. Broad real-source qualification is still an execution/evidence gate and no unrestricted access bypass is implied.

## J. Frontend and user lifecycle

**Status: CURRENT / INTEGRATION-GATED.**

The chat frontend is connected to the authenticated Operations conversational path with SSE lifecycle handling. Research UI lifecycle is connected to the Foundation research API and source-ingestion persistence, but the backend does not yet provide the complete discovery→evidence→synthesis research path.

## K. Chatbot control graph

**Status: CURRENT for source implementation; RUNTIME-GATED for L4.**

The authenticated chatbot route, trust boundary, prompt-injection handling, provider policy, durable model-call resource governance, token accounting, streaming and idempotency are present in canonical Operations modules. Current approved runtime evidence remains separate.

## L. GitHub governance and deployment

**Status: CURRENT / RUNTIME-GATED.**

The active `Protect main` ruleset, required checks, deployment workflow ownership and SHA-pinned Actions are current. Empirical `merge_group` execution, administration-only secret-scanning/push-protection verification and fresh canonical production execution remain separate gates.

## M. Cloudflare / B2 / ChatGPT platform state

**Status: EXTERNAL.**

This GitHub synchronization record does not certify Cloudflare production, D1 bindings, Worker runtime state, B2 remote restore, or ChatGPT connector publication. Those require their dedicated operational evidence paths.

## N. Extractor/mapper lineage

**Status: CURRENT.**

The historical extractor/mapper repository is not a third runtime authority. Operations retains the implementation family and compatibility facades, while deterministic product mapping authority remains in Foundation public core.

## O. Obsolete architecture

**Status: OBSOLETE.**

Unbounded production agent swarms, duplicate durable stores, universal anti-bot bypass, autonomous protected-policy rewriting and competing production deployment owners remain explicitly rejected.

## Critical integration gaps confirmed by current source inspection

1. The public research worker currently provides source-URL ingestion and run persistence; its response explicitly records `general_web_discovery=false` and `evidence_synthesis=false`.
2. The Foundation evidence graph schema is present, but the public ingestion path does not yet execute the full evidence-span/claim/verification/synthesis chain.
3. Operations chatbot model calls use the canonical durable `MODEL_CALLS` governance path. The separate multi-agent research LLM adapter is not yet unified behind that same provider runtime.
4. Deterministic product identity gating is already wired into the generic Operations extraction mapping path and has dedicated rejection tests; this requirement should not be treated as missing.
5. The artifact manifest currently contains core hash/provenance fields but not the complete richer lineage contract described in the broader plan.
6. Evaluation/promotion primitives exist; production-shaped research-to-evaluation-to-adjudication execution remains evidence-gated.

## Evidence boundary

Repository inspection is L1/L2. A successful current GitHub Actions run is L3. Approved runtime/production execution is L4. No source-only result in this document is to be interpreted as production certification.

## Synchronization rule

This reconciliation must be refreshed whenever either repository `main`, the approved production Operations revision, the pinned nightly research revision, canonical ownership, or a material acceptance gate changes. The `FAMILY_SYNC_STATE.json` file records the SHA observations for the audit; the live branch tips remain authoritative.
