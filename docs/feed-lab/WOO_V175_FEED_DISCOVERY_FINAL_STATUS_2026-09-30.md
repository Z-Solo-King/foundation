# WooCommerce Feed Discovery — Final Strategy Status — 2026-09-30

## Scope
Original corpus: 32 sites.
- Moskeys: excluded because the site is down.
- Only SSD: excluded from active calibration because its native Google feed was already separately established.
- Active calibration corpus: 30 sites.

## Phase 1 — known feed-related cohort
Phase 1 contains 10 sites: four standalone feed-generator families and six Google-for-WooCommerce / Google Listings & Ads integrations.

Standalone feed generators:
- PC Studio — WooCommerce Google Product Feed
- Quickin Computers — CTX Feed / WebAppick
- Avikaretails — Product Feed PRO / AdTribes
- IT Gadgets Online — Product Feed Manager / WPPFM

API-integrated Google family:
- Geekbees
- Ninja Dog
- Network IT Store
- My Nexus Infosys
- Solanki Enterprises
- AULA India

Baseline Phase 1 result:
- Native standalone Google Merchant XML verified: 0/10
- Expected family matches: 6/10
- Probe errors: 0

The mismatch set was used as classifier feedback rather than being copied into the unknown-site model.

## Classifier correction
Family detection now prefers exclusive fingerprints instead of generic page text. Generic Google Merchant Center wording cannot by itself create a Google-for-WooCommerce classification.

Family-specific signals include WooCommerce GPF, CTX/WebAppick/woo_feed, AdTribes/Product Feed PRO, WPFM/WPPFM, WebToffee, CodeSolz, FeedCraft, and Google Listings & Ads / wc/gla signatures.

Synthetic regressions pass for CTX, GLA, WooCommerce GPF, and WPFM signatures.

## Phase 2 — unknown 20
The remaining 20 sites were executed in six parallel shards using learned evidence transfer.
- Native standalone Google Merchant XML verified: 0/20.
- Weak family evidence is not forced into a definitive classification.

The corrected classifier plus historical refinement analyzed 333 archived HTML snapshots and currently yields four low-confidence family hypotheses:
- Kryptronix Gaming → WebToffee Product Feed
- NCL Computer → WebToffee Product Feed
- Prime ABGB → WooCommerce Google Product Feed
- Variety Infotech → Google for WooCommerce / Google Listings & Ads

The other 16 remain unresolved.

## Targeted family verification
A separate fast workflow verifies the four current hypotheses without rerunning all 20 sites.

WebToffee targets use the plugin output directory, stable/documented filename variants, discovered XML links, and same-host historical XML references.
WooCommerce Google Product Feed targets use the documented query/permalink grammar and partial-feed parameters.
Google for WooCommerce targets check public GLA REST signals and do not fabricate a standalone XML feed from the API integration.

## Final acceptance model
NATIVE_FEED_VERIFIED means the current response validates as Google Merchant XML.
API_INTEGRATED_GOOGLE means a Google-for-WooCommerce integration is evidenced without an independent public XML feed.
FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED means a feed-generator family is evidenced but the current public filename cannot be recovered.
FAMILY_HYPOTHESIS_ONLY means only weak historical evidence exists.
UNKNOWN means no family can be justified.

HTTP 403/429, challenge HTML, 404 HTML, RSS, normal sitemaps, and historical-only URLs are response states, not proof of feed absence.

## Efficiency and reproducibility
- Six parallel shards cover the unknown 20.
- Historical refinement is HTTP-only and does not install browser runtimes.
- Family-targeted verification is isolated from the 20-site historical run.
- Concurrency guards cancel obsolete overlapping runs.
- Superseded automatic guessing workflows are retired.
- The no-cookie-replay / no-clearance-bypass boundary remains enforced.
- Historical evidence is retained as learning input, while current payload validation remains the final acceptance gate.

## Current execution state
The implementation, corrected family classifier, 20-site historical refinement, targeted verifier, concurrency controls, and documentation are committed to PR #1604.

The latest live workflows are validation runs over this completed implementation. The authoritative historical result used for the current hypothesis set is the six-shard post-classifier refinement dataset.

## Reusable algorithm
1. Detect known family using exclusive fingerprints.
2. Search exact public feed references and explicit feed query parameters.
3. Inspect current browser/XHR/resource and REST evidence.
4. Inspect public output directories.
5. Inspect bounded historical references.
6. Transfer only family-specific URL grammar observed from evidence.
7. Revalidate candidates against the current site.
8. Record transport, evidence sources, failure states, and confidence.
9. Never infer feed absence solely from blocking, missing directory indexes, or unsuccessful filename guesses.