# WooCommerce V175 — Known Feed-Family Calibration — 2026-09-30

## Purpose

Phase 1 is the complete known feed-related calibration cohort. It is intentionally separate from the canonical 21-site production denominator tracked by Foundation issue #1247.

Original corpus accounting:
- 32 sites total.
- Moskeys is excluded from active calibration because the site is down/unresolvable.
- Only SSD is excluded from calibration because a native Google feed was already separately established.
- 30 sites remain in the calibration corpus.
- Phase 1 uses all 10 sites with known feed-family relationships; Phase 2 uses the remaining 20.

## Phase 1 cohort — exactly 10 sites

### Standalone feed-generator families

| Site | Expected family |
|---|---|
| PC Studio | WooCommerce Google Product Feed |
| Quickin Computers | CTX Feed / WebAppick |
| Avikaretails | Product Feed PRO / AdTribes |
| IT Gadgets Online | Product Feed Manager / WPPFM |

### Google-for-WooCommerce / Google Listings & Ads

| Site | Expected family |
|---|---|
| Geekbees | Google for WooCommerce |
| Ninja Dog | Google for WooCommerce |
| Network IT Store | Google for WooCommerce |
| My Nexus Infosys | Google for WooCommerce |
| Solanki Enterprises | Google for WooCommerce |
| AULA India | Google for WooCommerce |

## Baseline calibration result

The first Phase 1 run completed without probe errors:

| Site | Expected | Baseline detected | Confidence |
|---|---|---|---|
| PC Studio | WooCommerce GPF | unknown | low |
| Quickin Computers | CTX / WebAppick | Google for WooCommerce | high |
| Avikaretails | AdTribes | AdTribes | medium |
| IT Gadgets Online | WPFM | WPFM | medium |
| Geekbees | Google for WooCommerce | Google for WooCommerce | high |
| Ninja Dog | Google for WooCommerce | unknown | low |
| Network IT Store | Google for WooCommerce | Google for WooCommerce | high |
| My Nexus Infosys | Google for WooCommerce | unknown | low |
| Solanki Enterprises | Google for WooCommerce | Google for WooCommerce | high |
| AULA India | Google for WooCommerce | Google for WooCommerce | medium |

Aggregate baseline:
- expected family matches: 6/10;
- native standalone Google Merchant XML verified by the calibration guessing lanes: 0/10;
- probe errors: 0.

These are calibration observations, not production-feed negatives for #1247.

## What the mismatch taught us

Four classifier problems were identified by the controlled known cohort:

1. PC Studio was under-detected despite the expected WooCommerce GPF family.
2. Quickin Computers was falsely promoted to Google-for-WooCommerce because generic Google Merchant wording overlapped a broad rule.
3. Ninja Dog was under-detected.
4. My Nexus Infosys was under-detected.

The important learning is that generic page copy is not family-exclusive evidence.

## Classifier correction

V175 family classification now uses exclusive fingerprints for the feed families wherever possible.

Strong family signals include:
- WooCommerce GPF: `woocommerce_gpf`, `woocommerce-google-product-feed`, `google_product_feed`, related plugin slugs/namespaces.
- CTX/WebAppick: `ctx-feed`, `webappick`, `woo_feed`.
- AdTribes: `adtribes`, `woo-product-feed-pro`.
- WPFM: `wppfm`, `wppfm-feeds`, `wpfm/v1`.
- WebToffee: `webtoffee`, `webtoffee_product_feed`.
- CodeSolz: `codesolz`, `codesolz-feeds`.
- FeedCraft: `feedcraft`, `feedcraft-product-feed`.
- Google for WooCommerce: `google-listings-and-ads`, `wc/gla`, `google_merchant_center_plugin`.

Generic “Google Merchant Center” prose is explicitly insufficient to classify Google for WooCommerce.

Synthetic regression cases pass for CTX, Google-for-WooCommerce, WooCommerce GPF and WPFM signatures.

## Discovery lanes

The calibration harness preserves the V175 evidence contract:
1. exact public feed references;
2. plugin-specific documented candidate URLs;
3. browser/XHR/resource and REST namespace evidence;
4. public plugin output directories;
5. robots/sitemap/passive references;
6. bounded historical references;
7. strict current-feed validation.

Historical evidence can improve family identification and candidate generation, but it cannot certify a current native feed.

## Acceptance boundary

A standalone native feed is accepted only when the current public response validates as Google Merchant XML with the Google namespace and core product fields. RSS/Atom, sitemaps, Store API responses, historical captures, guessed filenames and API-only Google integrations remain non-native evidence.

No CAPTCHA solving, Cloudflare challenge bypass, authentication bypass, clearance-cookie replay, stealth browser, proxy rotation for evasion, or blind random-token enumeration is part of this calibration.
