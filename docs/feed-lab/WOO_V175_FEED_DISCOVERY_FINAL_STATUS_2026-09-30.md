# WooCommerce Feed Discovery — Final Strategy Status — 2026-09-30

## Scope
Original corpus: 32 sites.
- Moskeys: excluded because the site is down.
- Only SSD: excluded from active calibration because its native Google feed was already separately established.
- Active calibration corpus: 30 sites.

## Phase 1 — known feed-related cohort (10)
Standalone feed-generator families (4): PC Studio, Quickin Computers, Avikaretails, IT Gadgets Online.
Google-for-WooCommerce / Google Listings & Ads (6): Geekbees, Ninja Dog, Network IT Store, My Nexus Infosys, Solanki Enterprises, AULA India.

Completed baseline calibration: 0/10 standalone native Google Merchant XML verified; 6/10 expected family matches; 0 probe errors.

## Classifier correction
V175 family detection now uses family-exclusive fingerprints instead of generic page wording. This prevents ordinary Google Merchant Center text from creating a false Google-for-WooCommerce classification.

Regression checks pass for CTX/WebAppick, Google Listings & Ads, WooCommerce GPF, and WPFM signatures.

## Phase 2 — unknown 20
The 20 unknown sites were executed in six parallel shards using learned evidence transfer.
- Native standalone Google Merchant XML verified: 0/20.
- The corrected historical refinement analyzed 333 archived HTML snapshots.

Current low-confidence family hypotheses:
- Kryptronix Gaming → WebToffee Product Feed
- NCL Computer → WebToffee Product Feed
- Prime ABGB → WooCommerce Google Product Feed
- Variety Infotech → Google for WooCommerce / Google Listings & Ads

The other 16 remain unresolved because the evidence does not justify a family assignment.

## Phase 3 — targeted family verification
A separate fast verifier tested the four current hypotheses against the live sites.

| Site | Family hypothesis | Current result | Evidence |
|---|---|---|---|
| Kryptronix Gaming | WebToffee Product Feed | FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED | 77 candidates checked; no current validated Merchant XML; WebToffee directory returned 404 |
| NCL Computer | WebToffee Product Feed | FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED | 7 candidates checked; no current validated Merchant XML; WebToffee directory returned 403 |
| Prime ABGB | WooCommerce Google Product Feed | FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED | 1 candidate checked; no current validated Merchant XML |
| Variety Infotech | Google for WooCommerce / GLA | FAMILY_HYPOTHESIS_ONLY | GLA endpoints returned 403; no current XML feed verified |

Targeted result: 0/4 native Google Merchant XML verified.

## Final acceptance model
NATIVE_FEED_VERIFIED means the current response validates as Google Merchant XML.
API_INTEGRATED_GOOGLE means an API integration is positively evidenced without requiring standalone XML.
FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED means a family is evidenced but no current public filename/feed payload was recovered.
FAMILY_HYPOTHESIS_ONLY means the historical evidence is insufficient for a stronger current classification.
UNKNOWN means no family can be justified.

403/429, challenge HTML, 404 HTML, RSS, normal sitemaps, and historical-only URLs are response states, not feed absence.

## Efficiency and reproducibility
- Six parallel shards cover the unknown 20.
- Historical refinement is HTTP-only.
- Family-targeted verification is isolated from the full 20-site pass.
- Concurrency guards cancel obsolete overlapping runs.
- Superseded automatic guessing workflows are retired.
- The no-cookie-replay / no-clearance-bypass boundary remains enforced.
- Historical evidence is learning input; current payload validation remains the acceptance gate.

## Final reusable algorithm
1. Detect known family with exclusive fingerprints.
2. Search exact public feed references and explicit feed query parameters.
3. Inspect current browser/XHR/resource and REST evidence when appropriate.
4. Inspect public feed output directories.
5. Inspect bounded historical references.
6. Transfer only observed family-specific URL grammar.
7. Revalidate candidates against the current site.
8. Record transport, evidence source, response state and confidence.
9. Never infer feed absence from blocking or an unsuccessful filename guess.