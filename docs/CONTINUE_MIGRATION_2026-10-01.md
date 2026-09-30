# Migration Continuation Runbook — 2026-10-01

## Purpose

This document is the handoff point for continuing the cross-repository migration/audit work after the current chat reaches its context limit.

The project is the GitHub + Cloudflare Heroic AI stack:
- public repository: `Z-Solo-King/foundation`
- private repository: `Z-Solo-King/operations`

Feed extraction work is explicitly excluded from this migration lane. Do not modify or merge feed-hunt work while continuing the non-feed migration.

## Live state verified for this handoff

Checked from live GitHub and Cloudflare state immediately before writing this document.

### GitHub

Foundation main:
`94a5b5dfeb17f18239ac5defba72021aeb542ce2`

Operations main:
`7fe60d4630b30f38bfe30eff6666c9588cf2059f`

Canonical production Operations pin:
`ca3864a954569f6f8ce9a94793c53a0ef9ff03ec`

Current open acceptance issues:
- Foundation #58 — exhaustive coverage/meta tracker
- Foundation #157 — genuine 24-program live research acceptance
- Foundation #1247 — WooCommerce feed recovery (excluded)
- Foundation #1249 — Custom/API feed recovery (excluded)
- Operations #597 — mapper capability migration evidence
- Operations #603 — AI/model/tooling portability evidence

Current open feed/mixed PRs that are intentionally not part of this lane:
- Foundation feed PRs: #1652, #1653, #1656, #1657, #1658, #1660
- Operations #1361 — feed-only
- Operations #1400 — mixed extractor/feed work; do not use it as the non-feed migration merge vehicle

### Cloudflare

Current live production pair:
- `heroic` -> Foundation `0c1593ce...` -> TypeScript edge
- `heroic-core` -> Foundation `0c1593ce...` -> Python core
- `operations` -> Operations production pin `ca3864a9...`
- `operations-edge` -> Operations production pin `ca3864a9...`

The public Worker rollout is therefore already on the TypeScript edge migration in live Cloudflare.

Backblaze B2 remains owned by the Foundation Python core artifact/backup path. B2 is not an identity, policy, routing, resource or promotion authority.

## Canonical architecture after this migration wave

Internet / Pages
-> `heroic` TypeScript public HTTP/SSE edge
-> `heroic-core` Python semantic/application core
-> `operations-edge` TypeScript/JS delegation boundary
-> `operations` Python private control plane

Operations owns:
- provider/task-fabric runtime
- chatbot semantics and routing authority
- resource/quota/lease governance
- policy/evidence/provenance/idempotency/replay authority
- private acquisition/extraction orchestration
- research orchestration

Foundation owns:
- public-safe contracts
- public HTTP/SSE boundary
- deterministic mapper/core/data-quality primitives
- evidence publication/public admission
- canonical hosted GitHub Actions release authority

Rust/Go/other languages remain capability candidates. Do not transfer authority because of a language score, benchmark, compilation success or AI recommendation.

## Migration rule

Use:

language score -> experiment selection
measurement -> candidate value
differential/security/policy/provenance -> authority eligibility
shadow -> canary -> rollback -> promotion

Python remains the reference/authority until a candidate satisfies its exact promotion envelope.

TypeScript is the preferred application/edge/browser contract language.
Rust is for measured deterministic CPU/memory-sensitive kernels.
Go is for measured high-concurrency/network utilities.
C++/Java/etc. remain qualification candidates only when a concrete workload demonstrates a unique advantage.

## Completed in the last migration wave

### Foundation

- Public Heroic edge migrated from JavaScript to TypeScript.
- Production release generator updated to generate `edge.ts`.
- Public edge B2 secret exposure cleanup is part of the release boundary.
- CrossFire/research proxy lifecycle was consolidated into one execution step.
- Strict all-file/file-symbol language coverage audit was added.
- Extractor governance CI now installs the Workers runtime dependencies and materializes the pinned Foundation public core.
- Production D1 migration detection was corrected to avoid unnecessary free-tier row-read consumption.
- Mainline release/deployment was verified against live Cloudflare state.

### Operations

- Async research-provider transport migrated from thread-backed urllib to bounded async `httpx`.
- Cloudflare Browser Run candidate adapter added and corrected to the current `BrowserWorker` SDK type.
- Browser Run remains candidate-only and unpromoted.
- Strict coverage scanner expanded to classify Swift and Gleam experimental source files.
- Extractor-surface audit now matches test evidence by path as well as content.
- Provider contract fixtures synchronized with the canonical zero-cost provider rules.
- Migration evidence ledger synchronized with live state.

