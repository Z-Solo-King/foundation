# 2026-09-23 CURRENT AUTHORITY OVERRIDE

The following values are authoritative for the current handoff. Older dated checkpoints in this document are historical provenance only.

- Foundation main: `978a2b0208cafeae8e740a07374ed78865a19e0b`
- Operations main: `2d09b7306b1d383d3b715db789d199010c7bcb19`
- Audited Foundation runtime implementation: `b1767a40c7b5f0b49429753365fa60dffe50119b`
- Audited Operations production implementation: `4967fb56c5fcd0f0f393d06b327476c886cf3e05`
- Audited Operations nightly research pin: `3a7e350ddd5648caf93f58651323425186544f66`
- Foundation production deployment owner: GitHub Actions / `scripts/production_release.sh`
- Operations remains private runtime/control-plane authority and must not own GitHub Actions.
- Remaining open issues are acceptance gates; do not infer live closure from source inspection or deterministic CI.

---

## 2026-09-22 FINAL LIVE REF RECONCILIATION

**Live branch heads queried from GitHub:**
- Foundation `main`: `f9490f36d7ffd877157f26d674b3bfc27388f67e`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`

**Verified runtime implementation pins:**
- Foundation: `e5b26061861e570396b73993a3c8733496cb1956`
- Operations: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`

The live heads may contain documentation and migration-candidate commits after the verified runtime pins. Acceptance workflows intentionally remain pinned to the verified immutable revisions until promotion evidence passes.

## 2026-09-22 LIVE GITHUB REF RECONCILIATION

**Latest live branch heads queried from GitHub:**
- Foundation `main`: `86a7d02b86a78102bf412cdce050c1f9e6c95bd5`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`

**Verified runtime implementation pins:**
- Foundation: `e5b26061861e570396b73993a3c8733496cb1956`
- Operations: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`

**Important:** Operations `main` now contains merged migration-candidate/test fixes after the verified runtime pin. Those candidate revisions are not production/runtime certification and must not silently replace the immutable runtime pin in acceptance workflows. The coverage/runtime guard must fail closed when non-documentation drift exists after the approved pin.

## 2026-09-22 LIVE GITHUB REF RECONCILIATION

**Live branch heads observed immediately before this synchronization:**
- Foundation `main`: `baad1daf07ea7d0307077631c4afb3a27fa31e78`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`

**Last verified implementation revisions:**
- Foundation: `e5b26061861e570396b73993a3c8733496cb1956`
- Operations: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`

Documentation-only handoff commits may advance `main` without changing the verified runtime implementation revision. Always refresh live refs before mutation and keep live branch heads separate from runtime-certification pins.

## 2026-09-21 FINAL HANDOFF

Current heads:
- Foundation 985fd526913bdf48fffc73cfc7e834d38dd449de
- Operations 2da42873fa2ff7ae05df00973a7ba584cdd1c6a9

Completed in this work:
- rounds 5-6 scan findings reconciled;
- lifecycle/materialization fixes merged in Foundation #921;
- scan-method and maintenance documentation synchronized in Foundation #922 and Operations #670;
- Operations #650/#655/#656/#657 plus provider-configuration centralization #661 and deep-immutability residue #665 merged;
- issue labels and cross-issue relationships normalized;
- remaining queue reduced to explicit runtime/evidence acceptance gates.

The adaptive scan protocol is canonical in docs/CROSS_LANGUAGE_ADAPTIVE_SCAN_METHOD_2026-09-21.md and referenced by AGENTS.md.

---

## 2026-09-21 LIVE HANDOFF

Current GitHub heads:
- Foundation main: e50a84ee239937967f9c23412e94521d347e3466
- Operations main: 44c4dc2189efa9b5a6f0e5648f5c892c55b45746

Current implementation PR: Foundation #921 fixes #909/#910 with closed ResearchLifecycle semantics and bounded worker materialization.

Recently merged scan-derived Operations corrections: #650 Go fanout lifecycle/cancellation/deterministic receipt pilot; #655 ResourceLedgerSnapshot deep immutability; #656 explicit malformed provider-runtime diagnostics; #657 aggregate provider-stream output budget; #661 centralized provider configuration parsing; #665 nested-mutation hardening for frozen records.

