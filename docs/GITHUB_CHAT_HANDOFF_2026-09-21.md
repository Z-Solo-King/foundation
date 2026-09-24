# 2026-09-24 LIVE GITHUB/CHAT HANDOFF — CYCLE 7

- Foundation main: `2710b7559c9c7a0dcd2c84fe6ed77b8dbc684706`
- Operations main: `1fd629cae593959249107ddb8c7af3f55292e9df`
- Production Operations pin: `fda24660843cacfe28de661cf170789af542d28f`
- Production Foundation revision: `725e1b9cdaa637f07d4264673cddfc8ab806b3c6`
- Open issues: Foundation #58/#157; Operations #145/#340/#385/#597/#603/#699.
- Open PRs: Foundation #1137 (docs/session checkpoint only); Operations: none.
- Latest production release: `36030977718` PASS.
- Latest nightly research: `36030996071` FAIL at public Worker 403 / local 502 `upstream_worker_rejected`.
- Cloudflare basic control-plane reads: account membership/Workers/D1 all returned HTTP 200; exact deployment-history/version freshness is not newly certified by this checkpoint.
- Start every new chat by refreshing live heads and issue/PR state. Do not use historical handoff SHAs as current.

---

## 2026-09-24 CURRENT AUTHORITY RECONCILIATION

- Foundation `main` observed before this doc-only sync: `825d301d10d201cd9b74dd018973769aeb03f381`
- Operations `main` observed before this doc-only sync: `994793431981b87cd37f2ee1eabf8a2b11914c34`
- Production Operations pin: `1a12b98981f52de207fa8626cf2e1f5ad06659be`
- Nightly research/migration pin: `41db817dee6aa7d369ea9a07dd072b58ece1695a`
- Open issues: Foundation `#58/#157`; Operations `#145/#340/#385/#597/#603/#699`
- Open PRs: 0 at audit start
- Production release `#501`: success; current Cloudflare public/private provenance matches the production pins.
- Nightly `#893`: provider-gated before provider execution because the three research-provider secrets are absent.
- Extractor `#362`: strict evidence-quality pass; 40 receipts, 4 ok / 32 empty / 4 blocked.
- Deep scan `#365`: pass; 8 active issues + historical `#197`, four lanes.
- Smoke `#72`: contract-red on `infrastructure_verify` versus the current `infrastructure_verify_public_test` contract.
- Centralized Operations validation `#24`: broad test-suite contract failures.
- This synchronization changes documentation only; do not treat its resulting commit SHA as a new runtime implementation revision.

Read `docs/CURRENT_SOURCE_OF_TRUTH.md` and `docs/LIVE_GITHUB_CLOUDFLARE_SYNC_AUDIT_2026-09-24.md` for the current snapshot.

---

## 2026-09-22 CURRENT RECONCILIATION

**Live-head rule:** query the current GitHub `main` refs at chat startup. Documentation-only commits may advance `main` and must not be mistaken for a new runtime implementation revision.

- Last verified Foundation implementation revision: `e5b26061861e570396b73993a3c8733496cb1956`
- Last verified Operations implementation revision: `7cf73e6a15b1e1d090f023915f62e5a2bd066b8e`
- Canonical nightly research workflow: `.github/workflows/nightly-multi-agent-research-v2.yml`
- Nightly `OPERATIONS_RESEARCH_REF`: `7cf73e6a15b1e1d090f023915f62e5a2bd066b8e`
- Final implementation repair waves are merged through Foundation #960 and Operations #753.
- Foundation #157 remains the canonical 24-program nightly acceptance gate.
- Remaining open issues are runtime/provider/Cloudflare/migration evidence gates; do not infer closure from source inspection, unit tests, or dry-runs.
- GitHub Actions remains the sole CI/CD/production deployment authority; Operations must remain free of GitHub Actions, and Workers Builds/Deploy Hooks must not be re-enabled.

### Nightly research continuity
- 3 lanes × 8 programs = 24 programs.
- Provider configuration required: `RESEARCH_LLM_ENDPOINT`, `RESEARCH_LLM_API_KEY`, `RESEARCH_LLM_MODEL`.
- Live closure requires real provider-backed execution, all expected program IDs, complete JSONL/status artifacts, exact Operations revision provenance, and the final validation gate.
- Do not post secrets in issues/comments.

## 2026-09-21 CURRENT RECONCILIATION

