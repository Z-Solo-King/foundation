# Migration Live Reconciliation — 2026-10-04

This is the current non-feed migration checkpoint for the Foundation/Operations family.

## Live GitHub heads

- Foundation main at reconciliation start: `319ec99d09796ce9688468b14366acdaf7bccbe1`
- Operations main at reconciliation start: `54d36e5e7f7dac89b3363d6b606c7a782a4f2624`
- Operations #1588 merged the machine-readable migration evidence refresh before this checkpoint.

## Migration implementation state

The hybrid migration implementation is present in the repositories:

- Foundation owns the public-safe edge, hosted CI/release path, and migration verification.
- Operations owns the private runtime, policy, evidence, resource, provenance, replay/idempotency and private extraction/mapper surfaces.
- TypeScript is used at the public edge and exists as shadow/candidate boundaries for search/browser/observation work.
- Rust candidates exist for deterministic parsing/normalization leaves.
- Go remains a bounded concurrency/tooling candidate.
- Python remains the semantic/control-plane reference authority.

## Authority-promotion state

Language migration implementation is not equivalent to authority migration.

No candidate is promoted solely from static scans, benchmark scores, AI output, compilation, or documentation. Authority promotion still requires the repository-defined parity, security/policy/provenance, resource/performance, shadow, canary, rollback, and downstream-consumer gates.

The current Operations polyglot registry contains 53 candidates. The evidence registry does not contain a valid authority-promotion state for a candidate at this checkpoint.

## Runtime reconciliation

Current Cloudflare observations recorded separately from GitHub source state:

- public `heroic`: 100% latest observed version is tied to Foundation revision `45c59fef2f34f3d945e59ef1c8a02debdb890bad`
- `heroic-core`: 100% latest observed version is tied to Foundation revision `45c59fef2f34f3d945e59ef1c8a02debdb890bad`
- `operations`: 100% latest observed production version carries `RELEASE_OPERATIONS_REF=11f592116d9ef57b6189bf8bf0ff0e95ec3d410f`
- `operations-edge`: 100% latest observed version is annotated with Operations revision `da86e92d4e0fdb68912efb54ef95c69281a7d613`

These are deployment observations, not promotion instructions. Moving GitHub `main` is not treated as production authority.

## Fresh verification

A trusted push to Foundation `main` is used to execute the six-lane Migration Factory against the current immutable Operations head. The factory must report all six lanes for both repositories, cover every tracked Python file, and aggregate exactly 12 reports before the migration checkpoint is considered structurally complete.

The resulting factory artifacts are the authoritative coverage evidence for this checkpoint. Runtime authority remains independently evidence-gated.