Remaining queue is intentionally acceptance-driven; runtime-gated issues remain open until their live evidence exists.

Use AGENTS.md and docs/CROSS_LANGUAGE_ADAPTIVE_SCAN_METHOD_2026-09-21.md for all subsequent scan waves.

---

## 2026-09-20 VERIFIED HANDOFF

Start from Foundation `d4f8be98447d2b6c6d05d1b213941e029f8649a6` and Operations `dd30834aec8f1263d9b35142b1bd16b4ba95f1ca`.

Canonical production proof:
- Foundation production run `35519167159` / run number `321` = SUCCESS.
- Operations Cloudflare provenance = `github:dd30834aec8f1263d9b35142b1bd16b4ba95f1ca`.
- Operations active version observed by the release = `0dae35f1-854b-49e4-b278-f3a17af3aa00`.
- Runtime acceptance passed for chat, idempotency, SSE lifecycle, permitted-source research/readback, D1/B2, memory store/query/delete/owner boundary, replay guard, learning feedback, terminalization CAS, durable resource reservation/reconciliation, maintenance reconciliation and provider-stream contract.
- Cross-version memory/replay remains deferred.
- Live provider completion remains intentionally unavailable because no permitted provider is configured; deterministic fallback is explicit.

Migration:
- Foundation #862 is merged: exact pinned Foundation Git object/tree is asserted before public-core sync.
- Foundation #863 is the active follow-up correcting the pin discovery output contract; after it merges, run the fresh migration/extractor matrices before making candidate migration decisions.
- Do not treat earlier blob-mismatch failures as candidate failures; they were harness failures.
- Keep the 3 migration + 1 acceptance/blocker adaptive lane model.
## 2026-09-20 PRODUCTION PROMOTION OVERRIDE