## Current acceptance status

### Foundation #157 — 24-program live research

This is NOT closed.

Closure requires a fresh production-release-dispatched run that:
1. proves exact Foundation + Operations revisions deployed;
2. passes Worker-backed model preflight;
3. completes all 24 programs;
4. validates all 3 lane artifacts;
5. passes diagnosis and truthful-result gates;
6. retains complete artifacts and provenance.

A historical run with 24 program IDs is not enough. Coverage without valid lane execution is insufficient.

### Operations #597 — mapper migration

Repository-side decomposition and governance are implemented.

Still required for each actual candidate promotion:
- deterministic differential/parity
- normalized error taxonomy
- security
- policy
- provenance
- cancellation/timeout parity
- resource/performance measurement
- serialization/conversion cost
- shadow
- canary
- rollback

Do not retire the Python/reference path before those gates pass.

### Operations #603 — AI/model/tooling portability

Repository-side portability framework is implemented.

Still required for each promotion:
- orthogonal parity corpus (32 cases x >=3 repeats where required)
- functional parity
- security/policy/provenance
- cancellation/timeout
- serialization/conversion/resource cost
- canonical correctness authority
- shadow
- canary
- rollback

A score or benchmark is not authority evidence.

## Browser Run status

Live Cloudflare Browser Run `/content` execution has been verified separately.

The repository Browser Run adapter now uses the SDK `BrowserWorker` binding shape and retains:
- HTTPS/read-only acquisition policy
- explicit host allowlist
- max 50 allowed domains for Cloudflare guardrails
- existing timeout/page/response bounds
- candidate-only status

Do not add a production `BROWSER` binding or promote this path without a full resource + policy + provenance + differential + shadow + canary + rollback envelope.

## Provider status

Current governed provider configuration is strict-zero-cost.

SiliconFlow remains configured according to the current project state.
Cerebras remains intentionally unactivated for the free path because a card is required and no usable credential is configured.
Mistral remains conditional/excluded.

OpenAI-compatible transport does not imply semantic equivalence. Structured output, streaming, context, errors and tool behavior still require provider-specific differential validation.

## Audit strategy to continue

Run the audits as independent lenses, not one giant rewrite.

Recommended lanes:
1. repository/ownership/policy lens
2. TypeScript edge/application lens
3. Rust deterministic-kernel lens
4. Go concurrency/network lens
5. Cloudflare runtime/deployment lens
6. evidence/provenance/security lens

Every lane still covers both repositories. Shared writes must remain serialized and owned by the canonical repository/authority.

Use map-first retrieval:
AI_PROJECT_MAP -> REPOSITORY_MAP -> canonical feature/function -> policy/tests/workflows -> live runtime receipt.

## Important safety / authority rules

- Do not bypass GitHub permissions, Cloudflare challenges, CAPTCHAs or authentication.
- Do not infer credentials from names.
- Do not put secret values into AI project maps or receipts.
- Do not create a second deployment authority.
- Do not allow AI, benchmark or scoring systems to become policy/evidence authority.
- Do not treat historical receipts as current production proof.
- Do not implicitly promote a moving Operations main branch; the production pin is immutable.
- Do not merge feed work into the non-feed migration lane.

## First actions in the next chat

1. Re-read this file.
2. Refresh live GitHub Foundation/Operations heads.
3. Refresh the Foundation Operations pin manifest.
4. Refresh live Cloudflare deployments for the four canonical Workers.
5. Check the current status of #157, #597, #603.
6. Check open PRs and classify each as non-feed / feed / mixed.
7. Only then mutate code.
8. For candidate migrations, generate fresh evidence against the exact current authority/revision pair.
9. For production changes, let the canonical Foundation release workflow deploy; do not manually deploy around it.
10. After every accepted change, update AI_PROJECT_MAP / migration evidence and record the exact revision and receipt.

## Continuation invariant

The objective is not “rewrite everything into the fastest language”.

The objective is:
- fastest stable architecture for the actual workload
- minimum resource/token overhead
- one authority per responsibility
- deterministic behavior
- strict $0 policy
- complete provenance
- recoverable migrations
- measurable learning/evolution

Any proposed migration that makes the system faster but duplicates authority, weakens evidence, violates cost policy, increases serialization overhead, or reduces rollback safety is a regression even if its benchmark is faster.
