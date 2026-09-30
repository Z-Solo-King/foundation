# WooCommerce V175 — Unknown 20 Family-Targeted Verification — 2026-09-30

## Purpose

Run a small, independent verification pass against the four family hypotheses produced by the corrected 20-site historical refinement. Keeping this stage isolated allows the hypothesis set to change without consuming another full 20-site historical run.

## Current hypotheses

| Site | Family |
|---|---|
| Kryptronix Gaming | WebToffee Product Feed |
| NCL Computer | WebToffee Product Feed |
| Prime ABGB | WooCommerce Google Product Feed |
| Variety Infotech | Google for WooCommerce / Google Listings & Ads |

All four hypotheses remain **low confidence**.

## Targeted verification rules

### WebToffee
Search:
- the known WebToffee upload directory;
- documented/stable filename variants;
- XML links exposed in public HTML or site metadata;
- same-host historical XML references.

A generated filename may be configurable or non-deterministic. A missing directory index or missing stable filename is therefore not proof of feed absence.

### WooCommerce Google Product Feed
Search:
- documented `?woocommerce_gpf=google` query/permalink forms;
- bounded partial-feed parameters;
- explicit public references.

### Google for WooCommerce
Check public Google Listings & Ads / `wc/gla` REST evidence. Do not fabricate an XML feed from the API integration.

## Latest targeted result

The successful verification step checked the four current hypotheses:

| Site | Candidates checked | Current result |
|---|---:|---|
| Kryptronix Gaming | 77 | `FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED`; WebToffee output directory returned 404; no native XML |
| NCL Computer | 7 | `FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED`; WebToffee output directory returned 403; no native XML |
| Prime ABGB | 1 | `FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED`; no native XML |
| Variety Infotech | 0 XML candidates | `FAMILY_HYPOTHESIS_ONLY`; GLA endpoints returned 403; no current XML |

Aggregate targeted native verification: **0/4**.

These statuses describe the evidence recovered by this run. They do not assert that the target sites lack feeds.

## Acceptance

`NATIVE_FEED_VERIFIED` requires a current payload containing the Google Merchant namespace and core product fields.

`FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED` means family evidence exists but a current public filename/feed payload was not recovered.

`FAMILY_HYPOTHESIS_ONLY` means the current evidence is not strong enough to establish a current integration/feed endpoint.

Google-for-WooCommerce API evidence is tracked separately from standalone XML.

## Security and execution boundary

The verifier uses ordinary public HTTP requests and a static guard against cookie-replay/stealth dependencies. It has a dedicated workflow with concurrency cancellation so obsolete overlapping runs do not create competing evidence datasets.

No CAPTCHA solving, Cloudflare challenge bypass, authentication bypass, clearance-cookie replay, stealth browsing, proxy rotation for evasion, or blind random-token enumeration is permitted.
