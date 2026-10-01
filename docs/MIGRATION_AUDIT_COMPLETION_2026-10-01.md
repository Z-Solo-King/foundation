# Migration Audit Completion Checkpoint — 2026-10-01

## Scope
Non-feed migration work across Foundation, Operations, GitHub Actions, and Cloudflare. Feed recovery work is excluded.

## Repository state
- Foundation main: `966da57d7ab54c1f39692b82e5fe2df27a7752b4`
- Operations main: `7f28470ea512715dc4f65eb0832cdfab831dfe73`
- Canonical production Operations pin: `da86e92d4e0fdb68912efb54ef95c69281a7d613`
- Migration tooling pin: `f9f8ce0eb88b92a5d4e2e3ea5f2d397eebac5791`; the migration-review implementation is unchanged at the current Operations head.

## Migration implementation status
Repository-side migration architecture is complete for the current wave:
- Foundation owns hosted GitHub Actions and production deployment.
- Operations has no competing GitHub Actions authority.
- TypeScript is used for edge/application contract surfaces.
- Python remains canonical for semantic, policy, provenance, persistence, replay, resource and correctness authority.
- Rust/Go/other languages remain capability-specific candidates unless their promotion envelopes are satisfied.
- Migration evidence validators, registry integrity, evolution scoring, toolchain portability and mapper evidence contracts are implemented.
- Operations #597 is closed as completed after candidate-specific mapper evidence was recorded.
- Operations #603 remains open only for a future candidate-specific authority-promotion envelope; no current language/model/tooling authority transfer is claimed.

## Workflow finding
The previously observed nightly research runner failure due to missing `httpx` is already fixed in the current Foundation workflow: `.github/workflows/nightly-multi-agent-research-v3.yml` installs `httpx>=0.27,<1` immediately after Python setup and before `scripts/research_worker_proxy.py`.

Therefore the next acceptance action is a fresh execution, not another dependency patch.

## Cloudflare reconciliation
During this audit the live Worker provenance was:
- `heroic` / `heroic-core`: Foundation revision `cda35802516152b0106c21583cc93503fcd554b9`
- `operations` / `operations-edge`: Operations revision `90fa37df10d63824acd3fe20b64cc91043af9627`

The repository has since promoted `da86e92d4e0fdb68912efb54ef95c69281a7d613` as the canonical production pin. The live Operations Worker therefore requires a canonical production-release redeployment before that promotion is runtime-certified.

The deployment workflow is intentionally `workflow_dispatch`-driven and remains the sole production deployment authority. No second deployment path is introduced here.

## Exact remaining acceptance sequence
1. Dispatch the canonical Foundation production release.
2. Confirm the release consumes `da86e92d4e0fdb68912efb54ef95c69281a7d613`.
3. Verify `operations` and `operations-edge` provenance annotations, protected zero-cost bindings and Foundation/Operations service bindings.
4. Run the same-head production chatbot smoke.
5. Run the live nightly research CrossFire gate; it must produce valid lane artifacts and truthful-result acceptance.
6. Run the migration review against the exact released pair.
7. Only after candidate-specific receipts satisfy parity/security/policy/provenance/cancellation/resource/shadow/canary/rollback gates should any candidate authority change be considered.

## Safety boundary
No feed/WooCommerce code is changed. No secret is added. No mutable Operations reference is promoted. No language/model/tooling authority is inferred from benchmarks, compilation, static scans or documentation.
