# WooCommerce Unknown 20 — Final Family Target Strategy — 2026-09-30

## Purpose

The learned and historical passes are now separated from feed acceptance. Family identification is evidence-driven; feed acceptance still requires a current payload.

## Targeted hypotheses

- Cosmic Byte: low-confidence AdTribes Product Feed PRO hypothesis from archived/plugin evidence.
- NCL Computer: low-confidence WebToffee Product Feed hypothesis from archived/plugin evidence.
- PC Kumar Infotech: low-confidence Google for WooCommerce / Google Listings & Ads hypothesis.
- iTHunt: low-confidence Google for WooCommerce / Google Listings & Ads hypothesis.

## Decision rules

AdTribes and WebToffee are tested with their documented/static upload directories, bounded stable filename candidates, discovered XML links, and same-host historical XML references. Because generated feed filenames can be merchant-configured or non-deterministic, a missing stable filename is not treated as proof of feed absence.

Google for WooCommerce is handled as an API-integrated family. A public standalone XML feed is not assumed to exist; the verifier checks public GLA REST signals and does not manufacture XML candidates from the integration itself.

## Coverage / acceptance

The overall corpus accounting remains:
32 original sites -> 1 site down/excluded (Moskeys) + 1 separately verified native feed (Only SSD) -> 30 active calibration sites.

Phase 1 = 10 known feed-related sites.
Phase 2 = remaining 20 unknown-family sites.
Phase 3 = targeted family verification on newly identified hypotheses.

A native feed is accepted only when the current response validates as Google Merchant XML. Historical evidence can identify a family or candidate URL but cannot itself make the feed current/verified.

## Efficiency

All six-site shard jobs are concurrency-controlled and the workflow cancels obsolete overlapping runs. This prevents multiple patch-triggered runs from consuming Actions capacity and producing competing datasets.
