# WooCommerce V175 — Plugin Grouping, Research & Guessing — 2026-09-30

## 1. Corpus and phase boundaries

The research corpus contains 32 WooCommerce sites.

- Moskeys: excluded because the site is down/unresolvable.
- Only SSD: excluded from active calibration because its native Google feed was already separately established.
- Active calibration corpus: 30 sites.
- Phase 1: all 10 known feed-related sites.
- Phase 2: the remaining 20 unknown-family sites.
- Phase 3: targeted verification of any new family hypotheses.

This 30-site calibration track is separate from Foundation issue #1247's canonical 21-site active unresolved denominator. The calibration results must not overwrite that denominator.

## 2. Phase 1 — known feed-related families

### Standalone generators

| Site | Family |
|---|---|
| PC Studio | WooCommerce Google Product Feed |
| Quickin Computers | CTX Feed / WebAppick |
| Avikaretails | Product Feed PRO / AdTribes |
| IT Gadgets Online | Product Feed Manager / WPPFM |

### API-integrated Google family

| Site | Family |
|---|---|
| Geekbees | Google for WooCommerce / Google Listings & Ads |
| Ninja Dog | Google for WooCommerce / Google Listings & Ads |
| Network IT Store | Google for WooCommerce / Google Listings & Ads |
| My Nexus Infosys | Google for WooCommerce / Google Listings & Ads |
| Solanki Enterprises | Google for WooCommerce / Google Listings & Ads |
| AULA India | Google for WooCommerce / Google Listings & Ads |

The baseline Phase 1 run matched 6/10 expected families and verified 0/10 standalone native Merchant XML feeds. The mismatch set was used as classifier feedback rather than being copied into Phase 2.

## 3. Plugin-family research

### WooCommerce Google Product Feed

Documented query/permalink forms include `?woocommerce_gpf=google`, with partial-feed parameters such as `gpf_start` and `gpf_limit`.

Strategy: probe the documented query forms first, then use any explicit public references. A query response is accepted only if the current payload validates as Merchant XML.

### CTX Feed / WebAppick

Observed/documented generation uses the WooCommerce upload area, commonly under `/wp-content/uploads/woo-feed/google/xml/`, while feed filenames may be generated/configurable.

Strategy: inspect public directory indexes and source references. Do not enumerate arbitrary feed IDs.

### AdTribes Product Feed PRO

Generated feeds are commonly written below `/wp-content/uploads/woo-product-feed-pro/xml/` and may use generated or non-semantic filenames.

Strategy: use public directory/reference evidence and bounded stable filename variants only.

### Product Feed Manager / WPPFM

Generated feeds are associated with `/wp-content/uploads/wppfm-feeds/`.

Strategy: recover explicit public filenames or directory listings; do not assume a fixed `google.xml` filename.

### WebToffee Product Feed

Generated feeds are associated with `/wp-content/uploads/webtoffee_product_feed/`, with feed URLs and filenames configurable.

Strategy: search the known output directory, documented filename patterns and public references. Do not treat a missing directory index as proof of absence.

### CodeSolz Merchant Feed Booster

A deterministic public path is documented under `/wp-content/uploads/codesolz-feeds/`.

Strategy: direct validation of the documented path is appropriate before any broader search.

### FeedCraft

Documented REST feed endpoints exist under `/wp-json/feedcraft-product-feed/v1/`.

Strategy: direct validation of the documented REST family is appropriate.

### Google for WooCommerce / Google Listings & Ads

This family is handled as an API-integrated architecture. Public `wc/gla` / plugin evidence can identify the integration, but a standalone XML feed is not fabricated from the integration itself.

## 4. Phase 2 — current unknown-site hypotheses

The corrected classifier plus historical refinement produced four low-confidence hypotheses:

| Site | Current hypothesis | Confidence |
|---|---|---|
| Kryptronix Gaming | WebToffee Product Feed | low |
| NCL Computer | WebToffee Product Feed | low |
| Prime ABGB | WooCommerce Google Product Feed | low |
| Variety Infotech | Google for WooCommerce / Google Listings & Ads | low |

The other 16 remain `unknown_woocommerce`.

Historical refinement used 333 archived HTML snapshots and 112 historical feed-like candidates across the 20-site cohort. Historical evidence remains a hypothesis source only.

## 5. Guessing algorithm

Use evidence in descending priority:

1. exact public feed reference;
2. explicit query/permalink signature;
3. current browser/XHR/resource or REST evidence;
4. public plugin output directory;
5. bounded historical references;
6. family-specific documented URL grammar;
7. bounded stable filename candidates.

Do not expand the search space by blind random filename/token permutations.

Every candidate is revalidated against the current host. Same-host and current-payload requirements remain mandatory for native-feed acceptance.

## 6. Failure semantics

The following are response states, not feed absence:
- HTTP 403/429;
- challenge/interstitial HTML;
- 404 HTML;
- normal RSS/Atom;
- sitemap XML;
- Store API/product JSON;
- archive-only URLs;
- guessed filenames that do not resolve.

The extractor should record status, transport, evidence provenance and confidence rather than collapsing these states into a Boolean “feed/no feed”.

## 7. Security and reproducibility

- Public acquisition only.
- No CAPTCHA solving or challenge bypass.
- No authentication or clearance-cookie replay.
- No stealth/anti-detect browser.
- No proxy rotation for evasion.
- Historical refinement is HTTP-only.
- Unknown 20 runs in six parallel shards.
- Targeted verification is isolated from the full 20-site historical pass.
- Concurrency guards cancel obsolete overlapping runs.

## 8. Relationship to canonical issue #1247

Issue #1247 remains the canonical 21-site production unresolved track. This document records the separate 30-site learning/calibration corpus and its reusable algorithm. It is intentionally additive: new family evidence can improve future discovery without rewriting the production denominator or falsely certifying a native feed.
