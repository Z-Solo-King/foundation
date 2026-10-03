# Migration reconciliation — 2026-10-03

## Scope

Non-feed coding-language migration work across Foundation, Operations, GitHub Actions, and Cloudflare. Feed/WooCommerce work is excluded.

## Current heads

- Foundation main: `8d3a8580b2f758acd0f155fdbd1cd5e5d691b5a7`
- Operations main: `960544af58d02c118af93d88abf0c75a279e4b42`
- Foundation remains the sole hosted GitHub Actions/deployment authority.
- Operations has no competing Actions authority.

## Migration disposition

### TypeScript observation-contract

The immutable evidence packet from 2026-10-01 is complete as a private qualification packet:

- 32/32 exact differential cases;
- normalized error taxonomy parity;
- security/policy/provenance parity;
- cancellation/timeout parity;
- 3 repeats × 500 measured iterations;
- p50/p95/p99, CPU, RSS, allocation and serialization measurements;
- private read-only shadow;
- private read-only canary rehearsal;
- rollback/reference restoration.

The packet explicitly has `authority_promotion_claim=false`. Its reference revision is Operations `90fa37df...`, while current Operations main is `960544af...`. Therefore the packet remains valid historical evidence but is not current-head production authority evidence.

**Disposition:** evidence-complete shadow; Python remains the canonical production/reference authority until a fresh current-head acceptance packet and production deployment verification exist.

### Rust

Rust candidates remain component-specific. URL identity has an expanded 95-case security corpus; parser/normalization candidates remain shadow or benchmark lanes. No Rust production authority transfer is claimed.

### Go

Go HTTP fan-out remains a benchmark/tooling candidate. No independent production service boundary is justified by the current evidence.

### Elixir

The previously registry-only Elixir bounded-fanout admission was missing its implementation. This reconciliation adds a dependency-free 32-case candidate under `operations/polyglot/elixir-bounded-fanout` and a Foundation-owned CI lane using Elixir 1.20 / OTP 28.

The Elixir candidate is deliberately limited to bounded, deterministic concurrency. It has no policy, quota, persistence, provenance, network, or deployment authority.

**Disposition:** candidate implemented; CI benchmark/differential evidence still required before any promotion consideration.

## Cloudflare reconciliation

Live Worker configuration remains independently authoritative. Current live annotations are not assumed to equal current GitHub main:

- `heroic` / `heroic-core` currently report Foundation revision `45c59fef...`.
- `operations` is currently annotated by the controlled `live-sanitize-operations-2026-10-03` upload.
- `operations-edge` currently reports Operations commit `da86e92d...`.

This means repository migration completion must not be conflated with production deployment completion. The production deployment workflow remains the only permitted path for promotion; no direct Cloudflare mutation is used to bypass it.

## Remaining blockers

1. Fresh current-head TypeScript observation-contract acceptance against Operations `960544af...`.
2. Production deployment verification for the promoted candidate, if and when the authority-transfer gates pass.
3. Elixir CI execution and benchmark receipt.
4. Candidate-specific shadow/canary/rollback evidence for any future authority transfer.
5. Operations #603 remains open for the remaining portability/promotion envelope. Foundation #58 remains the aggregate tracker.

## External research cross-check

Current Cloudflare documentation confirms JavaScript/TypeScript, Python and Rust are first-class Worker languages and that Wasm can extend language options. Cloudflare recommends generated Worker types for TypeScript and documents Rust through `workers-rs`. Current Elixir documentation lists v1.20.4 as stable and documents `Task.async_stream` for bounded concurrent traversal. These facts support the current workload-specific candidate model; they do not override project-specific evidence gates.

## Truthful completion rule

A language migration is not marked production-complete merely because code compiles, tests pass, a benchmark improves, or a registry entry exists. Production authority requires exact contract parity plus security/policy/provenance/cancellation/resource evidence, shadow, canary, rollback and deployment verification.
