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

Mismatch feedback exposed four classifier problems: PC Studio under-detection, Quickin false GLA detection, Ninja Dog under-detection, and My Nexus Infosys under-detection.

## Classifier correction

Family detection now prefers exclusive fingerprints instead of generic page text. Generic Google Merchant Center wording cannot by itself create a Google-for-WooCommerce classification.

Family-specific signals include WooCommerce GPF, CTX/WebAppick/woo_feed, AdTribes/Product Feed PRO, WPFM/WPPFM, WebToffee, CodeSolz, FeedCraft, and Google Listings & Ads / wc/gla signatures.

Synthetic regressions pass for CTX, GLA, WooCommerce GPF, and WPFM signatures.

## Phase 2 — unknown 20

The remaining 20 sites were executed in six parallel shards using learned evidence transfer.
- Native standalone Google Merchant XML verified: 0/20.
- Weak family evidence is not promoted to a definitive classification.

Historical refinement analyzed 292 archived HTML snapshots and produced four low-confidence family hypotheses:
- Cosmic Byte → AdTribes Product Feed PRO
- NCL Computer → WebToffee Product Feed
- PC Kumar Infotech → Google for WooCommerce / Google Listings & Ads
- iTHunt → Google for WooCommerce / Google Listings & Ads

The other 16 remain unresolved.

## Phase 3 — targeted family verification

Added a dedicated verifier for the four hypotheses.

AdTribes: known output directories, bounded stable filename variants, discovered XML links, and same-host historical XML references.
WebToffee: known output directory, documented filename variants, discovered XML links, and same-host historical URLs.
Google for WooCommerce: public GLA REST signals are checked separately; an XML feed is not fabricated from an API integration.

## Final acceptance model

NATIVE_FEED_VERIFIED means the current response validates as Google Merchant XML.
API_INTEGRATED_GOOGLE means a Google-for-WooCommerce integration is evidenced without an independent public XML feed.
FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED means a generator family is evidenced but the current public filename cannot be recovered.
FAMILY_HYPOTHESIS_ONLY means only weak historical evidence exists.
UNKNOWN means no family can be justified.

HTTP 403/429, challenge HTML, 404 HTML, RSS, normal sitemaps, and historical-only URLs are response states, not proof of feed absence.

## Efficiency and reproducibility

Six parallel shards cover the unknown 20. Historical refinement is HTTP-only. Both primary workflows have concurrency guards. Superseded automatic guessing workflows were retired. The no-cookie-replay / no-clearance-bypass boundary remains enforced.

## Current execution state

The implementation, learned data pipeline, historical refinement, classifier correction, targeted verifier, concurrency controls, and final documentation are committed to PR #1604.

The latest post-fix live calibration/rerun remains subject to GitHub Actions runner scheduling. That is a validation pass over the completed implementation, not a missing code stage.

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