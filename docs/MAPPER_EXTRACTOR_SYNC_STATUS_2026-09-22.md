# Mapper / Extractor Cross-Repository Sync — 2026-09-22

## Purpose

This document is the synchronization record for the canonical Mapper/Extractor architecture across the two active repositories.

Implementation synchronization baseline:
- Foundation: `673080ad9eca408512adb241fe73c18d488c7e20`
- Operations: `7226f5d8404df032654f0b8ebb8fd71dddfe0a0d`

These are the implementation revisions at which the Mapper/Extractor fixes were fully synchronized before the dated documentation commits. The sync documents themselves are deliberately excluded from the implementation baseline so documentation commits do not invalidate the baseline reference.

## Canonical ownership

| Concern | Canonical owner |
|---|---|
| Deterministic product mapping | Foundation |
| Product identity decisions | Foundation |
| Public compatibility/core facade | Foundation |
| Acquisition / browser acquisition | Operations |
| Extractor execution | Operations |
| Resource reservation / consume / release | Operations |
| Observation / replay contract | Operations |
| Protected policy / evaluation / promotion | Operations |
| CI / canonical production deployment authority | Foundation |
| Master audit synthesis | Operations |
| Runtime / Cloudflare evidence | External runtime gate |

Operations must not become a second semantic mapping authority. Foundation must not acquire network or protected runtime responsibilities merely to support mapping.

## Mapper/Extractor contract alignment

The completed cross-audit covered:
- multi-seller offer preservation;
- strict input/output SHA-256 observation digests;
- public URL / redirect / DNS-rebinding acquisition boundaries;
- browser time and page budgets;
- failed browser navigation counting against page budget;
- ResourceLedger ownership;
- network-free deterministic replay;
- mapper/extractor artifact versioning;
- non-finite seller-price rejection;
- direct regression coverage on both repository surfaces.

## Permanent audit path

Foundation's exhaustive six-lane workflow runs:
`operations-repo/tools/mapper_extractor_cross_audit.py`

Current workflow scanner marker:
`mapper/extractor cross-audit v5 — multi-offer, digest, browser resource/page-budget and non-finite numeric invariants`

Receipt schema:
`mapper-extractor-cross-audit/v1`

The cross-audit is executed before the six concurrent exhaustive lanes and is registered as a required master-audit family.

## Implemented findings

### Multi-offer mapper loss
Foundation `map_product()` now preserves normalized multi-offer rows while keeping legacy top-level price/stock compatibility.

### Observation digest validation
Operations `ProductObservation` now validates `input_sha256` and `output_sha256` with the canonical SHA-256 validator.

### Browser resource enforcement
Operations browser acquisition now enforces canonical `max_browser_minutes` and `max_pages` limits and propagates the values into the browser benchmark.

### Failed-navigation page-budget bypass
A browser page attempt is counted immediately after page creation, before navigation, so failed navigation cannot bypass the page limit.

### Numeric safety
`SellerOffer.price` rejects NaN and infinite values.

## Verification state

The final Foundation exhaustive audit run on the synchronized stack completed successfully:
- live open-issue register: PASS
- mapper/extractor cross-audit: PASS
- exhaustive audit contract: PASS
- six concurrent exhaustive lanes: PASS
- artifact generation/upload: PASS

Foundation PR #986 was merged as `673080ad9eca408512adb241fe73c18d488c7e20`. Subsequent commits on `main` are documentation synchronization commits and do not change the implementation baseline recorded above.

Operations PRs #771, #772, #773, #774, #775, #776 and #777 were merged into Operations main during this synchronization wave.

## Evidence boundary

Repository/CI success certifies repository consistency and deterministic checks only. It does not certify Cloudflare/provider/runtime acceptance unless a matching runtime receipt exists.

## Maintenance rule

Any future Mapper or Extractor change must update:
1. the owning implementation;
2. the opposite-side contract/regression surface;
3. the executable mapper/extractor cross-audit when the invariant changes;
4. this synchronization record or its next dated successor when ownership/revisions change;
5. master-audit inputs when a new specialized audit family is introduced.

