# WooCommerce V175 — High-Confidence Calibration & Learning — 2026-09-30

## Objective

Use the 10 known feed-related sites as a controlled learning cohort before applying improved feed-family discovery to the remaining 20 sites.

The key design rule is to learn **methods and evidence patterns**, not to copy guessed URLs or classifications directly.

## Cohort

Phase 1 contains exactly 10 sites:

- PC Studio — WooCommerce Google Product Feed
- Quickin Computers — CTX Feed / WebAppick
- Avikaretails — Product Feed PRO / AdTribes
- IT Gadgets Online — Product Feed Manager / WPPFM
- Geekbees — Google for WooCommerce / Google Listings & Ads
- Ninja Dog — Google for WooCommerce / Google Listings & Ads
- Network IT Store — Google for WooCommerce / Google Listings & Ads
- My Nexus Infosys — Google for WooCommerce / Google Listings & Ads
- Solanki Enterprises — Google for WooCommerce / Google Listings & Ads
- AULA India — Google for WooCommerce / Google Listings & Ads

Only SSD remains outside the calibration because its native feed was already separately established. Moskeys remains outside because the site is down/unresolvable.

## Baseline and classifier learning

The first Phase 1 run produced 6/10 family matches, 0/10 standalone native Merchant XML validations and 0 probe errors.

The mismatch set directly exposed a family-classification weakness: generic “Google Merchant Center” page copy could collide with Google-for-WooCommerce detection. The classifier was changed to prefer family-exclusive plugin slugs, REST namespaces and endpoint signatures. Synthetic regressions now preserve real CTX, GLA, WooCommerce GPF and WPFM signatures while rejecting generic GLA wording.

This is the principal Phase 1 learning result: **family identification and feed acceptance are separate inference problems**.

## Evidence hierarchy

Discovery and learning use this order:

1. exact public feed URL/reference;
2. explicit query/permalink feed grammar;
3. current browser/XHR/resource or REST evidence;
4. public plugin output directory;
5. bounded historical feed/plugin references;
6. documented family URL grammar;
7. bounded stable filename candidates.

Evidence lower in the list can generate a hypothesis or candidate, but cannot outrank stronger current evidence.

## Transfer rules for the unknown 20

For each unknown site:

- infer only a family when there is a concrete family-specific signal;
- transfer URL grammar only when the grammar is supported by observed/documented evidence;
- keep API-integrated Google for WooCommerce distinct from standalone XML generators;
- revalidate every historical/discovered URL against the current host;
- record response status and evidence source rather than treating failures as “no feed”.

The learned pass runs in six parallel shards. It is followed by an independent historical refinement stage and, where useful, an isolated family-targeted verifier.

## Historical learning stage

The post-classifier 20-site historical refinement analyzed 333 archived HTML snapshots and produced four low-confidence hypotheses:

- Kryptronix Gaming → WebToffee Product Feed
- NCL Computer → WebToffee Product Feed
- Prime ABGB → WooCommerce Google Product Feed
- Variety Infotech → Google for WooCommerce / Google Listings & Ads

The other 16 remain unresolved. No native standalone Google Merchant XML feed was verified across the 20-site cohort.

## Targeted learning stage

The four hypotheses were then checked separately so the hypothesis set could be iterated without rerunning all 20 sites.

Current targeted results:
- Kryptronix Gaming: WebToffee; 77 candidates checked; no current native Merchant XML; filename unresolved.
- NCL Computer: WebToffee; 7 candidates checked; no current native Merchant XML; output directory returned 403.
- Prime ABGB: WooCommerce GPF; 1 candidate checked; no current native Merchant XML; filename unresolved.
- Variety Infotech: Google for WooCommerce; GLA endpoints returned 403; no current XML verified.

Targeted native verification: 0/4.

## Acceptance contract

Only a **current** public payload that validates as Google Merchant XML is `NATIVE_FEED_VERIFIED`.

The following are retained as evidence states but do not certify a native feed:
- historical captures;
- reconstructed XML;
- Store API/product JSON;
- RSS/Atom;
- sitemaps;
- HTML/interstitials;
- 403/429 transport responses;
- guessed or documented URLs that do not return valid Merchant XML.

Google-for-WooCommerce is represented separately as an API-integrated architecture when its public integration evidence is strong enough. It is not converted into a fictitious standalone XML feed.

## Security boundary

The learning system remains public-only and does not use CAPTCHA solving, Cloudflare challenge bypass, authentication bypass, clearance-cookie replay, stealth browsing or proxy rotation for evasion.
