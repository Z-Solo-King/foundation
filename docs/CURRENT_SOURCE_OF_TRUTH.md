# Current Source of Truth — 2026-09-23 Runtime Reconciliation

**Status:** CURRENT
**Owner:** Foundation family boundary
**Audit date:** 2026-09-23

## Current repository revisions

- Foundation `main`: `121ff5017c6b11ebc103dbbd26bdffe639fcc8cb`
- Operations `main`: `b47aa056f50d27df9b5f552495a6cd862ae8a697`
- Public Worker deployed provenance: `c465ed8cff860cf0f1a1d6de6655aaf9594f02d2`
- Private Worker production provenance: `bfcfaf5941824559cc253ecb2fd7d517cb1f1d7f`
- Canonical nightly research Operations pin: `3a7e350ddd5648caf93f58651323425186544f66`

Repository heads and deployed immutable runtime pins are intentionally separate.

## Current queue

11 open issues:
- Foundation: #58, #157
- Operations: #145, #197, #340, #352, #385, #597, #603, #699, #711

No open implementation/documentation PRs remain.

## Current CI / evidence

- Nightly research #861: BLOCKED before provider execution; required research endpoint/API key/model are absent. Run #862 is the subsequent scheduled run.
- Nightly contract #2302: PASS; contract-only evidence.
- Extractor benchmark #330: FAIL using stale Operations #830 (`246e563...`). The benchmark workflow has now been corrected to the canonical production pin `bfcfaf5941824559cc253ecb2fd7d517cb1f1d7f`; run #333 is queued.
- Coverage matrix #299: one deterministic idempotency fixture failure. The fixture case-matching defect has been corrected in Operations #833 and merged. The corrected coverage workflow receipts now separate test outcomes from live-probe outcomes. Run #302 is queued.
- Current live Worker probe on deployed Foundation `c465ed8cff860cf0f1a1d6de6655aaf9594f02d2`: PASS.
- Full production/runtime acceptance remains separate from repository CI.

## Evidence boundary

`L0 hypothesis -> L1 source -> L2 repository -> L3 GitHub Actions/control-plane -> L4 approved runtime/production`

Never upgrade source/test/contract evidence into L4 certification.

## Synchronization

Refresh live `main` heads and Cloudflare deployment receipts before new production claims. Runtime receipts outrank historical checkpoints.

---