- Foundation main before this promotion: 62ff421534034d70a110f1dba32f71975c7e5a2d.
- Operations main: 277ccb9ee33221038c7ca5647f19e27a00d84ea3.
- Production pin target: dd30834aec8f1263d9b35142b1bd16b4ba95f1ca (Operations #610, exact proven packaging fix).
- This is a deliberately immutable production target; it does not promote the newest Operations benchmark/docs commits.
- Fresh production certification is required after merge; historical production receipts do not certify this target.

## 2026-09-20 LIVE MIGRATION RECONCILIATION — CURRENT OVERRIDE

Refresh live GitHub refs before every mutation.

### Current repository heads
- Foundation main: 12cf25f6a5688522f945e48efed915a5d5902703.
- Operations main: b5982fd9c3203d360584f955b8adfcf85cfd1315.

### Active migration work
- Foundation #835 (TypeScript frontend controls) is merged.
- Foundation #836 is the documentation reconciliation PR.
- Operations #606, #607, #608, #609, #610 and #611 are merged.
- Operations #610 fixed the production Worker packaging defect where generated foundation_core was excluded from setuptools package discovery.
- Operations #603 remains the canonical AI-model/tooling portability tracker.
- Current main is not production-certified until a canonical production release proves the current revisions.

### Architecture invariant
Python remains protected policy/governance/persistence/provenance/replay/rollback authority. TypeScript/Rust/Go migration work remains evidence-gated. Operations remains free of GitHub Actions; Foundation remains the sole CI/CD/deployment owner.

# AI Agent Handoff — Research Intelligence Engine

## 2026-09-19 CURRENT HANDOFF — AUTHORITATIVE

This section is the continuity anchor for the next maintenance chat. Current GitHub state and fresh production evidence override all older sections in this file.

### Exact repository state

- Foundation `main`: `386dcad577cacf729ee49830548597ff5504de14`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`
- Foundation production Operations pin target: `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`
- Foundation nightly research pin remains: `f6600c068de6e17af1e0e99c1f3ba4b0f06f31b5`
- Foundation PRs #739, #740, #741, #742, #808, #810, #811, #812, #814, #815, #816, #817 and #818 are merged.
- Operations PRs #535, #536, #537, #575, #576, #577, #578, #579, #581, #583, #584, #585, #586 and #587 are merged.
- Foundation #27 is closed.
- Operations contains no GitHub Actions workflow authority.

### Latest canonical production proof

Run `35456292033` (#232), Foundation `6a91fbd17143083882e9ac7ebfa52f0b06a344b2`, last verified against Operations `f6600c068de6e17af1e0e99c1f3ba4b0f06f31b5`. The next production certification target is Operations `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`.

The release verified:

- public Worker deployment/readiness;
- private Operations Worker deployment and Cloudflare provenance `github:f6600c068de6e17af1e0e99c1f3ba4b0f06f31b5`;
- authenticated chat and idempotent replay;
- authenticated SSE lifecycle;
- permitted-source research ingestion/readback;
- D1/B2 lifecycle;
- memory store/query/delete and owner boundary;
- durable task-envelope replay protection;
- candidate learning and rating-feedback candidate flow;
- durable terminalization CAS;
- durable resource reserve/consume and reconciliation;
- maintenance scheduler reconciliation;
- provider-stream contract.

The production release emitted and uploaded `cross-repository-audit-receipt`. The release itself completed successfully.

### Repository-side fixes completed in this sequence

- Operations #535: family audit excludes approved compatibility facades.
- Operations #536: nested `foundation_core.*` compatibility facades are recognized correctly.
- Operations #537: terminalization CAS requires the current durable attempt identity and prevents stale/reclaimed attempts from masquerading as valid duplicate terminalization.
- Foundation #741: pins the corrected nested-facade audit revision.
- Foundation #742: pins the corrected terminalization runtime revision.
- Production run `35456292033` exercised the merged Operations terminalization correction successfully.

### Remaining queue

Foundation:
- #157 — real 24-program nightly execution/artifact evidence remains missing because the current push-triggered nightly run still fails before job creation.
- #263 — repository-side bridge v3 is fixed and merged; one real workflow-dispatch receipt with exact target SHA and actual job creation remains missing.
- #452 — repository SSE lifecycle is green; current architecture uses non-streaming provider calls, so remaining proof is real client cancellation/disconnect propagation; a true provider-error-after-partial-output path would require a separate incremental-provider-streaming feature.
- #58 — meta tracker remains open until the dependent gates above are genuinely satisfied.

Operations:
- #119 — live memory persistence across restart plus endpoint authorization/deletion.
- #120 — live durable feedback retention plus evaluation/benchmark integration.
- #132 — live replay-guard persistence/rejection across an actual restart/instance boundary.
- #145 — external approved scheduler activation.
- #155 — current cross-repository audit receipt is green in production; supported bridge-dispatch evidence is still required.
- #197 — broader approved runtime conversational acceptance.
- #340 — deeper provider streaming interruption/cancellation/error evidence.
- #352 — representative API/feed/HTML/browser extractor/mapper replay matrix with failures/retries/restarts/idempotency/provenance.
- #385 — broader concurrent completion/failure/cancellation, crash-after-side-effect, late-output, and restart/recovery acceptance. Unexpected chat exceptions are durable `failed` terminal receipts via #579, and unresolved external intents fail closed via #585; remaining broader recovery/runtime gates are still open.

### Do not regress the architecture

- Foundation remains the only GitHub Actions and canonical production deployment owner.
- Operations remains private and contains no GitHub Actions workflows.
- Do not add Cloudflare Workers Builds or Deploy Hooks.
- Do not create a second memory store, resource ledger, replay authority, lifecycle authority, evaluator, publication authority, or deployment path.
- Do not close runtime/external issues from source inspection or unit tests alone.

### Queue continuation

Use `FIX_NOW | INTEGRATE | VERIFY_REPO | RUNTIME_GATE | EXTERNAL_BLOCKED | DUPLICATE | SUPERSEDED | ROADMAP`.

For every mutation, preserve:
`issue -> canonical owner -> revision -> acceptance rung -> checks -> PR -> missing evidence`.

When a queue item is RUNTIME_GATE or EXTERNAL_BLOCKED, record the exact missing evidence on the issue and move to the next independent lane. The current repository migration sequence is TS edge/search/browser -> Rust measured kernels -> optional Go sidecars, while Python remains the protected rollback/policy authority.
