# Current Source of Truth — Foundation (public-safe)

This document is a public continuity aid, not a private runtime/control-plane authority.

Checked: 2026-09-26.
Foundation main: `4999c93dc8b17a5a3926faf3415e725fd4ae7b0e`.
Active GitHub issue count across the family: 11.
Public Foundation issues: #58, #157, #1157, #1247, #1249, #1305, #1306.

## Public architecture

`ai-cio.pages.dev` is the canonical public front door.
Foundation owns public-safe contracts/core, the public edge/API, GitHub Actions, and deployment orchestration.
The protected Operations side owns private runtime policy, provider control, resource governance, memory, recovery, and protected tooling.
The retired extractor-mapper repository is historical material, not a runtime owner.

## Runtime and evidence boundary

Protected runtime revisions, resource identifiers, deployment internals, private issue state, and private provider configuration are intentionally omitted from this public checkpoint.
Fresh production/runtime evidence must be obtained from the protected evidence path before making an L4 claim.

Current evidence classes:
- Nightly 24-program research: no provider-backed closure receipt is currently certified.
- Extractor benchmark: latest structural benchmark is 40 receipts with 4 `ok`, 32 `empty`, and 4 `blocked`; integrity/provenance checks passed, but this is not proof of 40 successful real acquisitions.
- Polyglot migration: deterministic/structural evidence exists; runtime performance evidence is still required before promotion.

## Continuity

Use this file together with `docs/FAMILY_SYNC_STATE.json` and `docs/PROMPT_TO_CANONICAL_DOC_MAP.md`.
Do not add another competing current-state document.