- Foundation `main`: `b2752d6a63aaf646743cc8173fa83b4271b02160`
- Operations `main`: `0fa576c10fee30221150110865b11c0132de4575`
- Canonical immutable Operations pin: `0fa576c10fee30221150110865b11c0132de4575`
- Foundation PRs #951, #952, #954, #955 and #956 are merged; Operations #745-#749 are merged.
- Foundation #953 is closed. The remaining open issue queue is Foundation #58/#157/#452 and Operations #119/#132/#145/#197/#340/#352/#385/#597/#603/#699/#711.
- Repository implementation waves are reconciled. Remaining issues are explicit runtime/control-plane/production evidence gates unless fresh CI reproduces a new defect.
- Do not infer Cloudflare/runtime certification from source inspection or GitHub-only tests.


> Foundation mirror. This handoff is intentionally mirrored so a future GitHub-only chat can start from either repository.

## Canonical repository state

- Foundation `main`: `0e5e3532e91ea40040b718a8dcbf7e3f66919d30`
- Operations `main`: `a03c90fde14ccf89535020f50a5e15e51123c1b3`
- This is the canonical GitHub-side handoff for the next AI/chat session.
- Cloudflare/live runtime verification remains separate from this GitHub-only context.

## Latest merged Operations work

- #707 / `3c4fad5f...`: endpoint-discovery security/parity hardening and frozen 32-case corpus.
- #708 / `acfd0e9c...`: polyglot registry, placement contract, documentation ownership cleanup and duplicate adapter retirement.
- #709 / `d3c680ce...`: acquisition IP allow-listing, streaming POST bounds, scoped task-envelope signing keys, provider-error preservation and production test-double removal.
- #710 / `4a471024...`: DNS revalidation immediately before public acquisition to close the hostname rebinding window.

## Current concrete implementation blocker

### #711 — DurableResourceLedger reservation orphan

Repository implementation is complete in the merged repair wave. #711 remains open only for runtime evidence: Python 3.14/full-suite evidence plus real/preview D1 `changes()` semantics and the concurrent over-limit probe. Do not close from static inspection alone.

## Remaining runtime/evidence gates

The older acceptance backlog remains intentionally open:
- #119 memory/provenance/version-boundary evidence;
- #132 task-envelope replay across real version boundary;
- #145 maintenance receipt;
- #197 live conversational execution/idempotency/policy denial;
- #340 provider streaming interruption/reconciliation;
- #352 representative extractor/mapper runtime replay;
- #385 cross-surface restart/recovery;
- #597 mapper migration evidence ladder;
- #603 portability/shadow/canary/rollback evidence.

These are evidence gates, not reasons to create duplicate implementations.

## Migration state

The repository-side polyglot migration work is complete at the implementation/evidence rung:
- Rust candidates: URL identity, text normalization, HTML/product-card, JSON-LD, Link-header pagination, robots/sitemap.
- TypeScript candidates: search/provider adapters, browser acquisition, public endpoint discovery, Next.js product-state, acquisition planner, edge-worker.
- Go: bounded HTTP fan-out benchmark/pilot.

Python remains the protected authority for policy, governance, persistence, replay/idempotency, provenance and rollback-sensitive semantics.

## Documentation/ownership

- `polyglot/REGISTRY.json` is the machine-readable candidate inventory.
- `docs/CODE_OWNERSHIP_AND_PLACEMENT.md` is the placement contract.
- `docs/CURRENT_SOURCE_OF_TRUTH.md` is stable state/ownership guidance, not a historical release log.
- Foundation owns public-safe common standards; Operations keeps only private addenda.

## New-chat procedure

Read this file first, then:
1. inspect both repos' current `main` SHAs;
2. inspect open PRs;
3. inspect #711 and its proposed fix before touching the acceptance backlog;
4. inspect the Foundation hardening PR/branch;
5. keep repository implementation work separate from live Cloudflare/runtime acceptance.

## Latest active implementation queue discovered after the prior handoff

- **#712** — open PR implementing the #711 DurableResourceLedger orphan-reservation fix. Review and required tests first; #711 stays open until Python 3.14/full-suite and real/preview D1 `changes()` evidence are recorded.
- **#717** — task-envelope/replay guard correctness and fail-closed behavior.
- **#718** — Worker/chat auth-before-parse, body limits, exception leakage, requested_fields typing, provenance, routing and decomposition.
- **#719** — reconciliation poison-row isolation, post-reserve deadline release, resource-kind reservation mapping, and invariants.
- **#720** — protected-policy no-op enforcement and semantic policy digest.
- **#721** — SSE terminal-state vocabulary, including `NOT_ATTEMPTED` and unknown-state fail-closed handling.

These are newer concrete implementation findings and must be reviewed before treating the older runtime acceptance backlog as the only remaining work.
