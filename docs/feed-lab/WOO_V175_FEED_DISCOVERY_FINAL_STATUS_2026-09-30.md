# WooCommerce V175 — Feed Discovery Final Status — 2026-09-30

## Executive state

The WooCommerce feed-learning track now has a stable three-phase structure:

- **Phase 1:** 10 known feed-related sites used for calibration.
- **Phase 2:** 20 remaining sites used for learned/historical family discovery.
- **Phase 3:** isolated targeted verification of newly identified family hypotheses.

The implementation and documentation are in Foundation PR **#1604** on branch `feat/wc-high-confidence-feed-guessing-20260930`.

## Corpus accounting

Original corpus: **32 sites**

- Moskeys — excluded because the site is down/unresolvable.
- Only SSD — excluded from active calibration because its native Google feed was already separately established.
- Active calibration corpus — **30 sites**.

This 30-site research corpus is deliberately separate from Foundation issue **#1247**, whose canonical production denominator remains **21 active unresolved sites**. The learning track must not overwrite that issue's denominator.

## Phase 1 — 10 known feed-related sites

Standalone generators:
- PC Studio — WooCommerce Google Product Feed
- Quickin Computers — CTX Feed / WebAppick
- Avikaretails — Product Feed PRO / AdTribes
- IT Gadgets Online — Product Feed Manager / WPPFM

Google-for-WooCommerce / Google Listings & Ads:
- Geekbees
- Ninja Dog
- Network IT Store
- My Nexus Infosys
- Solanki Enterprises
- AULA India

Baseline calibration:
- expected family matches: **6/10**
- standalone native Google Merchant XML verified by calibration: **0/10**
- probe errors: **0**

The mismatch set was used to fix family classification. The corrected classifier requires family-exclusive fingerprints where possible; generic Google Merchant Center page wording cannot create a Google-for-WooCommerce family hit by itself.

## Phase 2 — unknown 20

The remaining 20 sites were executed in six parallel shards.

The corrected post-classifier historical refinement analyzed:
- **333 archived HTML snapshots**
- **112 historical feed-like candidates**

Current low-confidence hypotheses:
- Kryptronix Gaming → WebToffee Product Feed
- NCL Computer → WebToffee Product Feed
- Prime ABGB → WooCommerce Google Product Feed
- Variety Infotech → Google for WooCommerce / Google Listings & Ads

The other **16/20** remain unresolved.

Current standalone native Google Merchant XML verified across the unknown 20: **0/20**.

## Phase 3 — targeted family verification

The four current hypotheses were verified separately so hypothesis changes do not require a full 20-site rerun.

Results:
- Kryptronix Gaming — 77 candidates checked; no current native Merchant XML; WebToffee filename unresolved; output directory returned 404.
- NCL Computer — 7 candidates checked; no current native Merchant XML; WebToffee filename unresolved; output directory returned 403.
- Prime ABGB — 1 candidate checked; no current native Merchant XML; filename unresolved.
- Variety Infotech — GLA endpoints returned 403; no current native XML; hypothesis remains low confidence.

Targeted native verification: **0/4**.

## Acceptance model

A native feed is verified only when the **current** response validates as Google Merchant XML with the expected Google namespace and real product fields.

Tracked separately:
- `NATIVE_FEED_VERIFIED` — current payload passed native validation.
- `API_INTEGRATED_GOOGLE_NO_PUBLIC_XML` — Google-for-WooCommerce integration is evidenced without a standalone XML payload.
- `FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED` — family is evidenced, but the current public filename/feed payload could not be recovered.
- `FAMILY_HYPOTHESIS_ONLY` — only low-confidence family evidence is available.
- `UNKNOWN` — no family can be justified.

Not proof of feed absence:
- 403/429;
- challenge/interstitial HTML;
- 404 HTML;
- normal RSS/Atom;
- sitemap XML;
- Store API/product JSON;
- historical-only URLs;
- unsuccessful filename guesses.

## Reusable algorithm

1. Detect family using exclusive fingerprints.
2. Search exact public feed references and explicit feed query/permalink parameters.
3. Inspect current browser/XHR/resource and REST evidence when available.
4. Inspect public plugin output directories.
5. Use bounded historical references for learning.
6. Transfer only family-specific URL grammar supported by evidence.
7. Revalidate candidates against the current host.
8. Record transport, provenance, response state and confidence.
9. Never infer feed absence solely from blocking, missing directory indexes, or failed filename guesses.

## Security boundary

The complete track remains public-only:
- no CAPTCHA solving;
- no Cloudflare challenge bypass;
- no authentication bypass;
- no clearance-cookie replay;
- no stealth/anti-detect browser;
- no proxy rotation for evasion;
- no blind random filename/token enumeration.

## Current GitHub validation state

PR #1604 is open at head `9273c23644cab5ae2b69ae889b1d6493990d725a3`.

At the latest sync checkpoint:
- CodeQL: success.
- Public tests: success.
- Analyze-python: success.
- Static Actions security checks and workflow/security regression checks: success.
- Phase 1 deep calibration job: success.
- The current six-shard learned unknown-20 execution is still in progress.

The in-progress Actions run is validation of the completed implementation; it is not evidence of a missing engineering stage. Results are not promoted to canonical until the relevant jobs and artifacts complete successfully.

## Repository authority

The V175 harness remains derived from the extractor's public-only evidence contract. Historical data is retained as learning input, but current payload validation remains the final native-feed acceptance gate.
